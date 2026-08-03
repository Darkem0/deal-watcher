from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

MIGRATIONS: tuple[tuple[int, str], ...] = (
    (
        1,
        """
        CREATE TABLE sources (
            id INTEGER PRIMARY KEY,
            source_key TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            base_url TEXT NOT NULL,
            source_type TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE product_targets (
            id TEXT PRIMARY KEY,
            source_id INTEGER NOT NULL REFERENCES sources(id),
            name TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            source_type TEXT NOT NULL,
            target_price_kurus INTEGER,
            config_json TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE forum_topics (
            id INTEGER PRIMARY KEY,
            source_id INTEGER NOT NULL REFERENCES sources(id),
            topic_id TEXT NOT NULL,
            canonical_url TEXT NOT NULL,
            title TEXT NOT NULL,
            prefix_labels_json TEXT NOT NULL,
            author TEXT,
            created_at TEXT,
            last_activity_at TEXT,
            last_activity_user TEXT,
            reply_count INTEGER NOT NULL DEFAULT 0,
            view_count INTEGER NOT NULL DEFAULT 0,
            page_count INTEGER NOT NULL DEFAULT 1,
            is_locked INTEGER NOT NULL DEFAULT 0,
            is_sticky INTEGER NOT NULL DEFAULT 0,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            UNIQUE(source_id, topic_id),
            UNIQUE(source_id, canonical_url)
        );
        CREATE INDEX idx_forum_topics_activity ON forum_topics(source_id, last_activity_at);
        CREATE TABLE product_listings (
            id INTEGER PRIMARY KEY,
            target_id TEXT NOT NULL REFERENCES product_targets(id),
            canonical_url TEXT NOT NULL,
            title TEXT NOT NULL,
            seller TEXT,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            UNIQUE(target_id, canonical_url)
        );
        CREATE TABLE price_observations (
            id INTEGER PRIMARY KEY,
            listing_id INTEGER NOT NULL REFERENCES product_listings(id),
            observed_at TEXT NOT NULL,
            price_kurus INTEGER NOT NULL,
            shipping_kurus INTEGER,
            total_kurus INTEGER,
            is_anomaly INTEGER NOT NULL DEFAULT 0,
            UNIQUE(listing_id, observed_at)
        );
        CREATE TABLE stock_observations (
            id INTEGER PRIMARY KEY,
            listing_id INTEGER NOT NULL REFERENCES product_listings(id),
            observed_at TEXT NOT NULL,
            in_stock INTEGER NOT NULL,
            UNIQUE(listing_id, observed_at)
        );
        CREATE TABLE source_fetch_runs (
            id INTEGER PRIMARY KEY,
            source_id INTEGER NOT NULL REFERENCES sources(id),
            started_at TEXT NOT NULL,
            completed_at TEXT,
            succeeded INTEGER NOT NULL,
            status_code INTEGER,
            item_count INTEGER NOT NULL DEFAULT 0,
            error TEXT
        );
        CREATE TABLE baseline_states (
            source_id INTEGER PRIMARY KEY REFERENCES sources(id),
            established_at TEXT NOT NULL,
            last_success_at TEXT NOT NULL,
            item_count INTEGER NOT NULL
        );
        CREATE TABLE notification_events (
            id INTEGER PRIMARY KEY,
            source_id INTEGER NOT NULL REFERENCES sources(id),
            event_key TEXT NOT NULL UNIQUE,
            event_type TEXT NOT NULL,
            priority TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            price_kurus INTEGER,
            match_reason TEXT NOT NULL,
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        );
        CREATE INDEX idx_notification_events_created ON notification_events(created_at);
        CREATE TABLE notification_deliveries (
            id INTEGER PRIMARY KEY,
            event_id INTEGER NOT NULL REFERENCES notification_events(id),
            channel TEXT NOT NULL,
            delivered_at TEXT NOT NULL,
            status TEXT NOT NULL,
            error TEXT,
            UNIQUE(event_id, channel)
        );
        CREATE TABLE parser_errors (
            id INTEGER PRIMARY KEY,
            source_id INTEGER REFERENCES sources(id),
            fetch_run_id INTEGER REFERENCES source_fetch_runs(id),
            occurred_at TEXT NOT NULL,
            error_type TEXT NOT NULL,
            message TEXT NOT NULL,
            context_json TEXT NOT NULL DEFAULT '{}'
        );
        """,
    ),
    (
        2,
        """
        ALTER TABLE forum_topics ADD COLUMN detail_json TEXT NOT NULL DEFAULT '{}';
        """,
    ),
    (
        3,
        """
        ALTER TABLE source_fetch_runs ADD COLUMN status TEXT NOT NULL DEFAULT 'unknown';
        ALTER TABLE source_fetch_runs ADD COLUMN elapsed_ms INTEGER;
        ALTER TABLE source_fetch_runs ADD COLUMN attempt_count INTEGER NOT NULL DEFAULT 0;
        ALTER TABLE source_fetch_runs ADD COLUMN error_type TEXT;
        ALTER TABLE source_fetch_runs ADD COLUMN masked_error_message TEXT;
        ALTER TABLE source_fetch_runs ADD COLUMN events_created INTEGER NOT NULL DEFAULT 0;
        CREATE TABLE product_snapshots (
            id INTEGER PRIMARY KEY,
            source TEXT NOT NULL,
            source_product_id TEXT NOT NULL,
            product_config_id TEXT NOT NULL,
            normalized_model TEXT NOT NULL,
            seller TEXT,
            listed_price INTEGER,
            shipping_price INTEGER,
            total_price INTEGER,
            stock_status TEXT NOT NULL,
            captured_at TEXT NOT NULL,
            raw_hash TEXT NOT NULL
        );
        CREATE INDEX idx_product_snapshots_lookup ON product_snapshots(product_config_id, source_product_id, captured_at);
        CREATE TABLE product_states (
            product_config_id TEXT NOT NULL,
            source_product_id TEXT NOT NULL,
            normalized_model TEXT NOT NULL,
            seller TEXT,
            first_seen_at TEXT NOT NULL,
            last_seen_at TEXT NOT NULL,
            baseline_price INTEGER,
            previous_price INTEGER,
            current_price INTEGER,
            all_time_low INTEGER,
            previous_stock_status TEXT,
            current_stock_status TEXT NOT NULL,
            PRIMARY KEY(product_config_id, source_product_id, seller)
        );
        CREATE TABLE price_events (
            id INTEGER PRIMARY KEY,
            event_type TEXT NOT NULL,
            product_config_id TEXT NOT NULL,
            source_product_id TEXT NOT NULL,
            seller TEXT,
            old_value TEXT,
            new_value TEXT,
            percentage_change REAL,
            priority TEXT NOT NULL,
            created_at TEXT NOT NULL,
            dedup_key TEXT NOT NULL UNIQUE
        );
        """,
    ),
    (
        4,
        """
        CREATE TABLE category_states (
            product_config_id TEXT PRIMARY KEY,
            model_keys_json TEXT NOT NULL,
            cheapest_model TEXT,
            cheapest_price INTEGER,
            updated_at TEXT NOT NULL
        );
        """,
    ),
)


class Database:
    def __init__(self, path: Path | str):
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def session(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def migrate(self) -> None:
        with self.session() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations ("
                "version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
            )
            applied = {
                row[0] for row in connection.execute("SELECT version FROM schema_migrations")
            }
            for version, sql in MIGRATIONS:
                if version in applied:
                    continue
                connection.executescript(sql)
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) "
                    "VALUES (?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))",
                    (version,),
                )

    def backup_to(self, destination: Path | str) -> Path:
        """Copy a consistent SQLite snapshot using SQLite's backup API."""
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.resolve() == self.path.resolve():
            raise ValueError("backup destination must differ from database path")
        source = self.connect()
        try:
            backup = sqlite3.connect(target)
            try:
                source.backup(backup)
            finally:
                backup.close()
        finally:
            source.close()
        return target
