import sqlite3

from deal_watcher import cli
from deal_watcher.notifiers.telegram import TelegramNotifier


def test_test_notification_without_send_is_dry_run_and_does_not_call_notifier(
    monkeypatch, tmp_path, capsys
) -> None:
    calls = []
    monkeypatch.setattr(cli, "_load_environment", lambda _path: None)
    monkeypatch.setenv("DEAL_WATCHER_DATABASE_PATH", str(tmp_path / "dry-run.sqlite3"))
    monkeypatch.setattr(TelegramNotifier, "send", lambda self, event: calls.append(event))

    result = cli.main(["test-notification"])

    output = capsys.readouterr()
    assert result == 0
    assert calls == []
    assert "Dry-run: evet" in output.out


def test_test_notification_send_uses_dispatcher_and_masks_chat_id(
    monkeypatch, tmp_path, capsys
) -> None:
    calls = []
    monkeypatch.setattr(cli, "_load_environment", lambda _path: None)
    monkeypatch.setenv("DEAL_WATCHER_DATABASE_PATH", str(tmp_path / "send.sqlite3"))
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token-never-print")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "6647685134")

    def fake_send(self, event) -> None:
        calls.append(event)
        self.last_message_id = 42

    monkeypatch.setattr(TelegramNotifier, "send", fake_send)

    result = cli.main(["test-notification", "--send"])

    output = capsys.readouterr()
    assert result == 0
    assert len(calls) == 1
    assert "Telegram test bildirimi gönderildi." in output.out
    assert "Chat: ******5134" in output.out
    assert "Message ID: 42" in output.out
    assert "Delivery: delivered" in output.out
    assert "test-token-never-print" not in output.out
    with sqlite3.connect(tmp_path / "send.sqlite3") as connection:
        assert connection.execute(
            "SELECT status FROM notification_deliveries WHERE channel='telegram'"
        ).fetchone() == ("delivered",)


def test_test_notification_send_requires_credentials(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.setattr(cli, "_load_environment", lambda _path: None)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.setenv("DEAL_WATCHER_DATABASE_PATH", str(tmp_path / "missing.sqlite3"))

    result = cli.main(["test-notification", "--send"])

    output = capsys.readouterr()
    assert result != 0
    assert "TELEGRAM_BOT_TOKEN veya TELEGRAM_CHAT_ID eksik" in output.err
