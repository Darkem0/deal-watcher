from __future__ import annotations

from pathlib import Path

from deal_watcher import cli, scheduler
from deal_watcher.models.config import load_config
from deal_watcher.models.domain import NotificationPriority
from deal_watcher.notifiers.base import format_event
from deal_watcher.runtime import RuntimeNotificationState

ROOT = Path(__file__).resolve().parents[1]


def _config(tmp_path):
    config = load_config(ROOT / "config")
    config.settings.storage.database_path = tmp_path / "runtime.sqlite3"
    config.settings.storage.instance_lock_path = tmp_path / "runtime.lock"
    config.forum.polling.first_page_minutes = 1
    config.forum.polling.jitter_seconds = (0, 0)
    return config


def _summary(topics_fetched: int, new_topics: int) -> cli.ForumScanSummary:
    return cli.ForumScanSummary(
        topics_fetched=topics_fetched,
        new_topics=new_topics,
        updated_topics=0,
        baseline_topics=0,
        events=(),
    )


def _run_jobs_immediately(_lock_path, jobs, *, max_iterations=None, on_started=None):
    if on_started is not None:
        on_started()
    for _ in range(max_iterations or 1):
        for job in jobs:
            try:
                job.callback()
            except (OSError, RuntimeError, ValueError):
                continue


def test_lifecycle_messages_have_exact_text_and_process_local_guards(tmp_path, monkeypatch) -> None:
    config = _config(tmp_path)
    database = cli._database(config, None)
    database.migrate()
    state = RuntimeNotificationState(process_id="test-process")
    dispatched = []
    monkeypatch.setattr(
        cli,
        "_persist_and_dispatch_lifecycle_event",
        lambda _config, _database, event: dispatched.append(event),
    )

    cli._send_runtime_started(config, database, state)
    cli._send_runtime_started(config, database, state)
    cli._send_first_successful_scan(config, database, state, _summary(15, 2))
    cli._send_first_successful_scan(config, database, state, _summary(16, 3))

    assert [event.event_type for event in dispatched] == [
        "runtime_started",
        "first_successful_scan",
    ]
    assert format_event(dispatched[0]) == (
        "Deal Watcher aktif.\n\n"
        "Kaynak: Donanım Arşivi Sıcak Fırsatlar\n"
        "Durum: İzleme süreci başlatıldı"
    )
    assert "Çekilen konu: 15" in format_event(dispatched[1])
    assert "Yeni konu: 2" in format_event(dispatched[1])
    assert "Tarama zamanı: " in format_event(dispatched[1])
    assert dispatched[0].priority is NotificationPriority.NORMAL


def test_run_sends_lifecycle_events_once_across_two_scheduler_tours(tmp_path, monkeypatch) -> None:
    config = _config(tmp_path)
    monkeypatch.setattr(cli, "load_config", lambda _directory: config)
    monkeypatch.setattr(cli, "_load_environment", lambda _env_file: None)
    monkeypatch.setattr(scheduler, "run_with_lock", _run_jobs_immediately)
    summaries = iter((_summary(15, 0), _summary(16, 1)))
    monkeypatch.setattr(cli, "_forum_live", lambda _config, _database: next(summaries))
    dispatched = []
    monkeypatch.setattr(
        cli,
        "_dispatch",
        lambda _config, _database, events, _dry_run: dispatched.extend(events),
    )

    assert (
        cli.main(
            [
                "run",
                "--max-iterations",
                "2",
                "--database",
                str(config.settings.storage.database_path),
            ]
        )
        == 0
    )

    assert [event.event_type for event in dispatched] == [
        "runtime_started",
        "first_successful_scan",
    ]
    assert sum(event.event_type == "runtime_started" for event in dispatched) == 1
    assert sum(event.event_type == "first_successful_scan" for event in dispatched) == 1


def test_first_successful_scan_waits_until_second_tour(tmp_path, monkeypatch) -> None:
    config = _config(tmp_path)
    monkeypatch.setattr(cli, "load_config", lambda _directory: config)
    monkeypatch.setattr(cli, "_load_environment", lambda _env_file: None)
    monkeypatch.setattr(scheduler, "run_with_lock", _run_jobs_immediately)
    calls = 0

    def forum(_config, _database):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("temporary forum failure")
        return _summary(12, 0)

    monkeypatch.setattr(cli, "_forum_live", forum)
    dispatched = []
    monkeypatch.setattr(
        cli,
        "_dispatch",
        lambda _config, _database, events, _dry_run: dispatched.extend(events),
    )

    assert (
        cli.main(
            [
                "run",
                "--max-iterations",
                "2",
                "--database",
                str(config.settings.storage.database_path),
            ]
        )
        == 0
    )

    assert calls == 2
    assert [event.event_type for event in dispatched] == [
        "runtime_started",
        "first_successful_scan",
    ]


def test_lifecycle_notification_errors_do_not_stop_forum_runtime(tmp_path, monkeypatch) -> None:
    config = _config(tmp_path)
    monkeypatch.setattr(cli, "load_config", lambda _directory: config)
    monkeypatch.setattr(cli, "_load_environment", lambda _env_file: None)
    monkeypatch.setattr(scheduler, "run_with_lock", _run_jobs_immediately)
    calls = 0

    def forum(_config, _database):
        nonlocal calls
        calls += 1
        return _summary(10 + calls, calls - 1)

    monkeypatch.setattr(cli, "_forum_live", forum)

    def broken_dispatch(*_args):
        raise RuntimeError("Telegram delivery failed")

    monkeypatch.setattr(cli, "_dispatch", broken_dispatch)

    assert (
        cli.main(
            [
                "run",
                "--max-iterations",
                "2",
                "--database",
                str(config.settings.storage.database_path),
            ]
        )
        == 0
    )
    assert calls == 2


def test_lifecycle_notifications_can_be_disabled_without_heartbeat_fields(
    tmp_path, monkeypatch
) -> None:
    config = _config(tmp_path)
    config.settings.notifications.send_runtime_started = False
    config.settings.notifications.send_first_successful_scan = False
    database = cli._database(config, None)
    database.migrate()
    state = RuntimeNotificationState()
    dispatched = []
    monkeypatch.setattr(
        cli,
        "_persist_and_dispatch_lifecycle_event",
        lambda _config, _database, event: dispatched.append(event),
    )

    cli._send_runtime_started(config, database, state)
    cli._send_first_successful_scan(config, database, state, _summary(1, 0))

    assert dispatched == []
    assert not hasattr(config.settings.notifications, "daily_heartbeat")
    assert not hasattr(config.settings.notifications, "hourly_heartbeat")
