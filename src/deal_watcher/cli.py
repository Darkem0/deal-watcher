from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx

from deal_watcher.http_client import ControlledHttpClient, HttpClientError
from deal_watcher.logging_setup import configure_logging, redact_secrets
from deal_watcher.models.config import ConfigLoadError, load_config
from deal_watcher.models.domain import NotificationEvent, NotificationPriority, Source
from deal_watcher.notifiers.base import (
    DryRunNotifier,
    NotificationDispatcher,
    NotificationDispatchResult,
)
from deal_watcher.runtime import (
    RuntimeNotificationState,
    configure_console_utf8,
    to_display_timezone,
)
from deal_watcher.services.forum_monitor import ForumMonitorService
from deal_watcher.services.notification_conversion import price_event_to_notification
from deal_watcher.services.price_history import PriceHistoryService
from deal_watcher.sources.akakce_browser import fetch_browser_html
from deal_watcher.sources.akakce_category import AkakceCategoryParser
from deal_watcher.sources.akakce_common import AkakceOffer, ParserChangedError
from deal_watcher.sources.akakce_product import AkakceProductParser
from deal_watcher.sources.forum import DonanimArsiviForumParser
from deal_watcher.storage.database import Database
from deal_watcher.storage.repository import DealRepository


@dataclass(frozen=True, slots=True)
class ForumScanSummary:
    topics_fetched: int
    new_topics: int
    updated_topics: int
    baseline_topics: int
    events: tuple[NotificationEvent, ...]
    database_updated: bool = True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deal-watcher")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate-config")
    validate.add_argument("--config-dir", type=Path, default=Path("config"))
    scan = sub.add_parser("forum-scan", help="process an offline forum fixture")
    scan.add_argument("--fixture", type=Path, required=True)
    scan.add_argument("--config-dir", type=Path, default=Path("config"))
    scan.add_argument("--database", type=Path)
    once = sub.add_parser("once", help="run selected sources once")
    once.add_argument("--source", choices=("all", "forum", "akakce"), default="all")
    once.add_argument("--dry-run", action="store_true")
    once.add_argument("--fixture-dir", type=Path)
    once.add_argument("--forum-fixture", type=Path)
    once.add_argument("--database", type=Path)
    once.add_argument("--config-dir", type=Path, default=Path("config"))
    run = sub.add_parser("run", help="run the scheduler loop")
    run.add_argument("--max-iterations", type=int)
    run.add_argument("--config-dir", type=Path, default=Path("config"))
    run.add_argument("--database", type=Path)
    test_notification = sub.add_parser("test-notification")
    test_notification.add_argument("--dry-run", action="store_true", default=True)
    test_notification.add_argument("--send", action="store_true")
    test_notification.add_argument("--config-dir", type=Path, default=Path("config"))
    backup = sub.add_parser("backup-db")
    backup.add_argument("--database", type=Path)
    backup.add_argument("--destination", type=Path)
    backup.add_argument("--config-dir", type=Path, default=Path("config"))
    for command in (validate, scan, once, run, test_notification, backup):
        command.add_argument("--env-file", type=Path)
    return parser


def _load_env_file(path: Path) -> None:
    """Load simple dotenv syntax without ever printing its content or overwriting process env."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip("\"'")


def _load_environment(env_file: Path | None) -> None:
    _load_env_file(env_file) if env_file else None
    _load_env_file(Path(".env"))


def _load(args):
    try:
        return load_config(args.config_dir)
    except ConfigLoadError as exc:
        print(str(exc), file=sys.stderr)
        return None


def _database(config, explicit: Path | None) -> Database:
    return Database(
        explicit or os.getenv("DEAL_WATCHER_DATABASE_PATH") or config.settings.storage.database_path
    )


def _build_notifiers(config, dry_run: bool, channels: tuple[str, ...] | None = None):
    if dry_run:
        return [DryRunNotifier(sys.stdout)]
    from deal_watcher.notifiers.platform import WindowsToastNotifier
    from deal_watcher.notifiers.telegram import TelegramNotifier

    selected = set(channels or config.settings.notifications.channels)
    notifiers = []
    if "telegram" in selected:
        token, chat_id = (
            os.getenv("DEAL_WATCHER_TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN"),
            os.getenv("DEAL_WATCHER_TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID"),
        )
        if not token or not chat_id:
            raise RuntimeError("Telegram secrets are missing; use --dry-run or configure .env")
        notifiers.append(TelegramNotifier(token, chat_id, config.settings.network.timeout_seconds))
    if "windows_toast" in selected:
        notifiers.append(WindowsToastNotifier())
    return notifiers


def _dispatch_with_stats(
    config, database, events, dry_run: bool, channels: tuple[str, ...] | None = None
) -> tuple[NotificationDispatchResult, list[object]]:
    notifiers = _build_notifiers(config, dry_run, channels)
    with database.session() as connection:
        repository = DealRepository(connection)
        result = NotificationDispatcher(lambda: repository, notifiers).dispatch_with_stats(events)
    return result, notifiers


def _dispatch(config, database, events, dry_run: bool) -> int:
    return _dispatch_with_stats(config, database, events, dry_run)[0].delivered


def _persist_and_dispatch_lifecycle_event(config, database, event: NotificationEvent) -> None:
    """Persist and deliver a lifecycle event without affecting source execution."""
    logger = logging.getLogger("deal_watcher.runtime")
    try:
        with database.session() as connection:
            repository = DealRepository(connection)
            source_id = repository.ensure_source(
                Source(
                    "donanim_arsivi_sicak_firsatlar",
                    config.forum.source.name,
                    str(config.forum.source.url),
                    "forum_category",
                )
            )
            saved = repository.add_event(source_id, event)
        if saved is not None:
            _dispatch(config, database, [saved], False)
    except Exception as exc:  # noqa: BLE001 - lifecycle notifications are best effort
        logger.warning("Lifecycle notification failed: %s", redact_secrets(str(exc)))


def _runtime_started_event(config, state: RuntimeNotificationState) -> NotificationEvent:
    return NotificationEvent(
        f"runtime_started:{state.process_id}",
        "donanim_arsivi_sicak_firsatlar",
        "runtime_started",
        "Deal Watcher aktif.",
        str(config.forum.source.url),
        NotificationPriority.NORMAL,
        "runtime lifecycle",
        payload={
            "message": "Deal Watcher aktif.\n\n"
            "Kaynak: Donanım Arşivi Sıcak Fırsatlar\n"
            "Durum: İzleme süreci başlatıldı"
        },
    )


def _first_successful_scan_event(
    config, state: RuntimeNotificationState, summary: ForumScanSummary
) -> NotificationEvent:
    local_time = to_display_timezone(datetime.now(UTC), config.settings.application.timezone)
    return NotificationEvent(
        f"first_successful_scan:{state.process_id}",
        "donanim_arsivi_sicak_firsatlar",
        "first_successful_scan",
        "Sistem çalışıyor.",
        str(config.forum.source.url),
        NotificationPriority.NORMAL,
        "first successful forum scan",
        payload={
            "message": "Sistem çalışıyor.\n\n"
            "Son tarama başarılı.\n"
            f"Çekilen konu: {summary.topics_fetched}\n"
            f"Yeni konu: {summary.new_topics}\n"
            f"Tarama zamanı: {local_time.strftime('%d.%m.%Y %H:%M:%S')}"
        },
    )


def _send_runtime_started(config, database, state: RuntimeNotificationState) -> None:
    if state.runtime_started_sent or not config.settings.notifications.send_runtime_started:
        return
    state.runtime_started_sent = True
    _persist_and_dispatch_lifecycle_event(config, database, _runtime_started_event(config, state))


def _send_first_successful_scan(
    config, database, state: RuntimeNotificationState, summary: ForumScanSummary
) -> None:
    if (
        state.first_successful_scan_sent
        or not config.settings.notifications.send_first_successful_scan
    ):
        return
    state.first_successful_scan_sent = True
    _persist_and_dispatch_lifecycle_event(
        config, database, _first_successful_scan_event(config, state, summary)
    )


def _process_forum_topics(config, database, topics) -> ForumScanSummary:
    with database.session() as connection:
        repository = DealRepository(connection)
        source_id = repository.ensure_source(
            Source(
                "donanim_arsivi_sicak_firsatlar",
                config.forum.source.name,
                str(config.forum.source.url),
                "forum_category",
            )
        )
        baseline_exists = repository.baseline_exists(source_id)
        new_topics = sum(
            repository.get_topic(source_id, topic.topic_id) is None for topic in topics
        )
        updated_topics = len(topics) - new_topics
        events = ForumMonitorService(repository, config.forum).process(topics)
    return ForumScanSummary(
        topics_fetched=len(topics),
        new_topics=new_topics if baseline_exists else 0,
        updated_topics=updated_topics if baseline_exists else 0,
        baseline_topics=len(topics) if not baseline_exists else 0,
        events=tuple(events),
    )


def _forum_once(config, database, fixture: Path) -> ForumScanSummary:
    result = DonanimArsiviForumParser().parse(
        fixture.read_text(encoding="utf-8"), str(config.forum.source.url)
    )
    if result.errors:
        raise ParserChangedError("; ".join(result.errors))
    return _process_forum_topics(config, database, result.topics)


def _forum_live(config, database) -> ForumScanSummary:
    client = ControlledHttpClient(
        timeout=httpx.Timeout(
            config.settings.network.timeout_seconds,
            connect=config.settings.network.connect_timeout_seconds,
            read=config.settings.network.read_timeout_seconds,
            write=config.settings.network.write_timeout_seconds,
            pool=config.settings.network.pool_timeout_seconds,
        ),
        max_retries=config.settings.network.max_retries,
        backoff_seconds=tuple(config.settings.network.backoff_seconds),
        min_interval_seconds=config.settings.network.min_request_interval_seconds,
        max_response_bytes=config.settings.network.max_response_bytes,
        user_agent=config.settings.network.user_agent,
    )
    started = datetime.now(UTC)
    try:
        response = client.get_html(str(config.forum.source.url))
        result = DonanimArsiviForumParser().parse(
            response.content.decode("utf-8", errors="replace"), str(config.forum.source.url)
        )
        if result.errors:
            raise ParserChangedError("; ".join(result.errors))
        summary = _process_forum_topics(config, database, result.topics)
        with database.session() as connection:
            repository = DealRepository(connection)
            source_id = repository.ensure_source(
                Source(
                    "donanim_arsivi_sicak_firsatlar",
                    config.forum.source.name,
                    str(config.forum.source.url),
                    "forum_category",
                )
            )
            repository.record_fetch_run(
                source_id=source_id,
                started_at=started.isoformat(),
                completed_at=datetime.now(UTC).isoformat(),
                status="success",
                status_code=response.status_code,
                elapsed_ms=response.elapsed_ms,
                attempt_count=response.attempts,
                items_discovered=len(result.topics),
                events_created=len(summary.events),
            )
            return summary
    except (HttpClientError, ParserChangedError, UnicodeError) as exc:
        with database.session() as connection:
            repository = DealRepository(connection)
            source_id = repository.ensure_source(
                Source(
                    "donanim_arsivi_sicak_firsatlar",
                    config.forum.source.name,
                    str(config.forum.source.url),
                    "forum_category",
                )
            )
            repository.record_fetch_run(
                source_id=source_id,
                started_at=started.isoformat(),
                completed_at=datetime.now(UTC).isoformat(),
                status="failure",
                status_code=getattr(exc, "status_code", None),
                error_type=getattr(exc, "error_type", type(exc).__name__),
                masked_error_message=str(exc),
            )
        raise
    finally:
        client.close()


def _category_as_offer(item, target_id: str) -> AkakceOffer:
    return AkakceOffer(
        item.source_product_id,
        item.product_url,
        item.product_name,
        item.normalized_model,
        item.normalized_brand,
        item.normalized_model,
        None,
        item.seller,
        None,
        item.listed_price,
        item.shipping_price,
        item.total_price,
        "TRY",
        item.stock_status,
        item.installment_count,
        None,
        item.scraped_at,
        item.raw_hash,
    )


def _akakce_once(config, database, fixture_dir: Path | None) -> list[dict[str, object]]:
    client = ControlledHttpClient(
        timeout=httpx.Timeout(
            config.settings.network.timeout_seconds,
            connect=config.settings.network.connect_timeout_seconds,
            read=config.settings.network.read_timeout_seconds,
            write=config.settings.network.write_timeout_seconds,
            pool=config.settings.network.pool_timeout_seconds,
        ),
        max_retries=config.settings.network.max_retries,
        backoff_seconds=tuple(config.settings.network.backoff_seconds),
        min_interval_seconds=config.settings.network.min_request_interval_seconds,
        max_response_bytes=config.settings.network.max_response_bytes,
        user_agent=config.settings.network.user_agent,
    )
    results: list[dict[str, object]] = []
    try:
        for target in config.products.products:
            started = datetime.now(UTC)
            try:
                if fixture_dir:
                    filename = f"{target.id}.html"
                    html = (fixture_dir / filename).read_text(encoding="utf-8")
                    attempts, status_code, elapsed = 0, None, 0
                else:
                    if config.settings.akakce.fetch_mode == "browser":
                        html = fetch_browser_html(
                            str(target.url), headless=config.settings.akakce.browser_headless
                        )
                        attempts, status_code, elapsed = 1, None, 0
                    else:
                        try:
                            response = client.get_html(str(target.url))
                            html, attempts, status_code, elapsed = (
                                response.content.decode("utf-8", errors="replace"),
                                response.attempts,
                                response.status_code,
                                response.elapsed_ms,
                            )
                        except HttpClientError as exc:
                            if not (
                                config.settings.akakce.fetch_mode == "auto"
                                and config.settings.akakce.browser_fallback_enabled
                                and exc.error_type in {"access_denied", "captcha_or_challenge"}
                            ):
                                raise
                            html = fetch_browser_html(
                                str(target.url), headless=config.settings.akakce.browser_headless
                            )
                            attempts, status_code, elapsed = 2, exc.status_code, 0
                if target.source_type == "category_page":
                    category_items = AkakceCategoryParser().parse(html, str(target.url))
                    offers = tuple(_category_as_offer(item, target.id) for item in category_items)
                else:
                    category_items = ()
                    offers = AkakceProductParser().parse(
                        html, str(target.url), target.id, target.name
                    )
                with database.session() as connection:
                    history = PriceHistoryService(connection)
                    events = [
                        event for offer in offers for event in history.observe(target.id, offer)
                    ]
                    if category_items:
                        events.extend(history.observe_category(target.id, category_items))
                    source_id = DealRepository(connection).ensure_source(
                        Source(target.source, target.source, str(target.url), target.source_type)
                    )
                    DealRepository(connection).record_fetch_run(
                        source_id=source_id,
                        started_at=started.isoformat(),
                        completed_at=datetime.now(UTC).isoformat(),
                        status="success",
                        status_code=status_code,
                        elapsed_ms=elapsed,
                        attempt_count=attempts,
                        items_discovered=len(offers),
                        events_created=len(events),
                    )
                results.append(
                    {
                        "target": target.id,
                        "target_name": target.name,
                        "target_url": str(target.url),
                        "status": "success",
                        "items": len(offers),
                        "events": events,
                    }
                )
            except (OSError, ParserChangedError, HttpClientError, UnicodeError) as exc:
                with database.session() as connection:
                    source_id = DealRepository(connection).ensure_source(
                        Source(target.source, target.source, str(target.url), target.source_type)
                    )
                    DealRepository(connection).record_fetch_run(
                        source_id=source_id,
                        started_at=started.isoformat(),
                        completed_at=datetime.now(UTC).isoformat(),
                        status="failure",
                        error_type=getattr(exc, "error_type", type(exc).__name__),
                        masked_error_message=str(exc),
                        items_discovered=0,
                    )
                results.append({"target": target.id, "status": "failure", "error": str(exc)})
    finally:
        client.close()
    return results


def _akakce_notifications(database, results: list[dict[str, object]]) -> list[NotificationEvent]:
    persisted: list[NotificationEvent] = []
    with database.session() as connection:
        repository = DealRepository(connection)
        source_id = repository.ensure_source(
            Source("akakce", "Akakçe", "https://www.akakce.com", "product")
        )
        for result in results:
            for price_event in result.get("events", []):
                event = price_event_to_notification(
                    price_event, title=str(result["target_name"]), url=str(result["target_url"])
                )
                if event:
                    stored = repository.add_event(source_id, event)
                    if stored:
                        persisted.append(stored)
    return persisted


def _print_price_events(results: list[dict[str, object]]) -> None:
    for result in results:
        for event in result.get("events", []):
            print(
                json.dumps(
                    {
                        "target": result["target"],
                        "event_type": event.event_type,
                        "seller": event.seller,
                        "new_value": event.new_value,
                        "priority": event.priority.value,
                    },
                    ensure_ascii=False,
                )
            )


def _print_forum_summary(
    config, database, summary: ForumScanSummary, dispatch: NotificationDispatchResult, dry_run: bool
) -> None:
    print("Forum taraması tamamlandı.")
    print(f"Kaynak: {config.forum.source.name}")
    print(f"Çekilen konu: {summary.topics_fetched}")
    print(f"Yeni konu: {summary.new_topics}")
    print(f"Güncellenen konu: {summary.updated_topics}")
    print(f"Baseline konu: {summary.baseline_topics}")
    print(f"Üretilen bildirim: {len(summary.events)}")
    print(f"Gönderilen bildirim: {dispatch.delivered}")
    print(f"Başarısız bildirim: {dispatch.failed}")
    print(f"Dry-run: {'evet' if dry_run else 'hayır'}")
    print(
        "Veritabanı güncellendi: evet"
        if summary.database_updated
        else "Veritabanı güncellendi: hayır"
    )
    print(f"Veritabanı: {database.path}")
    print("Sonuç: success")


def _masked_chat_id(chat_id: str) -> str:
    return f"{'*' * max(0, len(chat_id) - 4)}{chat_id[-4:]}"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_console_utf8()
    _load_environment(args.env_file)
    if os.getenv("DEAL_WATCHER_CONFIG_DIR") and args.config_dir == Path("config"):
        args.config_dir = Path(os.environ["DEAL_WATCHER_CONFIG_DIR"])
    config = _load(args)
    if config is None:
        return 2
    if os.getenv("DEAL_WATCHER_LOG_DIR"):
        config.settings.storage.log_directory = Path(os.environ["DEAL_WATCHER_LOG_DIR"])
    configure_logging(
        config.settings.storage.log_directory, os.getenv("DEAL_WATCHER_LOG_LEVEL", "INFO")
    )
    if args.command == "validate-config":
        print(
            f"Yapılandırma geçerli: {len(config.products.products)} ürün, {len(config.forum.categories)} forum kategorisi"
        )
        return 0
    if args.command == "test-notification":
        event = NotificationEvent(
            f"test:notification:{datetime.now(UTC).isoformat()}",
            "telegram_test",
            "test",
            "Deal Watcher bildirim testi başarılı.",
            "https://example.invalid",
            NotificationPriority.NORMAL,
            "Telegram canlı doğrulama",
        )
        if not args.send:
            print("Telegram test bildirimi önizlemesi")
            DryRunNotifier(sys.stdout).send(event)
            print("Dry-run: evet")
            return 0
    database = _database(config, getattr(args, "database", None))
    database.migrate()
    if args.command == "test-notification":
        try:
            with database.session() as connection:
                repository = DealRepository(connection)
                source_id = repository.ensure_source(
                    Source(
                        "telegram_test",
                        "Telegram canlı doğrulama",
                        "https://api.telegram.org",
                        "notification",
                    )
                )
                saved_event = repository.add_event(source_id, event)
            assert saved_event is not None
            dispatch, notifiers = _dispatch_with_stats(
                config, database, [saved_event], False, channels=("telegram",)
            )
        except RuntimeError as exc:
            if "Telegram secrets are missing" in str(exc):
                print(
                    "Telegram gönderimi yapılamadı: TELEGRAM_BOT_TOKEN veya TELEGRAM_CHAT_ID eksik.",
                    file=sys.stderr,
                )
            else:
                print("Telegram gönderimi yapılamadı: notifier başlatılamadı.", file=sys.stderr)
            return 2
        if dispatch.failed:
            print("Telegram gönderimi yapılamadı: delivery failed.", file=sys.stderr)
            return 3
        telegram = next(
            (notifier for notifier in notifiers if notifier.channel == "telegram"), None
        )
        message_id = getattr(telegram, "last_message_id", None)
        chat_id = os.getenv("DEAL_WATCHER_TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID") or ""
        print("Telegram test bildirimi gönderildi.")
        print(f"Chat: {_masked_chat_id(chat_id)}")
        print(f"Message ID: {message_id if message_id is not None else 'unknown'}")
        print("Delivery: delivered")
        return 0
    if args.command == "backup-db":
        destination = args.destination or Path(str(database.path) + ".backup")
        print(database.backup_to(destination))
        return 0
    if args.command == "forum-scan":
        try:
            summary = _forum_once(config, database, args.fixture)
            dispatch, _ = _dispatch_with_stats(config, database, summary.events, True)
            _print_forum_summary(config, database, summary, dispatch, True)
            return 0
        except (OSError, RuntimeError, ValueError, httpx.HTTPError) as exc:
            print(f"Forum taraması başarısız: {exc}", file=sys.stderr)
            return 3
    if args.command == "once":
        failures = 0
        if args.source in ("all", "forum"):
            fixture = args.forum_fixture or (
                args.fixture_dir / "forum_update.html"
                if args.fixture_dir and (args.fixture_dir / "forum_update.html").exists()
                else None
            )
            if fixture is None:
                try:
                    summary = _forum_live(config, database)
                    dispatch, _ = _dispatch_with_stats(
                        config, database, summary.events, args.dry_run
                    )
                    _print_forum_summary(config, database, summary, dispatch, args.dry_run)
                except (OSError, RuntimeError, ValueError, httpx.HTTPError) as exc:
                    status = getattr(exc, "status_code", None)
                    suffix = f" (HTTP {status})" if status else ""
                    print(f"Forum taraması başarısız{suffix}: {exc}", file=sys.stderr)
                    failures += 1
            else:
                try:
                    summary = _forum_once(config, database, fixture)
                    dispatch, _ = _dispatch_with_stats(
                        config, database, summary.events, args.dry_run
                    )
                    _print_forum_summary(config, database, summary, dispatch, args.dry_run)
                except (OSError, RuntimeError, ValueError, httpx.HTTPError) as exc:
                    status = getattr(exc, "status_code", None)
                    suffix = f" (HTTP {status})" if status else ""
                    print(f"Forum taraması başarısız{suffix}: {exc}", file=sys.stderr)
                    failures += 1
        if args.source == "akakce" and not config.settings.akakce.enabled:
            print(
                "source disabled: akakce (experimental; config.settings.akakce.enabled=true gerekli)"
            )
            return 0
        if args.source in ("all", "akakce") and config.settings.akakce.enabled:
            results = _akakce_once(config, database, args.fixture_dir)
            price_notifications = _akakce_notifications(database, results)
            _dispatch(config, database, price_notifications, args.dry_run)
            _print_price_events(results)
            failures += sum(result["status"] == "failure" for result in results)
            for result in results:
                print(
                    json.dumps(
                        {key: value for key, value in result.items() if key != "events"},
                        ensure_ascii=False,
                    )
                )
        return 1 if failures else 0
    if args.command == "run":
        from deal_watcher.scheduler import ScheduledJob, run_with_lock

        lifecycle_state = RuntimeNotificationState()

        def dispatch_forum() -> None:
            summary = _forum_live(config, database)
            try:
                _dispatch(config, database, summary.events, False)
            except Exception as exc:  # noqa: BLE001 - delivery must not fail source run
                logging.getLogger("deal_watcher.runtime").warning(
                    "Forum event notification failed: %s", redact_secrets(str(exc))
                )
            _send_first_successful_scan(config, database, lifecycle_state, summary)

        def dispatch_akakce() -> None:
            results = _akakce_once(config, database, None)
            _dispatch(config, database, _akakce_notifications(database, results), False)

        jobs = [
            ScheduledJob(
                "forum",
                config.forum.polling.first_page_minutes * 60,
                dispatch_forum,
                config.forum.polling.jitter_seconds,
            ),
        ]
        if config.settings.akakce.enabled:
            jobs.append(ScheduledJob("akakce", 15 * 60, dispatch_akakce, 45))
        run_with_lock(
            config.settings.storage.instance_lock_path,
            jobs,
            max_iterations=args.max_iterations,
            on_started=lambda: _send_runtime_started(config, database, lifecycle_state),
        )
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
