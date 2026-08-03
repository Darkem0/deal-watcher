from pathlib import Path

import pytest

from deal_watcher.models.domain import ForumTopic
from deal_watcher.services.classification import classify_topic
from deal_watcher.services.forum_monitor import ForumMonitorService
from deal_watcher.sources.forum_topic import (
    DonanimArsiviForumTopicParser,
    ForumTopicDetailParseError,
)
from deal_watcher.storage.database import Database
from deal_watcher.storage.repository import DealRepository

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://forum.donanimarsivi.com/konular/ornek.1/"


def detail(name: str):
    html = (ROOT / "tests" / "fixtures" / name).read_text(encoding="utf-8")
    return DonanimArsiviForumTopicParser().parse(html, BASE_URL)


def test_detail_parser_extracts_prices_coupon_stock_links_and_shipping() -> None:
    parsed = detail("topic_detail_offer.html")
    assert parsed.topic_id == "77"
    assert parsed.canonical_topic_url.endswith("rtx-firsati.77/")
    assert parsed.title == "RTX 5070 Ti fırsatı"
    assert [item.price_kurus for item in parsed.prices] == [
        3_199_900,
        3_499_900,
        1_299_900,
        179_900,
    ]
    assert parsed.prices[1].is_previous_price
    assert parsed.coupon_codes == ("DONANIM500", "PERSONALIZED")
    assert parsed.personalized_coupon and parsed.cart_discount
    assert parsed.back_in_stock and parsed.stock_status == "tekrar stokta"
    assert parsed.shipping_info == "Kargo ücretsiz"
    assert parsed.external_links[0].domain == "example-store.test"
    assert parsed.external_links[0].store_name == "Örnek Mağaza"


def test_detail_parser_filters_specs_and_forum_links() -> None:
    parsed = detail("topic_detail_edge_cases.html")
    assert [item.price_kurus for item in parsed.prices] == [3_190_000]
    assert parsed.external_links == ()
    assert parsed.discount_expired


@pytest.mark.parametrize(
    ("title", "expected", "secondary"),
    [
        ("RTX 5070 ekran kartı fırsatı", "gpu", ()),
        ("Ryzen 9700X işlemci soğutucusu", "cpu_cooler", ()),
        ("RTX 5070 hazır sistem", "complete_system", ()),
        ("SSD kutusu fırsatı", "other", ()),
        ("850W PSU kablosu", "other", ()),
        ("Watch kayışı", "other", ()),
    ],
)
def test_classification_avoids_common_false_matches(app_config, title, expected, secondary) -> None:
    result = classify_topic(ForumTopic("x", "https://example.test/x", title), app_config.forum)
    assert result.category == expected
    assert result.secondary_categories == secondary


def test_classification_uses_message_and_secondary_categories(app_config) -> None:
    topic = ForumTopic(
        "x",
        "https://example.test/x",
        "Anakart ve Ryzen fırsatı",
        ("Fırsat",),
        detail=detail("topic_detail_offer.html"),
    )
    result = classify_topic(topic, app_config.forum, target_names=("RTX 5070 Ti",))
    assert result.category == "gpu"
    assert {"cpu", "cpu_cooler", "storage", "memory", "power_supply"} <= set(
        result.secondary_categories
    )
    assert result.priority.value == "urgent"


def test_missing_message_is_controlled_parse_error() -> None:
    with pytest.raises(ForumTopicDetailParseError, match="first message"):
        DonanimArsiviForumTopicParser().parse("<html><body></body></html>", BASE_URL)


def test_detail_events_are_persistently_deduplicated(tmp_path: Path, app_config) -> None:
    database = Database(tmp_path / "detail-events.sqlite3")
    database.migrate()
    parsed = detail("topic_detail_offer.html")
    topic = ForumTopic("77", "https://example.test/topic.77/", "RTX 5070 Ti fırsatı", detail=parsed)
    baseline = ForumTopic("77", topic.canonical_topic_url, topic.title)
    with database.session() as connection:
        monitor = ForumMonitorService(DealRepository(connection), app_config.forum)
        assert monitor.process((baseline,)) == []
        events = monitor.process((topic,))
        assert {event.event_type for event in events} >= {
            "price_detected",
            "coupon_detected",
            "back_in_stock",
            "low_stock",
        }
        assert monitor.process((topic,)) == []
