from __future__ import annotations

import json
import sqlite3
from dataclasses import replace
from datetime import UTC, datetime

from deal_watcher.logging_setup import redact_secrets
from deal_watcher.models.domain import (
    ExternalLink,
    ForumTopic,
    ForumTopicDetail,
    NotificationEvent,
    PriceMention,
    Source,
)


def utc_now_text() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _datetime_text(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class DealRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def ensure_source(self, source: Source) -> int:
        now = utc_now_text()
        self.connection.execute(
            "INSERT INTO sources(source_key, name, base_url, source_type, created_at) "
            "VALUES (?, ?, ?, ?, ?) ON CONFLICT(source_key) DO UPDATE SET "
            "name=excluded.name, base_url=excluded.base_url, source_type=excluded.source_type",
            (source.key, source.name, source.url, source.source_type, now),
        )
        row = self.connection.execute(
            "SELECT id FROM sources WHERE source_key = ?", (source.key,)
        ).fetchone()
        assert row is not None
        return int(row["id"])

    def baseline_exists(self, source_id: int) -> bool:
        return (
            self.connection.execute(
                "SELECT 1 FROM baseline_states WHERE source_id = ?", (source_id,)
            ).fetchone()
            is not None
        )

    def establish_baseline(self, source_id: int, item_count: int) -> None:
        now = utc_now_text()
        self.connection.execute(
            "INSERT INTO baseline_states(source_id, established_at, last_success_at, item_count) "
            "VALUES (?, ?, ?, ?) ON CONFLICT(source_id) DO UPDATE SET "
            "last_success_at=excluded.last_success_at, item_count=excluded.item_count",
            (source_id, now, now, item_count),
        )

    def touch_baseline(self, source_id: int, item_count: int) -> None:
        self.connection.execute(
            "UPDATE baseline_states SET last_success_at = ?, item_count = ? WHERE source_id = ?",
            (utc_now_text(), item_count, source_id),
        )

    def get_topic(self, source_id: int, topic_id: str) -> ForumTopic | None:
        row = self.connection.execute(
            "SELECT * FROM forum_topics WHERE source_id = ? AND topic_id = ?",
            (source_id, topic_id),
        ).fetchone()
        return self._topic_from_row(row) if row else None

    def upsert_topic(self, source_id: int, topic: ForumTopic) -> None:
        now = utc_now_text()
        self.connection.execute(
            """
            INSERT INTO forum_topics(
                source_id, topic_id, canonical_url, title, prefix_labels_json, author,
                created_at, last_activity_at, last_activity_user, reply_count, view_count,
                page_count, is_locked, is_sticky, detail_json, first_seen_at, last_seen_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id, topic_id) DO UPDATE SET
                canonical_url=excluded.canonical_url, title=excluded.title,
                prefix_labels_json=excluded.prefix_labels_json, author=excluded.author,
                created_at=COALESCE(forum_topics.created_at, excluded.created_at),
                last_activity_at=excluded.last_activity_at,
                last_activity_user=excluded.last_activity_user,
                reply_count=excluded.reply_count, view_count=excluded.view_count,
                page_count=excluded.page_count, is_locked=excluded.is_locked,
                is_sticky=excluded.is_sticky, last_seen_at=excluded.last_seen_at
                ,detail_json=excluded.detail_json
            """,
            (
                source_id,
                topic.topic_id,
                topic.canonical_topic_url,
                topic.title,
                json.dumps(topic.prefix_labels, ensure_ascii=False),
                topic.author,
                _datetime_text(topic.created_at),
                _datetime_text(topic.last_activity_at),
                topic.last_activity_user,
                topic.reply_count,
                topic.view_count,
                topic.page_count,
                int(topic.is_locked),
                int(topic.is_sticky),
                json.dumps(_detail_json(topic.detail), ensure_ascii=False, sort_keys=True),
                now,
                now,
            ),
        )

    def add_event(self, source_id: int, event: NotificationEvent) -> NotificationEvent | None:
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO notification_events(
                source_id, event_key, event_type, priority, title, url, price_kurus,
                match_reason, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                event.event_key,
                event.event_type,
                event.priority.value,
                event.title,
                event.url,
                event.price_kurus,
                event.match_reason,
                json.dumps(event.payload, ensure_ascii=False, sort_keys=True),
                utc_now_text(),
            ),
        )
        if cursor.rowcount == 0:
            return None
        return replace(event, id=int(cursor.lastrowid))

    def delivery_exists(self, event_id: int, channel: str) -> bool:
        return (
            self.connection.execute(
                "SELECT 1 FROM notification_deliveries "
                "WHERE event_id=? AND channel=? AND status='delivered'",
                (event_id, channel),
            ).fetchone()
            is not None
        )

    def record_delivery(
        self, event_id: int, channel: str, status: str, error: str | None = None
    ) -> None:
        self.connection.execute(
            "INSERT INTO notification_deliveries("
            "event_id, channel, delivered_at, status, error) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(event_id, channel) DO UPDATE SET "
            "delivered_at=excluded.delivered_at, status=excluded.status, error=excluded.error",
            (event_id, channel, utc_now_text(), status, redact_secrets(error) if error else None),
        )

    def record_fetch_run(
        self,
        *,
        source_id: int,
        started_at: str,
        completed_at: str,
        status: str,
        status_code: int | None = None,
        elapsed_ms: int | None = None,
        attempt_count: int = 0,
        error_type: str | None = None,
        masked_error_message: str | None = None,
        items_discovered: int = 0,
        events_created: int = 0,
    ) -> int:
        cursor = self.connection.execute(
            """INSERT INTO source_fetch_runs(
                source_id, started_at, completed_at, succeeded, status_code, item_count,
                error, status, elapsed_ms, attempt_count, error_type, masked_error_message, events_created
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                source_id,
                started_at,
                completed_at,
                int(status == "success"),
                status_code,
                items_discovered,
                masked_error_message,
                status,
                elapsed_ms,
                attempt_count,
                error_type,
                masked_error_message,
                events_created,
            ),
        )
        return int(cursor.lastrowid)

    @staticmethod
    def _topic_from_row(row: sqlite3.Row) -> ForumTopic:
        def parse_time(value: str | None) -> datetime | None:
            return datetime.fromisoformat(value) if value else None

        detail_data = json.loads(row["detail_json"]) if "detail_json" in row else {}
        detail = _detail_from_json(detail_data)
        return ForumTopic(
            topic_id=row["topic_id"],
            canonical_topic_url=row["canonical_url"],
            title=row["title"],
            prefix_labels=tuple(json.loads(row["prefix_labels_json"])),
            author=row["author"],
            created_at=parse_time(row["created_at"]),
            last_activity_at=parse_time(row["last_activity_at"]),
            last_activity_user=row["last_activity_user"],
            reply_count=row["reply_count"],
            view_count=row["view_count"],
            page_count=row["page_count"],
            is_locked=bool(row["is_locked"]),
            is_sticky=bool(row["is_sticky"]),
            detail=detail,
        )


def _detail_json(detail: ForumTopicDetail | None) -> dict[str, object]:
    if detail is None:
        return {}
    return {
        "first_message": detail.first_message,
        "topic_id": detail.topic_id,
        "canonical_topic_url": detail.canonical_topic_url,
        "title": detail.title,
        "prefix_labels": detail.prefix_labels,
        "edited_at": _datetime_text(detail.edited_at),
        "external_links": [
            link.__dict__
            if hasattr(link, "__dict__")
            else {
                "url": link.url,
                "domain": link.domain,
                "store_name": link.store_name,
                "product_names": link.product_names,
            }
            for link in detail.external_links
        ],
        "prices": [
            {
                "price_kurus": price.price_kurus,
                "context": price.context,
                "product_name": price.product_name,
                "is_previous_price": price.is_previous_price,
            }
            for price in detail.prices
        ],
        "coupon_codes": detail.coupon_codes,
        "personalized_coupon": detail.personalized_coupon,
        "cart_discount": detail.cart_discount,
        "stock_status": detail.stock_status,
        "back_in_stock": detail.back_in_stock,
        "discount_expired": detail.discount_expired,
        "shipping_info": detail.shipping_info,
        "product_names": detail.product_names,
    }


def _detail_from_json(data: dict[str, object]) -> ForumTopicDetail | None:
    if not data:
        return None
    return ForumTopicDetail(
        first_message=str(data.get("first_message", "")),
        topic_id=data.get("topic_id") if isinstance(data.get("topic_id"), str) else None,
        canonical_topic_url=data.get("canonical_topic_url")
        if isinstance(data.get("canonical_topic_url"), str)
        else None,
        title=data.get("title") if isinstance(data.get("title"), str) else None,
        prefix_labels=tuple(data.get("prefix_labels", [])),
        edited_at=datetime.fromisoformat(str(data["edited_at"])) if data.get("edited_at") else None,
        external_links=tuple(ExternalLink(**item) for item in data.get("external_links", [])),
        prices=tuple(PriceMention(**item) for item in data.get("prices", [])),
        coupon_codes=tuple(data.get("coupon_codes", [])),
        personalized_coupon=bool(data.get("personalized_coupon", False)),
        cart_discount=bool(data.get("cart_discount", False)),
        stock_status=data.get("stock_status")
        if isinstance(data.get("stock_status"), str)
        else None,
        back_in_stock=bool(data.get("back_in_stock", False)),
        discount_expired=bool(data.get("discount_expired", False)),
        shipping_info=data.get("shipping_info")
        if isinstance(data.get("shipping_info"), str)
        else None,
        product_names=tuple(data.get("product_names", [])),
    )
