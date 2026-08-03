from __future__ import annotations

import re

from selectolax.parser import HTMLParser, Node

from deal_watcher.sources.akakce_common import (
    AkakceOffer,
    ParserChangedError,
    canonical_url,
    content_hash,
    first_text,
    json_ld,
    normalize_text,
    now_utc,
    parse_price_kurus,
    source_id_from_url,
)


def _price(node: Node, selectors: tuple[str, ...]) -> int | None:
    return parse_price_kurus(first_text(node, selectors))


def _stock(text: str) -> str:
    lower = normalize_text(text)
    if any(item in lower for item in ("stokta yok", "tukendi", "temin edilemiyor")):
        return "out_of_stock"
    if any(item in lower for item in ("stokta", "hemen gonder", "kargoda")):
        return "in_stock"
    return "unknown"


class AkakceProductParser:
    """Parse a product page without making network requests."""

    offer_selectors = (".offer", ".product-offer", "tr.offer", "li.pt_v8", "div[class*=offer]")

    def parse(
        self,
        html: str,
        page_url: str,
        target_id: str | None = None,
        expected_name: str | None = None,
    ) -> tuple[AkakceOffer, ...]:
        tree = HTMLParser(html)
        title = first_text(tree, ("h1", ".product-title", "[data-product-name]"))
        structured = [item for item in json_ld(tree) if item.get("@type") in ("Product", "product")]
        if title is None and structured:
            title = str(structured[0].get("name") or "") or None
        if not title:
            raise ParserChangedError("Akakçe product title selector and JSON-LD name both missing")
        if expected_name and not self._matches_expected(title, expected_name):
            raise ParserChangedError(
                f"Akakçe page product variant does not match configured target {expected_name!r}"
            )

        nodes = [node for selector in self.offer_selectors for node in tree.css(selector)]
        if not nodes:
            nodes = [tree.body or tree.root]
        offers: list[AkakceOffer] = []
        for node in nodes:
            offer = self._parse_offer(node, title, page_url, target_id, structured)
            if offer is not None:
                offers.append(offer)
        if not offers:
            raise ParserChangedError("Akakçe product page contained no price offer")
        unique: dict[tuple[str, str | None, int | None], AkakceOffer] = {}
        for offer in offers:
            unique[(offer.canonical_url, offer.seller, offer.total_price)] = offer
        return tuple(unique.values())

    @staticmethod
    def _matches_expected(title: str, expected: str) -> bool:
        actual = normalize_text(title).replace(" ", "")
        wanted = normalize_text(expected).replace(" ", "")
        if "huaweiwatchgt6" in wanted and ("41mm" in wanted) != ("41mm" in actual):
            return False
        if "ronic" in wanted and "4000g" in wanted and "4000g" not in actual:
            return False
        if "9700x" in wanted and "9700x" not in actual:
            return False
        return "proartx870ecreator" not in wanted or "proartx870ecreator" in actual

    def _parse_offer(
        self,
        node: Node,
        title: str,
        page_url: str,
        target_id: str | None,
        structured: list[dict[str, object]],
    ) -> AkakceOffer | None:
        text = node.text(separator=" ", strip=True)
        listed = _price(node, (".price", ".current-price", "[data-price]", ".pt_v8", "body"))
        if listed is None:
            listed = parse_price_kurus(text)
        if listed is None:
            offers = [item.get("offers") for item in structured]
            for value in offers:
                if isinstance(value, dict):
                    listed = parse_price_kurus(str(value.get("price") or ""))
                    if listed is not None:
                        break
        if listed is None:
            return None
        href_node = node.css_first("a[href]")
        href = href_node.attributes.get("href") if href_node is not None else page_url
        offer_url = canonical_url(page_url, href or page_url)
        seller_url = canonical_url(page_url, href) if href and href != page_url else None
        seller = first_text(node, (".seller", ".merchant", ".store", "[data-seller]"))
        shipping_text = first_text(node, (".shipping", ".cargo", ".kargo", "[data-shipping]"))
        if shipping_text and any(
            x in normalize_text(shipping_text) for x in ("ücretsiz", "ucretsiz", "bedava")
        ):
            shipping = 0
        else:
            shipping = parse_price_kurus(shipping_text)
        total = listed + shipping if shipping is not None else None
        installments = first_text(node, (".installment", ".taksit", "[data-installment]"))
        count_match = re.search(r"(\d+)\s*(?:taksit|x)", installments or text, re.IGNORECASE)
        cash = parse_price_kurus(installments)
        return AkakceOffer(
            source_product_id=target_id or source_id_from_url(page_url),
            canonical_url=offer_url,
            product_name=title,
            normalized_product_name=normalize_text(title),
            brand=title.split()[0] if title.split() else None,
            model=title,
            variant=None,
            seller=seller,
            seller_url=seller_url,
            listed_price=listed,
            shipping_price=shipping,
            total_price=total,
            currency="TRY",
            stock_status=_stock(text),
            installment_count=int(count_match.group(1)) if count_match else None,
            cash_price_installment=cash,
            scraped_at=now_utc(),
            raw_hash=content_hash(text),
        )
