from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class NotificationPriority(StrEnum):
    URGENT = "urgent"
    NORMAL = "normal"
    DIGEST = "digest"


class BaselineState(StrEnum):
    NOT_ESTABLISHED = "not_established"
    ESTABLISHED = "established"


@dataclass(frozen=True, slots=True)
class Source:
    key: str
    name: str
    url: str
    source_type: str


@dataclass(frozen=True, slots=True)
class ProductTarget:
    id: str
    source_key: str
    name: str
    url: str
    source_type: str
    target_price_kurus: int | None = None


@dataclass(frozen=True, slots=True)
class ProductListing:
    target_id: str
    canonical_url: str
    title: str
    seller: str | None
    price_kurus: int | None
    in_stock: bool | None


@dataclass(frozen=True, slots=True)
class ForumTopic:
    topic_id: str
    canonical_topic_url: str
    title: str
    prefix_labels: tuple[str, ...] = ()
    author: str | None = None
    created_at: datetime | None = None
    last_activity_at: datetime | None = None
    last_activity_user: str | None = None
    reply_count: int = 0
    view_count: int = 0
    page_count: int = 1
    is_locked: bool = False
    is_sticky: bool = False
    detail: ForumTopicDetail | None = None


@dataclass(frozen=True, slots=True)
class ExternalLink:
    url: str
    domain: str
    store_name: str | None = None
    product_names: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PriceMention:
    price_kurus: int
    context: str
    product_name: str | None = None
    is_previous_price: bool = False


@dataclass(frozen=True, slots=True)
class ForumTopicDetail:
    first_message: str
    topic_id: str | None = None
    canonical_topic_url: str | None = None
    title: str | None = None
    prefix_labels: tuple[str, ...] = ()
    edited_at: datetime | None = None
    external_links: tuple[ExternalLink, ...] = ()
    prices: tuple[PriceMention, ...] = ()
    coupon_codes: tuple[str, ...] = ()
    personalized_coupon: bool = False
    cart_discount: bool = False
    stock_status: str | None = None
    back_in_stock: bool = False
    discount_expired: bool = False
    shipping_info: str | None = None
    product_names: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExtractedOffer:
    title: str
    url: str
    price_kurus: int | None
    match_reason: str


@dataclass(frozen=True, slots=True)
class PriceObservation:
    listing_id: int
    observed_at: datetime
    price_kurus: int
    shipping_kurus: int | None = None


@dataclass(frozen=True, slots=True)
class StockObservation:
    listing_id: int
    observed_at: datetime
    in_stock: bool


@dataclass(frozen=True, slots=True)
class NotificationEvent:
    event_key: str
    source_key: str
    event_type: str
    title: str
    url: str
    priority: NotificationPriority
    match_reason: str
    price_kurus: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    id: int | None = None


@dataclass(frozen=True, slots=True)
class SourceFetchResult:
    source_key: str
    fetched_at: datetime
    succeeded: bool
    status_code: int | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class ParseResult:
    topics: tuple[ForumTopic, ...]
    errors: tuple[str, ...] = ()
