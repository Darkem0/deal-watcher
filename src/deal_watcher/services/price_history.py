from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from deal_watcher.models.domain import NotificationPriority
from deal_watcher.sources.akakce_common import AkakceCategoryItem, AkakceOffer
from deal_watcher.storage.repository import utc_now_text


@dataclass(frozen=True, slots=True)
class PriceEvent:
    event_type: str
    product_config_id: str
    source_product_id: str
    seller: str | None
    old_value: str | None
    new_value: str | None
    percentage_change: float | None
    priority: NotificationPriority
    dedup_key: str
    payload: dict[str, object] | None = None


class PriceHistoryService:
    def __init__(
        self,
        connection,
        *,
        anomaly_percent: float = 35.0,
        target_price_kurus: int | None = None,
        urgent_price_kurus: int | None = None,
        now=None,
    ):
        self.connection = connection
        self.anomaly_percent = anomaly_percent
        self.target_price_kurus = target_price_kurus
        self.urgent_price_kurus = urgent_price_kurus
        self.now = now or (lambda: datetime.now(UTC))

    def observe(self, product_config_id: str, offer: AkakceOffer) -> tuple[PriceEvent, ...]:
        captured = offer.scraped_at.astimezone(UTC)
        captured_text = captured.isoformat().replace("+00:00", "Z")
        seller_key = offer.seller or ""
        self.connection.execute(
            """INSERT INTO product_snapshots(
                source, source_product_id, product_config_id, normalized_model, seller,
                listed_price, shipping_price, total_price, stock_status, captured_at, raw_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "akakce",
                offer.source_product_id,
                product_config_id,
                offer.normalized_product_name,
                seller_key,
                offer.listed_price,
                offer.shipping_price,
                offer.total_price,
                offer.stock_status,
                captured_text,
                offer.raw_hash,
            ),
        )
        key = (product_config_id, offer.source_product_id, seller_key)
        row = self.connection.execute(
            "SELECT * FROM product_states WHERE product_config_id=? AND source_product_id=? AND seller IS ?",
            key,
        ).fetchone()
        previous = row["current_price"] if row else None
        previous_stock = row["current_stock_status"] if row else None
        baseline = row["baseline_price"] if row else offer.total_price
        lows = self._lows(product_config_id, offer.source_product_id, seller_key, offer.total_price)
        comparable_prices = tuple(
            value
            for value in (row["all_time_low"] if row else None, offer.total_price)
            if value is not None
        )
        all_time_low = min(comparable_prices) if comparable_prices else None
        self.connection.execute(
            """INSERT INTO product_states(
                product_config_id, source_product_id, normalized_model, seller, first_seen_at,
                last_seen_at, baseline_price, previous_price, current_price, all_time_low,
                previous_stock_status, current_stock_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(product_config_id, source_product_id, seller) DO UPDATE SET
                normalized_model=excluded.normalized_model, last_seen_at=excluded.last_seen_at,
                previous_price=excluded.previous_price, current_price=excluded.current_price,
                all_time_low=excluded.all_time_low, previous_stock_status=excluded.previous_stock_status,
                current_stock_status=excluded.current_stock_status""",
            (
                product_config_id,
                offer.source_product_id,
                offer.normalized_product_name,
                seller_key,
                captured_text if row is None else row["first_seen_at"],
                captured_text,
                baseline,
                previous,
                offer.total_price,
                all_time_low,
                previous_stock,
                offer.stock_status,
            ),
        )
        events = self._events(
            product_config_id, offer, previous, previous_stock, baseline, lows, all_time_low
        )
        if previous is not None and offer.total_price is not None:
            base = f"{product_config_id}:{offer.source_product_id}:{offer.seller or '-'}"
            if self.target_price_kurus is not None and offer.total_price <= self.target_price_kurus:
                events.append(
                    self._event(
                        "target_price_reached",
                        f"{base}:target:{offer.total_price}",
                        product_config_id,
                        offer,
                        str(previous),
                        str(offer.total_price),
                        None,
                        NotificationPriority.NORMAL,
                    )
                )
            if self.urgent_price_kurus is not None and offer.total_price <= self.urgent_price_kurus:
                events.append(
                    self._event(
                        "urgent_price_reached",
                        f"{base}:urgent:{offer.total_price}",
                        product_config_id,
                        offer,
                        str(previous),
                        str(offer.total_price),
                        None,
                        NotificationPriority.URGENT,
                    )
                )
        stored: list[PriceEvent] = []
        for event in events:
            cursor = self.connection.execute(
                """INSERT OR IGNORE INTO price_events(
                    event_type, product_config_id, source_product_id, seller, old_value, new_value,
                    percentage_change, priority, created_at, dedup_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    event.event_type,
                    event.product_config_id,
                    event.source_product_id,
                    event.seller,
                    event.old_value,
                    event.new_value,
                    event.percentage_change,
                    event.priority.value,
                    utc_now_text(),
                    event.dedup_key,
                ),
            )
            if cursor.rowcount:
                stored.append(event)
        return tuple(stored)

    def observe_category(
        self, product_config_id: str, items: tuple[AkakceCategoryItem, ...]
    ) -> tuple[PriceEvent, ...]:
        active = [
            item
            for item in items
            if item.total_price is not None and item.stock_status != "out_of_stock"
        ]
        model_keys = sorted({item.normalized_model for item in items})
        cheapest = min(active, key=lambda item: item.total_price) if active else None
        row = self.connection.execute(
            "SELECT * FROM category_states WHERE product_config_id=?", (product_config_id,)
        ).fetchone()
        old_models = set(json.loads(row["model_keys_json"])) if row else set()
        events: list[PriceEvent] = []
        if row:
            for item in items:
                if item.normalized_model not in old_models:
                    events.append(
                        PriceEvent(
                            "new_listing",
                            product_config_id,
                            item.source_product_id,
                            item.seller,
                            None,
                            str(item.total_price) if item.total_price is not None else None,
                            None,
                            NotificationPriority.NORMAL,
                            f"category:{product_config_id}:new:{item.source_product_id}",
                        )
                    )
        if row and cheapest and row["cheapest_model"] != cheapest.normalized_model:
            events.append(
                PriceEvent(
                    "cheapest_model_changed",
                    product_config_id,
                    cheapest.source_product_id,
                    cheapest.seller,
                    row["cheapest_model"],
                    cheapest.normalized_model,
                    None,
                    NotificationPriority.NORMAL,
                    f"category:{product_config_id}:cheapest:{cheapest.normalized_model}:{cheapest.total_price}",
                )
            )
        self.connection.execute(
            "INSERT INTO category_states(product_config_id,model_keys_json,cheapest_model,cheapest_price,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(product_config_id) DO UPDATE SET model_keys_json=excluded.model_keys_json,cheapest_model=excluded.cheapest_model,cheapest_price=excluded.cheapest_price,updated_at=excluded.updated_at",
            (
                product_config_id,
                json.dumps(model_keys, ensure_ascii=False),
                cheapest.normalized_model if cheapest else None,
                cheapest.total_price if cheapest else None,
                utc_now_text(),
            ),
        )
        stored: list[PriceEvent] = []
        for event in events:
            cursor = self.connection.execute(
                "INSERT OR IGNORE INTO price_events(event_type,product_config_id,source_product_id,seller,old_value,new_value,percentage_change,priority,created_at,dedup_key) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    event.event_type,
                    event.product_config_id,
                    event.source_product_id,
                    event.seller,
                    event.old_value,
                    event.new_value,
                    event.percentage_change,
                    event.priority.value,
                    utc_now_text(),
                    event.dedup_key,
                ),
            )
            if cursor.rowcount:
                stored.append(event)
        return tuple(stored)

    def _lows(self, product_id, source_id, seller, current):
        if current is None:
            return {}
        now = self.now().astimezone(UTC)
        rows = self.connection.execute(
            "SELECT captured_at,total_price FROM product_snapshots WHERE product_config_id=? AND source_product_id=? AND seller IS ? AND total_price IS NOT NULL",
            (product_id, source_id, seller),
        ).fetchall()
        values = [(datetime.fromisoformat(row[0]), row[1]) for row in rows]
        return {
            days: min(
                (price for timestamp, price in values if timestamp >= now - timedelta(days=days)),
                default=None,
            )
            for days in (1, 7, 30)
        }

    def _events(self, product_id, offer, previous, previous_stock, baseline, lows, all_time_low):
        events: list[PriceEvent] = []
        current = offer.total_price
        base = f"{product_id}:{offer.source_product_id}:{offer.seller or '-'}"
        if previous is None:
            events.append(
                self._event(
                    "baseline_created",
                    base,
                    product_id,
                    offer,
                    None,
                    current,
                    None,
                    NotificationPriority.NORMAL,
                )
            )
            return events
        elif current is not None and previous and current < previous:
            drop = (previous - current) / previous * 100
            for threshold, name, priority in (
                (10, "price_drop_10_percent", NotificationPriority.URGENT),
                (5, "price_drop_5_percent", NotificationPriority.NORMAL),
                (3, "price_drop_3_percent", NotificationPriority.NORMAL),
            ):
                if drop >= threshold:
                    events.append(
                        self._event(
                            name,
                            f"{base}:{name}:{current}",
                            product_id,
                            offer,
                            str(previous),
                            str(current),
                            -drop,
                            priority,
                        )
                    )
        if previous_stock in ("out_of_stock", "unknown") and offer.stock_status == "in_stock":
            events.append(
                self._event(
                    "back_in_stock",
                    f"{base}:back:{current}",
                    product_id,
                    offer,
                    previous_stock,
                    offer.stock_status,
                    None,
                    NotificationPriority.NORMAL,
                )
            )
        if previous_stock == "in_stock" and offer.stock_status == "out_of_stock":
            events.append(
                self._event(
                    "out_of_stock",
                    f"{base}:out:{current}",
                    product_id,
                    offer,
                    previous_stock,
                    offer.stock_status,
                    None,
                    NotificationPriority.NORMAL,
                )
            )
        for days, name in ((1, "daily_low"), (7, "seven_day_low"), (30, "thirty_day_low")):
            if current is not None and lows.get(days) == current:
                events.append(
                    self._event(
                        name,
                        f"{base}:{name}:{current}",
                        product_id,
                        offer,
                        None,
                        str(current),
                        None,
                        NotificationPriority.NORMAL,
                    )
                )
        if current is not None and all_time_low == current:
            events.append(
                self._event(
                    "all_time_low",
                    f"{base}:all_time:{current}",
                    product_id,
                    offer,
                    None,
                    str(current),
                    None,
                    NotificationPriority.NORMAL,
                )
            )
        return events

    @staticmethod
    def _event(event_type, dedup_key, product_id, offer, old, new, pct, priority):
        return PriceEvent(
            event_type,
            product_id,
            offer.source_product_id,
            offer.seller,
            old,
            new,
            pct,
            priority,
            dedup_key,
            {
                "product_name": offer.product_name,
                "variant": offer.variant,
                "seller": offer.seller,
                "listed_price": offer.listed_price,
                "shipping_price": offer.shipping_price,
                "total_price": offer.total_price,
                "currency": offer.currency,
                "url": offer.canonical_url,
                "captured_at": offer.scraped_at.isoformat(),
            },
        )
