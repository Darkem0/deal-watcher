from __future__ import annotations

import platform
import signal
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from threading import Event
from types import FrameType
from typing import Self
from uuid import uuid4
from zoneinfo import ZoneInfo


def utc_now() -> datetime:
    return datetime.now(UTC)


def configure_console_utf8() -> None:
    """Best-effort Windows console setup; older redirected streams may lack reconfigure."""
    if platform.system() != "Windows":
        return
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


def to_display_timezone(value: datetime, timezone_name: str = "Europe/Istanbul") -> datetime:
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return value.astimezone(ZoneInfo(timezone_name))


class InstanceLockError(RuntimeError):
    pass


@dataclass(slots=True)
class RuntimeNotificationState:
    """Process-local lifecycle notification guards; no heartbeat state is persisted."""

    process_id: str = field(default_factory=lambda: uuid4().hex)
    runtime_started_sent: bool = False
    first_successful_scan_sent: bool = False


class InstanceLock:
    """One-host advisory lock; shared-database event keys remain the cross-host guard."""

    def __init__(self, path: Path):
        self.path = path
        self._file = None

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_file = self.path.open("a+b")
        try:
            lock_file.seek(0, 2)
            if lock_file.tell() == 0:
                lock_file.write(b"0")
                lock_file.flush()
            lock_file.seek(0)
            if platform.system() == "Windows":
                import msvcrt

                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError) as exc:
            lock_file.close()
            raise InstanceLockError(f"another instance holds {self.path}") from exc
        self._file = lock_file

    def release(self) -> None:
        if self._file is None:
            return
        self._file.seek(0)
        if platform.system() == "Windows":
            import msvcrt

            msvcrt.locking(self._file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(self._file.fileno(), fcntl.LOCK_UN)
        self._file.close()
        self._file = None

    def __enter__(self) -> Self:
        self.acquire()
        return self

    def __exit__(self, *_args: object) -> None:
        self.release()


class ShutdownController:
    def __init__(self) -> None:
        self.requested = Event()

    def install(self) -> None:
        signals = [signal.SIGINT, signal.SIGTERM]
        if hasattr(signal, "SIGBREAK"):
            signals.append(signal.SIGBREAK)
        for shutdown_signal in signals:
            signal.signal(shutdown_signal, self._handle)

    def _handle(self, _signum: int, _frame: FrameType | None) -> None:
        self.requested.set()
