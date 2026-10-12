import shutil
from pathlib import Path

import httpx
import pytest

from deal_watcher import setup
from deal_watcher.setup import create_env, find_chats


def test_setup_preserves_existing_credentials(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text("CUSTOM=preserved\n")
    with pytest.raises(FileExistsError):
        create_env(path, "synthetic-token", "123")
    assert path.read_text() == "CUSTOM=preserved\n"


def test_setup_rejects_environment_injection(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        create_env(tmp_path / ".env", "test\nOTHER=value", "123")
    assert not (tmp_path / ".env").exists()


def test_chat_discovery_uses_only_get_updates(monkeypatch) -> None:
    def get(url, **kwargs):
        assert url.endswith("/getUpdates")
        return httpx.Response(
            200,
            request=httpx.Request("GET", url),
            json={"ok": True, "result": [{"message": {"chat": {"id": -123, "type": "group"}}}]},
        )

    monkeypatch.setattr(httpx, "get", get)
    assert find_chats("synthetic-token") == {"-123": "group"}


def test_chat_discovery_does_not_print_token_on_network_failure(monkeypatch) -> None:
    def get(url, **kwargs):
        raise httpx.ConnectError(url)

    monkeypatch.setattr(httpx, "get", get)
    with pytest.raises(RuntimeError) as error:
        find_chats("synthetic-private-token")
    assert "synthetic-private-token" not in str(error.value)


def test_setup_check_is_offline_and_preserves_env(tmp_path, monkeypatch, capsys) -> None:
    shutil.copytree(Path(__file__).resolve().parents[1] / "config", tmp_path / "config")
    monkeypatch.chdir(tmp_path)
    token = "synthetic-local-only"
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", token)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-123")
    create_env(tmp_path / ".env", token, "-123")
    before = (tmp_path / ".env").read_bytes()

    def no_network(*args, **kwargs):
        raise AssertionError("offline setup check contacted Telegram")

    monkeypatch.setattr(httpx, "get", no_network)
    assert setup.main(["--check"]) == 0
    assert (tmp_path / ".env").read_bytes() == before
    assert token not in capsys.readouterr().out


def test_complete_env_preserves_existing_credentials_and_custom_settings(tmp_path) -> None:
    path = tmp_path / ".env"
    path.write_text("CUSTOM=keep\nTELEGRAM_BOT_TOKEN=existing-local\nTELEGRAM_CHAT_ID=\n")
    setup.complete_env(path, "different-token", "-123")
    assert path.read_text() == (
        "CUSTOM=keep\nTELEGRAM_BOT_TOKEN=existing-local\nTELEGRAM_CHAT_ID=-123\n"
    )


def test_complete_env_refuses_symlink(tmp_path) -> None:
    target = tmp_path / "private"
    target.write_text("CUSTOM=keep\n")
    link = tmp_path / ".env"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlink creation not supported by current user")
    with pytest.raises(ValueError):
        setup.complete_env(link, "synthetic", "123")
    assert target.read_text() == "CUSTOM=keep\n"


def test_guided_setup_finds_chat_without_manual_file_edit(tmp_path, monkeypatch, capsys) -> None:
    for key in (
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "DEAL_WATCHER_TELEGRAM_BOT_TOKEN",
        "DEAL_WATCHER_TELEGRAM_CHAT_ID",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(setup, "_load_environment", lambda _: None)
    monkeypatch.setattr(setup.getpass, "getpass", lambda _: "synthetic-guided-token")
    answers = iter(["", ""])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    monkeypatch.setattr(setup, "find_chats", lambda _: {"-123": "private"})
    assert setup.guided_setup(tmp_path / ".env") is True
    assert "TELEGRAM_CHAT_ID=-123" in (tmp_path / ".env").read_text()
    assert "synthetic-guided-token" not in capsys.readouterr().out


def test_guided_setup_no_chat_does_not_save_partial_credentials(tmp_path, monkeypatch) -> None:
    for key in (
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "DEAL_WATCHER_TELEGRAM_BOT_TOKEN",
        "DEAL_WATCHER_TELEGRAM_CHAT_ID",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(setup, "_load_environment", lambda _: None)
    monkeypatch.setattr(setup.getpass, "getpass", lambda _: "synthetic-guided-token")
    answers = iter(["", "", "h"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    monkeypatch.setattr(setup, "find_chats", lambda _: {})
    assert setup.guided_setup(tmp_path / ".env") is False
    assert not (tmp_path / ".env").exists()
