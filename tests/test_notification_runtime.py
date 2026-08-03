from io import StringIO

from deal_watcher.logging_setup import redact_secrets
from deal_watcher.models.domain import NotificationEvent, NotificationPriority
from deal_watcher.notifiers.base import DryRunNotifier, NotificationDispatcher
from deal_watcher.services.notification_conversion import price_event_to_notification
from deal_watcher.services.price_history import PriceEvent
from deal_watcher.storage.database import Database
from deal_watcher.storage.repository import DealRepository


def test_price_event_conversion_skips_baseline_and_keeps_details() -> None:
    baseline = PriceEvent(
        "baseline_created", "p", "1", None, None, None, None, NotificationPriority.NORMAL, "b"
    )
    assert price_event_to_notification(baseline, title="Ürün", url="https://example.test") is None
    event = PriceEvent(
        "price_drop_5_percent",
        "p",
        "1",
        "satıcı",
        "10000",
        "9000",
        -10.0,
        NotificationPriority.NORMAL,
        "drop",
        {"shipping_price": None, "total_price": 9000, "url": "https://example.test/p"},
    )
    converted = price_event_to_notification(event, title="Ürün", url="https://example.test")
    assert converted is not None
    assert converted.price_kurus == 9000
    assert "Satıcı: satıcı" in converted.payload["details"]


def test_delivery_error_is_redacted_and_dry_run_supports_turkish_emoji(tmp_path) -> None:
    token = "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef"
    assert token not in redact_secrets(f"https://api.telegram.org/bot{token}/sendMessage")
    database = Database(tmp_path / "runtime.sqlite3")
    database.migrate()
    event = NotificationEvent(
        "e",
        "test",
        "price_drop",
        "İndirim 🎉",
        "https://example.test",
        NotificationPriority.NORMAL,
        "test",
    )
    output = StringIO()

    class Broken:
        channel = "telegram"

        def send(self, _event):
            raise RuntimeError(f"https://api.telegram.org/bot{token}/sendMessage failed")

    with database.session() as connection:
        repository = DealRepository(connection)
        saved = repository.add_event(
            repository.ensure_source(
                __import__("deal_watcher.models.domain", fromlist=["Source"]).Source(
                    "test", "test", "https://example.test", "test"
                )
            ),
            event,
        )
        assert saved
        assert (
            NotificationDispatcher(lambda: repository, [Broken(), DryRunNotifier(output)]).dispatch(
                [saved]
            )
            == 1
        )
        error = connection.execute(
            "SELECT error FROM notification_deliveries WHERE channel='telegram'"
        ).fetchone()[0]
    assert token not in error
    assert "[REDACTED]" in error
    assert "İndirim 🎉" in output.getvalue()
