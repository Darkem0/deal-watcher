from datetime import UTC, datetime

import pytest

from deal_watcher.runtime import InstanceLock, InstanceLockError, to_display_timezone


def test_turkish_timezone_conversion_is_explicit() -> None:
    value = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    displayed = to_display_timezone(value)
    assert displayed.isoformat() == "2026-01-01T15:00:00+03:00"


def test_naive_datetime_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        to_display_timezone(datetime(2026, 1, 1, 12, 0))  # noqa: DTZ001


def test_instance_lock_prevents_second_local_instance(tmp_path) -> None:
    first = InstanceLock(tmp_path / "deal-watcher.lock")
    second = InstanceLock(tmp_path / "deal-watcher.lock")
    with first, pytest.raises(InstanceLockError):
        second.acquire()
    with second:
        pass
