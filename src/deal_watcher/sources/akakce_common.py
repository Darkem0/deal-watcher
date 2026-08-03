from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin, urlsplit, urlunsplit

from selectolax.parser import HTMLParser, Node


class ParserChangedError(ValueError):
    """The source returned HTML without the critical structure we expect."""


class SourceAccessError(RuntimeError):
    """A source could not be fetched or returned an unusable response."""


_NUMBER = r"\d{1,3}(?:[.\s]\d{3})*(?:,\d{1,2})?|\d+(?:[,.]\d{1,2})?"
_PRICE_RE = re.compile(
    rf"(?<![\w])({_NUMBER})\s*(?:TL|TRY|₺|bin\s*TL|k)\b|"
    rf"(?:TL|TRY|₺)\s*({_NUMBER})",
    re.IGNORECASE,
)


def normalize_text(value: str) -> str:
    return " ".join(value.casefold().replace("İ", "i").split())


def parse_price_kurus(value: str | None) -> int | None:
    if not value:
        return None
    match = _PRICE_RE.search(value)
    if not match:
        return None
    raw = (match.group(1) or match.group(2) or "").strip().lower()
    compact = raw.replace(" ", "")
    unit_text = match.group(0).casefold()
    multiplier = 1000 if re.search(r"(?:k|bin)\s*(?:tl)?$", unit_text) else 1
    compact = re.sub(r"(bin|k)$", "", compact).strip()
    if "," in compact and "." in compact:
        if compact.rfind(",") > compact.rfind("."):
            compact = compact.replace(".", "").replace(",", ".")
        else:
            compact = compact.replace(",", "")
    elif "," in compact:
        left, right = compact.rsplit(",", 1)
        compact = left.replace(",", "") + (f".{right}" if len(right) <= 2 else right)
    elif compact.count(".") > 1:
        compact = compact.replace(".", "")
    elif "." in compact:
        left, right = compact.rsplit(".", 1)
        compact = left.replace(".", "") + (f".{right}" if len(right) <= 2 else right)
    try:
        return round(float(compact) * 100 * multiplier)
    except ValueError:
        return None


def canonical_url(base_url: str, href: str) -> str:
    parts = urlsplit(urljoin(base_url, href))
    return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), "", ""))


def source_id_from_url(url: str) -> str:
    path = urlsplit(url).path.rstrip("/")
    match = re.search(r",(\d+)\.html$|[.-](\d+)(?:\.html)?$", path)
    if match:
        return next(group for group in match.groups() if group)
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def now_utc() -> datetime:
    return datetime.now(UTC)


def first_text(node: Node, selectors: tuple[str, ...]) -> str | None:
    for selector in selectors:
        found = node.css_first(selector)
        if found is not None:
            text = found.text(strip=True)
            if text:
                return text
    return None


def json_ld(tree: HTMLParser) -> list[dict[str, Any]]:
    import json

    values: list[dict[str, Any]] = []
    for script in tree.css('script[type="application/ld+json"]'):
        try:
            decoded = json.loads(script.text())
        except (TypeError, ValueError):
            continue
        candidates = decoded if isinstance(decoded, list) else [decoded]
        values.extend(item for item in candidates if isinstance(item, dict))
    return values


def content_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class AkakceOffer:
    source_product_id: str
    canonical_url: str
    product_name: str
    normalized_product_name: str
    brand: str | None
    model: str | None
    variant: str | None
    seller: str | None
    seller_url: str | None
    listed_price: int | None
    shipping_price: int | None
    total_price: int | None
    currency: str
    stock_status: str
    installment_count: int | None
    cash_price_installment: int | None
    scraped_at: datetime
    raw_hash: str


@dataclass(frozen=True, slots=True)
class AkakceCategoryItem:
    product_name: str
    product_url: str
    source_product_id: str
    normalized_brand: str | None
    normalized_model: str
    chipset: str | None
    vram_gb: int | None
    listed_price: int | None
    shipping_price: int | None
    total_price: int | None
    seller: str | None
    stock_status: str
    installment_count: int | None
    rank: int
    scraped_at: datetime
    raw_hash: str
    validation_warnings: tuple[str, ...] = ()
