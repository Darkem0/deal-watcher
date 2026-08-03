from io import StringIO
from pathlib import Path

from deal_watcher.notifiers.base import DryRunNotifier, NotificationDispatcher
from deal_watcher.services.forum_monitor import ForumMonitorService
from deal_watcher.sources.forum import DonanimArsiviForumParser
from deal_watcher.storage.database import Database
from deal_watcher.storage.repository import DealRepository

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://forum.donanimarsivi.com/forumlar/Sicakfirsatlar/"


def parse_fixture(name: str):
    html = (ROOT / "tests" / "fixtures" / name).read_text(encoding="utf-8")
    result = DonanimArsiviForumParser().parse(html, BASE_URL)
    assert not result.errors
    return result.topics


def test_parser_extracts_complete_topic_fields() -> None:
    topics = parse_fixture("forum_baseline.html")
    topic = topics[0]
    assert topic.topic_id == "100"
    assert (
        topic.canonical_topic_url == "https://forum.donanimarsivi.com/konular/rtx-5070-firsati.100/"
    )
    assert topic.title == "RTX 5070 ekran kartı fırsatı"
    assert topic.prefix_labels == ("Fırsat",)
    assert topic.author == "alice"
    assert topic.created_at is not None
    assert topic.last_activity_at is not None
    assert topic.last_activity_user == "bob"
    assert topic.reply_count == 3
    assert topic.view_count == 1200
    assert topic.page_count == 1
    assert not topic.is_locked
    assert not topic.is_sticky
    assert topics[2].is_locked and topics[2].is_sticky


def test_parser_accepts_real_xenforo_list_shape() -> None:
    topics = parse_fixture("forum_real_shape.html")
    assert topics[0].topic_id == "1033348"
    assert topics[0].author == "itopya.com"
    assert topics[0].prefix_labels == ("🔥İndirim",)


def test_baseline_change_detection_and_persistent_dedup(tmp_path: Path, app_config) -> None:
    database = Database(tmp_path / "flow.sqlite3")
    database.migrate()
    output = StringIO()
    with database.session() as connection:
        repository = DealRepository(connection)
        monitor = ForumMonitorService(repository, app_config.forum)

        baseline_events = monitor.process(parse_fixture("forum_baseline.html"))
        assert baseline_events == []
        assert repository.baseline_exists(repository.ensure_source(monitor.source))

        events = monitor.process(parse_fixture("forum_update.html"))
        assert {event.event_type for event in events} == {"yeni_konu", "stok_geri_geldi"}
        assert {event.payload["topic_id"] for event in events} == {"101", "102"}
        assert all(event.payload["topic_id"] != "100" for event in events)
        assert all(event.payload["topic_id"] != "901" for event in events)

        updated = repository.get_topic(repository.ensure_source(monitor.source), "100")
        assert updated is not None
        assert updated.title.endswith("başlık güncellendi")
        assert updated.reply_count == 9

        dispatcher = NotificationDispatcher(
            lambda: repository,
            [DryRunNotifier(output)],
        )
        assert dispatcher.dispatch(events) == 2
        assert dispatcher.dispatch(events) == 0
        assert monitor.process(parse_fixture("forum_update.html")) == []

        deliveries = connection.execute("SELECT COUNT(*) FROM notification_deliveries").fetchone()[
            0
        ]
        event_count = connection.execute("SELECT COUNT(*) FROM notification_events").fetchone()[0]

    assert deliveries == 2
    assert event_count == 2
    rendered = output.getvalue()
    assert "Kaynak:" in rendered
    assert "Öncelik:" in rendered
    assert "Eşleşme nedeni:" in rendered
    assert "tekrar stokta" in rendered.casefold()


def test_new_sticky_ad_is_not_notified(tmp_path: Path, app_config) -> None:
    database = Database(tmp_path / "sticky.sqlite3")
    database.migrate()
    with database.session() as connection:
        monitor = ForumMonitorService(DealRepository(connection), app_config.forum)
        monitor.process(parse_fixture("forum_baseline.html"))
        events = monitor.process(parse_fixture("forum_update.html"))
    assert "901" not in {event.payload["topic_id"] for event in events}


def test_failed_delivery_can_be_retried(tmp_path: Path, app_config) -> None:
    database = Database(tmp_path / "retry.sqlite3")
    database.migrate()

    class FlakyNotifier:
        channel = "test"

        def __init__(self) -> None:
            self.calls = 0

        def send(self, _event) -> None:
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("temporary failure")

    notifier = FlakyNotifier()
    with database.session() as connection:
        repository = DealRepository(connection)
        monitor = ForumMonitorService(repository, app_config.forum)
        monitor.process(parse_fixture("forum_baseline.html"))
        event = monitor.process(parse_fixture("forum_update.html"))[0]
        dispatcher = NotificationDispatcher(lambda: repository, [notifier])
        assert dispatcher.dispatch([event]) == 0
        assert dispatcher.dispatch([event]) == 1
        assert dispatcher.dispatch([event]) == 0
    assert notifier.calls == 2
