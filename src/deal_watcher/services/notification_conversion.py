from __future__ import annotations

from deal_watcher.models.domain import NotificationEvent
from deal_watcher.services.price_history import PriceEvent


def price_event_to_notification(
    event: PriceEvent, *, title: str, url: str
) -> NotificationEvent | None:
    """Convert one persisted Akakce domain event into the shared notification contract."""
    if event.event_type == "baseline_created":
        return None
    payload = dict(event.payload or {})
    product_url = str(payload.get("url") or url)
    old_price = event.old_value
    new_price = event.new_value
    details = "; ".join(
        part
        for part in (
            f"Model/varyant: {payload.get('variant')}" if payload.get("variant") else None,
            f"Satıcı: {event.seller}" if event.seller else None,
            f"Eski fiyat: {old_price}" if old_price else None,
            f"Yeni fiyat: {new_price}" if new_price else None,
            f"Değişim: {event.percentage_change:.2f}%"
            if event.percentage_change is not None
            else None,
            f"Kargo: {payload.get('shipping_price')}"
            if payload.get("shipping_price") is not None
            else None,
            f"Toplam: {payload.get('total_price')}"
            if payload.get("total_price") is not None
            else None,
            f"Zaman: {payload.get('captured_at')}" if payload.get("captured_at") else None,
        )
        if part
    )
    payload.update({"old_value": old_price, "new_value": new_price, "details": details})
    price = payload.get("total_price")
    return NotificationEvent(
        event_key=f"akakce:{event.dedup_key}",
        source_key="akakce",
        event_type=event.event_type,
        title=str(payload.get("product_name") or title),
        url=product_url,
        priority=event.priority,
        match_reason="Akakçe fiyat/stok olayı",
        price_kurus=price if isinstance(price, int) else None,
        payload=payload,
    )
