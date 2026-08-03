import sqlite3
from pathlib import Path

import pytest

from deal_watcher.storage.database import Database


def test_migration_is_applied_and_idempotent(tmp_path: Path) -> None:
    database = Database(tmp_path / "test.sqlite3")
    database.migrate()
    database.migrate()
    with database.session() as connection:
        versions = connection.execute("SELECT version FROM schema_migrations").fetchall()
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert [row[0] for row in versions] == [1, 2, 3, 4]
    assert {"sources", "forum_topics", "baseline_states", "notification_events"} <= tables


def test_foreign_keys_are_enabled_and_enforced(tmp_path: Path) -> None:
    database = Database(tmp_path / "test.sqlite3")
    database.migrate()
    with database.session() as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO baseline_states(source_id, established_at, last_success_at, item_count) "
                "VALUES (999, '2026-08-03T00:00:00Z', '2026-08-03T00:00:00Z', 0)"
            )
