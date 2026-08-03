from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Protocol, TextIO

from deal_watcher.logging_setup import redact_secrets
from deal_watcher.models.domain import NotificationEvent
from deal_watcher.storage.repository import DealRepository


class Notifier(Protocol):
    channel: str

    def send(self, event: NotificationEvent) -> None: ...


@dataclass(frozen=True, slots=True)
class NotificationDispatchResult:
    delivered: int = 0
    failed: int = 0


def format_event(event: NotificationEvent) -> str:
    message = event.payload.get("message")
    if isinstance(message, str) and message:
        return message
    price = f"{event.price_kurus / 100:,.2f} TL" if event.price_kurus is not None else "-"
    return "\n".join(
        (
            f"Kaynak: {event.source_key}",
            f"Başlık/Ürün: {event.title}",
            f"Fiyat: {price}",
            f"Öncelik: {event.priority.value}",
            f"Olay: {event.event_type}",
            f"Eşleşme nedeni: {event.match_reason}",
            f"URL: {event.url}",
            *(f"Detay: {event.payload['details']}" for _ in [0] if event.payload.get("details")),
        )
    )


class DryRunNotifier:
    channel = "dry_run"

    def __init__(self, stream: TextIO):
        self.stream = stream

    def send(self, event: NotificationEvent) -> None:
        self.stream.write(format_event(event) + "\n---\n")


class LoggingNotifier:
    channel = "logging"

    def __init__(self, logger: logging.Logger | None = None):
        self.logger = logger or logging.getLogger("deal_watcher.notifications")

    def send(self, event: NotificationEvent) -> None:
        self.logger.info("\n%s", format_event(event))


class NotificationDispatcher:
    def __init__(
        self,
        repository_factory: Callable[[], DealRepository],
        notifiers: Iterable[Notifier],
    ):
        self.repository_factory = repository_factory
        self.notifiers = tuple(notifiers)

    def dispatch(self, events: Iterable[NotificationEvent]) -> int:
        return self.dispatch_with_stats(events).delivered

    def dispatch_with_stats(
        self, events: Iterable[NotificationEvent]
    ) -> NotificationDispatchResult:
        delivered = 0
        failed = 0
        repository = self.repository_factory()
        for event in events:
            if event.id is None:
                raise ValueError("event must be persisted before dispatch")
            for notifier in self.notifiers:
                if repository.delivery_exists(event.id, notifier.channel):
                    continue
                try:
                    notifier.send(event)
                except Exception as exc:  # noqa: BLE001 - channel failures must be isolated
                    repository.record_delivery(
                        event.id, notifier.channel, "failed", redact_secrets(str(exc))
                    )
                    failed += 1
                    continue
                repository.record_delivery(event.id, notifier.channel, "delivered")
                delivered += 1
        return NotificationDispatchResult(delivered=delivered, failed=failed)
