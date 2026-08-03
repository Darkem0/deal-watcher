from __future__ import annotations

from datetime import UTC

from deal_watcher.models.config import ForumConfig
from deal_watcher.models.domain import ForumTopic, NotificationEvent, Source
from deal_watcher.services.classification import classify_topic, topic_signals
from deal_watcher.storage.repository import DealRepository


class ForumMonitorService:
    def __init__(self, repository: DealRepository, config: ForumConfig):
        self.repository = repository
        self.config = config
        self.source = Source(
            key="donanim_arsivi_sicak_firsatlar",
            name=config.source.name,
            url=str(config.source.url),
            source_type="forum_category",
        )

    def process(self, topics: tuple[ForumTopic, ...]) -> list[NotificationEvent]:
        source_id = self.repository.ensure_source(self.source)
        is_baseline = not self.repository.baseline_exists(source_id)
        events: list[NotificationEvent] = []
        for topic in topics:
            previous = self.repository.get_topic(source_id, topic.topic_id)
            if not is_baseline:
                candidates = self._events_for_change(previous, topic)
                for candidate in candidates:
                    stored = self.repository.add_event(source_id, candidate)
                    if stored is not None:
                        events.append(stored)
            self.repository.upsert_topic(source_id, topic)
        if is_baseline:
            self.repository.establish_baseline(source_id, len(topics))
        else:
            self.repository.touch_baseline(source_id, len(topics))
        return events

    def _events_for_change(
        self, previous: ForumTopic | None, current: ForumTopic
    ) -> list[NotificationEvent]:
        current_signals = topic_signals(current)
        classification = classify_topic(current, self.config)
        if previous is None:
            if current.is_sticky or current.is_locked or {"reklam", "ana_konu"} & current_signals:
                return []
            events = [
                NotificationEvent(
                    event_key=f"forum:{current.topic_id}:yeni_konu",
                    source_key=self.source.key,
                    event_type="yeni_konu",
                    title=current.title,
                    url=current.canonical_topic_url,
                    priority=classification.priority,
                    match_reason=f"Yeni forum konusu; {classification.reason}",
                    payload={"topic_id": current.topic_id, "category": classification.category},
                )
            ]
            return [*events, *self._detail_events(None, current, classification)]

        previous_signals = topic_signals(previous)
        events: list[NotificationEvent] = []
        for signal in ("stok_geri_geldi", "indirim_bitti"):
            if signal in current_signals and signal not in previous_signals:
                activity = current.last_activity_at
                if activity is not None:
                    if activity.tzinfo is None:
                        activity = activity.replace(tzinfo=UTC)
                    occurrence = activity.astimezone(UTC).isoformat()
                else:
                    occurrence = current.title.casefold()
                events.append(
                    NotificationEvent(
                        event_key=f"forum:{current.topic_id}:{signal}:{occurrence}",
                        source_key=self.source.key,
                        event_type=signal,
                        title=current.title,
                        url=current.canonical_topic_url,
                        priority=classification.priority,
                        match_reason=f"Durum değişikliği: {signal}; {classification.reason}",
                        payload={"topic_id": current.topic_id, "category": classification.category},
                    )
                )
        events.extend(self._detail_events(previous, current, classification))
        return events

    def _detail_events(self, previous, current, classification):
        detail = current.detail
        if detail is None:
            return []
        previous_detail = previous.detail if previous is not None else None
        events: list[NotificationEvent] = []

        def add(event_type: str, reason: str, suffix: str) -> None:
            events.append(
                NotificationEvent(
                    event_key=f"forum:{current.topic_id}:{event_type}:{suffix}",
                    source_key=self.source.key,
                    event_type=event_type,
                    title=current.title,
                    url=current.canonical_topic_url,
                    priority=classification.priority,
                    match_reason=reason,
                    price_kurus=detail.prices[0].price_kurus if detail.prices else None,
                    payload={
                        "topic_id": current.topic_id,
                        "category": classification.category,
                        "secondary_categories": classification.secondary_categories,
                    },
                )
            )

        if detail.prices and previous_detail is None:
            add("price_detected", "İlk konu fiyatı ayrıştırıldı", str(detail.prices[0].price_kurus))
        elif (
            detail.prices
            and previous_detail
            and previous_detail.prices
            and min(item.price_kurus for item in detail.prices)
            < min(item.price_kurus for item in previous_detail.prices)
        ):
            add(
                "price_reduced",
                "Konu fiyatı önceki gözleme göre düştü",
                str(detail.prices[0].price_kurus),
            )
        if detail.coupon_codes and (previous_detail is None or not previous_detail.coupon_codes):
            add("coupon_detected", "Yeni kupon kodu ayrıştırıldı", detail.coupon_codes[0])
        low_stock_text = any(
            phrase in detail.first_message.casefold()
            for phrase in ("son stok", "1 adet", "2 adet", "sınırlı stok")
        )
        if low_stock_text and (
            previous_detail is None
            or previous_detail.stock_status not in {"son stok", "1 adet", "2 adet", "sınırlı stok"}
        ):
            add("low_stock", "Düşük stok sinyali ayrıştırıldı", detail.stock_status)
        if detail.back_in_stock and (previous_detail is None or not previous_detail.back_in_stock):
            add("back_in_stock", "Tekrar stokta sinyali ayrıştırıldı", "back")
        if detail.discount_expired and (
            previous_detail is None or not previous_detail.discount_expired
        ):
            add("discount_expired", "İndirim bitti sinyali ayrıştırıldı", "expired")
        return events
