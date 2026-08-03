import pytest

from deal_watcher.scheduler import ScheduledJob, Scheduler, _jitter_delay


def test_scheduler_runs_due_job_once_without_overlap() -> None:
    calls = []
    scheduler = Scheduler(
        [ScheduledJob("one", 60, lambda: calls.append("run"))], sleeper=lambda _: None
    )
    scheduler.run(max_iterations=1)
    assert calls == ["run"]


def test_configured_jitter_range_is_honored(monkeypatch) -> None:
    captured: list[tuple[float, float]] = []

    def fake_uniform(low: float, high: float) -> float:
        captured.append((low, high))
        return 23.0

    monkeypatch.setattr("deal_watcher.scheduler.random.uniform", fake_uniform)

    assert _jitter_delay((10, 45)) == 23.0
    assert captured == [(10, 45)]


def test_numeric_jitter_keeps_zero_to_maximum_behavior(monkeypatch) -> None:
    captured: list[tuple[float, float]] = []

    def fake_uniform(low: float, high: float) -> float:
        captured.append((low, high))
        return 12.0

    monkeypatch.setattr("deal_watcher.scheduler.random.uniform", fake_uniform)

    assert _jitter_delay(45) == 12.0
    assert captured == [(0.0, 45)]


def test_invalid_jitter_range_is_rejected() -> None:
    with pytest.raises(ValueError, match="non-negative and ordered"):
        _jitter_delay((45, 10))
