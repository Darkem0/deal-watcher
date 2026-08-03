from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urljoin, urlsplit, urlunsplit

from selectolax.parser import HTMLParser

from deal_watcher.models.domain import (
    ExternalLink,
    ForumTopicDetail,
    PriceMention,
)
from deal_watcher.sources.forum import ForumParseError, extract_price_kurus


class ForumTopicDetailParseError(ForumParseError):
    """A topic detail fixture is missing a required XenForo-like element."""


_TRACKING_PARAMS = {"fbclid", "gclid", "ref", "ref_", "utm_campaign", "utm_medium", "utm_source"}
_COUPON_RE = re.compile(
    r"(?:kupon|kod|sepette)\s*[:：]?\s*([A-Z0-9_-]*\d[A-Z0-9_-]*)", re.IGNORECASE
)
_STORE_RE = re.compile(r"(?:mağaza|magaza|satıcı|satici)\s*[:：]\s*([^\n,|]+)", re.IGNORECASE)


def _canonical_url(base_url: str, href: str) -> str:
    parts = urlsplit(urljoin(base_url, href))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _domain(url: str) -> str:
    return (urlsplit(url).hostname or "").lower().removeprefix("www.")


class DonanimArsiviForumTopicParser:
    """Parse a saved topic detail page; no network access is performed here."""

    def parse(self, html: str, base_url: str) -> ForumTopicDetail:
        tree = HTMLParser(html)
        message = tree.css_first("article.message-body, .message-body")
        if message is None:
            raise ForumTopicDetailParseError("missing first message body")
        first = message.text(separator="\n", strip=True)
        if not first:
            raise ForumTopicDetailParseError("first message body is empty")

        canonical = tree.css_first('link[rel="canonical"]')
        canonical_url = (
            _canonical_url(base_url, canonical.attributes.get("href", ""))
            if canonical is not None and canonical.attributes.get("href")
            else None
        )
        title_node = tree.css_first("h1.p-title-value, h1.topic-title")
        title = title_node.text(strip=True) if title_node is not None else None
        topic_id_match = re.search(r"(?:konu|topic)/[^/]*\.(\d+)", canonical_url or "")

        edited = tree.css_first("time.edited-time")
        edited_at = None
        if edited is not None:
            value = edited.attributes.get("datetime") or edited.text(strip=True)
            try:
                edited_at = datetime.fromisoformat(value) if value else None
            except ValueError as exc:
                raise ForumTopicDetailParseError(f"invalid edited time: {value!r}") from exc

        links: list[ExternalLink] = []
        for anchor in message.css("a[href]"):
            href = anchor.attributes.get("href", "")
            url = _canonical_url(base_url, href)
            domain = _domain(url)
            if not domain or domain.endswith("donanimarsivi.com"):
                continue
            store_match = _STORE_RE.search(anchor.text(strip=True))
            links.append(
                ExternalLink(url, domain, store_match.group(1).strip() if store_match else None)
            )

        raw_prices = extract_price_kurus(first)
        prices = tuple(
            PriceMention(
                price,
                first,
                is_previous_price=index == 1 and "önceki" in first.casefold(),
            )
            for index, price in enumerate(raw_prices)
        )
        codes = tuple(dict.fromkeys(match.group(1).upper() for match in _COUPON_RE.finditer(first)))
        lower = first.casefold().replace("i\u0307", "i")
        personalized = "kişiye özel" in lower or "sana özel" in lower
        if personalized:
            codes = tuple(dict.fromkeys((*codes, "PERSONALIZED")))
        stock_status = next(
            (
                phrase
                for phrase in (
                    "tekrar stokta",
                    "son stok",
                    "1 adet",
                    "2 adet",
                    "sınırlı stok",
                    "stok bitti",
                    "tükendi",
                    "stokta",
                )
                if phrase in lower
            ),
            None,
        )
        shipping = next(
            (
                sentence.strip()
                for sentence in re.split(r"[.!?]", first)
                if "kargo" in sentence.casefold()
            ),
            None,
        )
        product_names = tuple(
            line.strip()
            for line in first.splitlines()
            if any(char.isdigit() for char in line) and extract_price_kurus(line)
        )
        return ForumTopicDetail(
            first_message=first,
            topic_id=topic_id_match.group(1) if topic_id_match else None,
            canonical_topic_url=canonical_url,
            title=title,
            prefix_labels=tuple(
                node.text(strip=True) for node in tree.css(".label") if node.text(strip=True)
            ),
            edited_at=edited_at,
            external_links=tuple(links),
            prices=prices,
            coupon_codes=codes,
            personalized_coupon=personalized,
            cart_discount="sepette" in lower or "sepet indirimi" in lower,
            stock_status=stock_status,
            back_in_stock="tekrar stokta" in lower,
            discount_expired="indirim bitti" in lower or "indirim sona erdi" in lower,
            shipping_info=shipping,
            product_names=product_names,
        )
