from datetime import UTC, datetime, timedelta

from deal_watcher.models.domain import NotificationPriority
from deal_watcher.services.price_history import PriceHistoryService
from deal_watcher.sources.akakce_common import AkakceOffer
from deal_watcher.storage.database import Database


def offer(price: int, captured: datetime, stock: str = "in_stock") -> AkakceOffer:
    return AkakceOffer(
        "100",
        "https://example.test/p/100",
        "RTX 5070 Ti",
        "rtx 5070 ti",
        "ASUS",
        "RTX 5070 Ti",
        "TUF",
        "seller",
        None,
        price,
        0,
        price,
        "TRY",
        stock,
        None,
        None,
        captured,
        f"{price}-{captured.isoformat()}",
    )


def test_price_thresholds_baseline_lows_and_stock_return(tmp_path) -> None:
    database = Database(tmp_path / "prices.sqlite3")
    database.migrate()
    first = datetime.now(UTC) - timedelta(minutes=5)
    with database.session() as connection:
        service = PriceHistoryService(connection)
        baseline = service.observe("rtx-5070-ti", offer(100_000, first, "out_of_stock"))
        assert [event.event_type for event in baseline] == ["baseline_created"]
        events = service.observe(
            "rtx-5070-ti", offer(90_000, first + timedelta(minutes=1), "in_stock")
        )
        kinds = {event.event_type for event in events}
        assert {
            "price_drop_10_percent",
            "price_drop_5_percent",
            "price_drop_3_percent",
            "back_in_stock",
        } <= kinds
        assert all(
            event.priority in (NotificationPriority.NORMAL, NotificationPriority.URGENT)
            for event in events
        )


def test_price_event_dedup_same_observation(tmp_path) -> None:
    database = Database(tmp_path / "dedup.sqlite3")
    database.migrate()
    timestamp = datetime.now(UTC)
    with database.session() as connection:
        service = PriceHistoryService(connection)
        service.observe("p", offer(100_000, timestamp))
        service.observe("p", offer(90_000, timestamp + timedelta(minutes=1)))
        repeated = service.observe("p", offer(90_000, timestamp + timedelta(minutes=2)))
        assert not any(event.event_type.startswith("price_drop") for event in repeated)


def test_unknown_shipping_survives_three_scans_without_minimum_crash(tmp_path) -> None:
    database = Database(tmp_path / "unknown-shipping.sqlite3")
    database.migrate()
    captured = datetime.now(UTC)
    unknown_shipping = AkakceOffer(
        "100",
        "https://example.test/p/100",
        "RTX 5070 Ti",
        "rtx 5070 ti",
        "ASUS",
        "RTX 5070 Ti",
        None,
        "seller",
        None,
        100_000,
        None,
        None,
        "TRY",
        "in_stock",
        None,
        None,
        captured,
        "unknown",
    )
    with database.session() as connection:
        service = PriceHistoryService(connection)
        first = service.observe("p", unknown_shipping)
        second = service.observe("p", unknown_shipping)
        third = service.observe("p", unknown_shipping)
        assert [event.event_type for event in first] == ["baseline_created"]
        assert second == ()
        assert third == ()
        assert connection.execute("SELECT total_price FROM product_snapshots").fetchone()[0] is None
