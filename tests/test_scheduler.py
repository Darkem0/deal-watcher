from deal_watcher.scheduler import ScheduledJob, Scheduler


def test_scheduler_runs_due_job_once_without_overlap() -> None:
    calls = []
    scheduler = Scheduler(
        [ScheduledJob("one", 60, lambda: calls.append("run"))], sleeper=lambda _: None
    )
    scheduler.run(max_iterations=1)
    assert calls == ["run"]
