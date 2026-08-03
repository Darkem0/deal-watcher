from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from threading import Event, Lock

from deal_watcher.runtime import InstanceLock, ShutdownController


@dataclass(slots=True)
class ScheduledJob:
    name: str
    interval_seconds: float
    callback: Callable[[], None]
    jitter_seconds: float = 0.0
    next_run: float = 0.0
    running: bool = False
    failures: int = 0


class Scheduler:
    def __init__(
        self,
        jobs: list[ScheduledJob],
        *,
        sleeper=time.sleep,
        clock=time.monotonic,
        stop: Event | None = None,
    ):
        self.jobs = jobs
        self._sleep = sleeper
        self._clock = clock
        self.stop = stop or Event()
        self._lock = Lock()

    def run(self, *, max_iterations: int | None = None) -> None:
        iterations = 0
        now = self._clock()
        for job in self.jobs:
            job.next_run = now
        while not self.stop.is_set() and (max_iterations is None or iterations < max_iterations):
            now = self._clock()
            due = [job for job in self.jobs if job.next_run <= now and not job.running]
            if not due:
                self._sleep(min(1.0, max(0.0, min(job.next_run for job in self.jobs) - now)))
                continue
            for job in due:
                with self._lock:
                    if job.running:
                        continue
                    job.running = True
                try:
                    job.callback()
                    job.failures = 0
                    delay = job.interval_seconds
                except (OSError, RuntimeError, ValueError):
                    job.failures += 1
                    delay = min(job.interval_seconds * (2 ** min(job.failures, 4)), 3600)
                finally:
                    job.running = False
                jitter = random.uniform(0, job.jitter_seconds) if job.jitter_seconds else 0
                job.next_run = self._clock() + delay + jitter
                iterations += 1


def run_with_lock(
    lock_path,
    jobs: list[ScheduledJob],
    *,
    max_iterations: int | None = None,
    on_started: Callable[[], None] | None = None,
) -> None:
    controller = ShutdownController()
    controller.install()
    with InstanceLock(lock_path):
        if on_started is not None:
            on_started()
        Scheduler(jobs, stop=controller.requested).run(max_iterations=max_iterations)
