"""Small interactive setup; credentials stay in the user's local .env."""

from __future__ import annotations

import argparse
import getpass
import os
from pathlib import Path

import httpx

from deal_watcher.cli import _load_environment
from deal_watcher.cli import main as cli_main
from deal_watcher.runtime import configure_console_utf8


def find_chats(token: str) -> dict[str, str]:
    """Read recent incoming updates without sending or consuming messages."""
    try:
        response = httpx.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=20)
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise ValueError("Telegram request failed")
        chats = {}
        for update in data.get("result", []):
            message = update.get("message") or update.get("channel_post") or {}
            chat = message.get("chat", {})
            if "id" in chat:
                chats[str(chat["id"])] = chat.get("type", "unknown")
        return chats
    except (httpx.HTTPError, ValueError, TypeError, AttributeError) as exc:
        # HTTP exception text can contain the token-bearing URL.
        raise RuntimeError("Telegram'a erişilemedi; token ve bağlantıyı kontrol edin.") from exc


def create_env(path: Path, token: str, chat_id: str) -> None:
    if not token or any(c in token + chat_id for c in "\r\n"):
        raise ValueError("Token boş olamaz; değerler tek satır olmalıdır.")
    if chat_id and not chat_id.lstrip("-").isdigit():
        raise ValueError("Chat ID sayısal olmalıdır.")
    # Exclusive creation protects an existing configuration, including custom keys.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(f"TELEGRAM_BOT_TOKEN={token}\nTELEGRAM_CHAT_ID={chat_id}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deal Watcher yerel kurulum yardımcısı")
    parser.add_argument("--check", action="store_true", help="Yalnız offline kontrol yap")
    parser.add_argument(
        "--find-chat", action="store_true", help="Telegram getUpdates ile Chat ID bul"
    )
    args = parser.parse_args(argv)
    configure_console_utf8()
    if not Path("config/settings.yaml").is_file():
        print("Önce deal-watcher proje klasörüne geçin.")
        return 2
    env = Path(".env")
    if args.find_chat:
        _load_environment(None)
        token = os.getenv("DEAL_WATCHER_TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            print("Önce kurulum yardımcısıyla token'ı .env içine kaydedin.")
            return 2
        try:
            chats = find_chats(token)
        except RuntimeError as exc:
            print(str(exc))
            return 1
        for chat_id, chat_type in chats.items():
            print(f"Chat ID: {chat_id} ({chat_type})")
        if not chats:
            print("Botunuza /start gönderin; grupta bir komut gönderip tekrar deneyin.")
        else:
            print("İstediğiniz ID'yi .env dosyasındaki TELEGRAM_CHAT_ID alanına yazın.")
        return 0
    if not env.exists() and not args.check:
        print("BotFather'dan aldığınız token yalnız bu bilgisayarda saklanır.")
        token = getpass.getpass("Telegram bot token: ").strip()
        chat_id = input("Chat ID (bilmiyorsanız boş bırakın): ").strip()
        try:
            create_env(env, token, chat_id)
        except (OSError, ValueError) as exc:
            print(f".env oluşturulamadı: {type(exc).__name__}; mevcut dosya değiştirilmedi.")
            return 2
        if not chat_id:
            print("Botunuza /start gönderip uv run deal-watcher-setup --find-chat çalıştırın.")
    elif env.exists():
        print("Mevcut .env korundu; token ve Chat ID değiştirilmedi.")
    result = cli_main(["validate-config"])
    if result:
        return result
    result = cli_main(["test-notification", "--dry-run"])
    if result:
        return result
    _load_environment(None)
    token = os.getenv("DEAL_WATCHER_TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("DEAL_WATCHER_TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Offline kontrol geçti. Telegram için .env token ve Chat ID alanlarını doldurun.")
        return 2
    print("Hazır. Kontrol: uv run deal-watcher test-notification --send")
    print("Başlat: uv run deal-watcher run  |  Durdur: Ctrl+C")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
