from deal_watcher import launcher
from deal_watcher.runtime import InstanceLockError


def test_incomplete_setup_does_not_start_runtime(monkeypatch) -> None:
    monkeypatch.setattr(launcher.setup, "main", lambda _: 2)

    def should_not_start(_args):
        raise AssertionError("runtime started before setup completed")

    monkeypatch.setattr(launcher.cli, "main", should_not_start)
    assert launcher.main() == 2


def test_ready_launcher_enters_existing_runtime(monkeypatch) -> None:
    monkeypatch.setattr(launcher.setup, "main", lambda _: 0)
    commands = []
    monkeypatch.setattr(launcher.cli, "main", lambda args: commands.append(args) or 0)
    assert launcher.main() == 0
    assert commands == [["run"]]


def test_duplicate_runtime_has_readable_message(monkeypatch, capsys) -> None:
    monkeypatch.setattr(launcher.setup, "main", lambda _: 0)

    def locked(_args):
        raise InstanceLockError("already held")

    monkeypatch.setattr(launcher.cli, "main", locked)
    assert launcher.main() == 2
    assert "Bot zaten" in capsys.readouterr().out
