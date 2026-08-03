from __future__ import annotations

import re

from selectolax.parser import HTMLParser, Node

from deal_watcher.sources.akakce_common import (
    AkakceCategoryItem,
    ParserChangedError,
    canonical_url,
    content_hash,
    first_text,
    normalize_text,
    now_utc,
    parse_price_kurus,
    source_id_from_url,
)


class AkakceCategoryParser:
    card_selectors = (".p-c", ".product-card", "li.product", "article.product", "tr.product")
    reject_terms = (
        "laptop",
        "notebook",
        "hazır sistem",
        "masaüstü",
        "water block",
        "soğutucu",
        "backplate",
        "bracket",
        "kablo",
        "aksesuar",
        "ikinci el",
        "outlet",
        "teşhir",
    )

    def parse(self, html: str, page_url: str, limit: int = 20) -> tuple[AkakceCategoryItem, ...]:
        tree = HTMLParser(html)
        nodes = [node for selector in self.card_selectors for node in tree.css(selector)]
        if not nodes:
            raise ParserChangedError("Akakçe category product-card selectors matched no elements")
        items: list[AkakceCategoryItem] = []
        seen: set[tuple[str, str]] = set()
        for node in nodes:
            parsed = self._parse_card(node, page_url, len(items) + 1)
            if parsed is None:
                continue
            key = (parsed.source_product_id, parsed.product_url)
            if key in seen:
                continue
            seen.add(key)
            items.append(parsed)
            if len(items) >= limit:
                break
        if not items:
            raise ParserChangedError("Akakçe category had no valid RTX 5070 Ti cards")
        return tuple(items)

    def _parse_card(self, node: Node, page_url: str, rank: int) -> AkakceCategoryItem | None:
        title = first_text(node, ("h3", "h2", ".product-title", ".p-n", "a[href]"))
        if not title:
            return None
        normalized = normalize_text(title)
        if "rtx 5070 ti" not in normalized or "rtx 5070 ti" not in normalized.replace("-", " "):
            return None
        if any(term in normalized for term in self.reject_terms):
            return None
        href_node = node.css_first("a[href]")
        href = href_node.attributes.get("href") if href_node is not None else None
        if not href:
            return None
        product_url = canonical_url(page_url, href)
        listed = parse_price_kurus(first_text(node, (".price", ".p-pr", "[data-price]")))
        if listed is None:
            listed = parse_price_kurus(node.text(separator=" ", strip=True))
        if listed is None:
            return None
        shipping_text = first_text(node, (".shipping", ".cargo", ".kargo"))
        shipping = (
            0
            if shipping_text
            and any(value in normalize_text(shipping_text) for value in ("ücretsiz", "ucretsiz"))
            else parse_price_kurus(shipping_text)
        )
        total = listed + shipping if shipping is not None else None
        vram_match = re.search(r"(\d+)\s*gb", normalized)
        vram = int(vram_match.group(1)) if vram_match else None
        warnings = ("expected VRAM 16 GB not observed",) if vram not in (None, 16) else ()
        seller = first_text(node, (".seller", ".merchant", ".store"))
        stock = (
            "out_of_stock" if any(x in normalized for x in ("stokta yok", "tükendi")) else "unknown"
        )
        return AkakceCategoryItem(
            product_name=title,
            product_url=product_url,
            source_product_id=source_id_from_url(product_url),
            normalized_brand=title.split()[0] if title.split() else None,
            normalized_model=self._normalize_model(title),
            chipset="RTX 5070 Ti",
            vram_gb=vram,
            listed_price=listed,
            shipping_price=shipping,
            total_price=total,
            seller=seller,
            stock_status=stock,
            installment_count=None,
            rank=rank,
            scraped_at=now_utc(),
            raw_hash=content_hash(node.text(separator=" ", strip=True)),
            validation_warnings=warnings,
        )

    @staticmethod
    def _normalize_model(title: str) -> str:
        value = normalize_text(title)
        value = re.sub(r"\b(oc|gaming|ventus|tuf|prime|eagle)\b", "", value)
        value = re.sub(r"\s+", " ", value).strip()
        return value
