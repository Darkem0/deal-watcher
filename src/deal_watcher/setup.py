"""Small interactive setup; credentials stay in the user's local .env."""

from __future__ import annotations

import argparse
import getpass
import os
import tempfile
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


def complete_env(path: Path, token: str, chat_id: str) -> None:
    """Fill missing credentials; preserve all configured values and other settings."""
    if not path.exists():
        create_env(path, token, chat_id)
        return
    if path.is_symlink():
        raise ValueError(".env bir bağlantı; dosyayı kendiniz düzenleyin")
    original = path.read_bytes()
    lines = original.decode("utf-8").splitlines()
    missing = {"TELEGRAM_BOT_TOKEN": token, "TELEGRAM_CHAT_ID": chat_id}
    if any(c in token + chat_id for c in "\r\n"):
        raise ValueError("Değerler tek satır olmalıdır")
    for index, line in enumerate(lines):
        if "=" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key in missing:
            new_value = missing.pop(key)
            if not value.strip().strip("\"'"):
                lines[index] = f"{key}={new_value}"
    lines.extend(f"{key}={value}" for key, value in missing.items())
    content = "\n".join(lines) + "\n"
    if content.encode() == original:
        return
    # A replaced Unix file retains the temporary file's owner-only permissions.
    fd, temporary = tempfile.mkstemp(prefix=".env-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
        if path.read_bytes() != original:
            raise ValueError(".env başka bir süreçte değişti; tekrar deneyin")
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def guided_setup(path: Path) -> bool:
    _load_environment(None)
    token = os.getenv("DEAL_WATCHER_TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("DEAL_WATCHER_TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
    if token and chat_id:
        print("Telegram bağlantı bilgileri hazır; mevcut ayarlar korundu.")
        return True
    print("\nİlk kurulum: Telegram'ı telefonunuzda açın.")
    print("1. https://t.me/BotFather adresinde /newbot ile bot oluşturun.")
    print("2. Verilen token'ı buraya yapıştırın; yazarken görünmemesi normaldir.")
    if not token:
        token = getpass.getpass("Bot token: ").strip()
    if not token or any(c in token for c in "\r\n"):
        print("Token boş veya geçersiz; bilgi kaydedilmedi.")
        return False
    if not chat_id:
        chat_id = input("Chat ID biliyorsanız yazın; otomatik bulmak için Enter: ").strip()
    while not chat_id:
        print("3. Kendi botunuzun sohbetini açın ve /start mesajı gönderin.")
        input("Hazırsanız Enter: Telegram'dan sohbet ID'niz okunacak. ")
        try:
            chats = find_chats(token)
        except RuntimeError as exc:
            print(str(exc))
            return False
        choices = list(chats)
        if not choices:
            print("Sohbet bulunamadı. Botunuza /start gönderdiğinizden emin olun.")
            if input("Tekrar denensin mi? [e/H]: ").strip().lower() != "e":
                return False
        elif len(choices) == 1:
            chat_id = choices[0]
            print(f"Sohbet bulundu ({chats[chat_id]}).")
        else:
            for index, value in enumerate(choices, 1):
                print(f"{index}. {chats[value]} — Chat ID: {value}")
            selected = input("Bildirimlerin gideceği sohbetin sıra numarası: ").strip()
            if not selected.isdigit() or not 1 <= int(selected) <= len(choices):
                print("Seçim geçersiz; tekrar başlatın.")
                return False
            chat_id = choices[int(selected) - 1]
    if not chat_id.lstrip("-").isdigit():
        print("Chat ID sayısal olmalıdır; kurulum tamamlanmadı.")
        return False
    complete_env(path, token, chat_id)
    os.environ["TELEGRAM_BOT_TOKEN"] = token
    os.environ["TELEGRAM_CHAT_ID"] = chat_id
    print("Bağlantı bilgileri bu bilgisayarda .env dosyasına kaydedildi.")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deal Watcher yerel kurulum yardımcısı")
    parser.add_argument("--check", action="store_true", help="Yalnız offline kontrol yap")
    parser.add_argument("--guided", action="store_true", help="Adım adım Telegram kurulumu")
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
    if args.guided:
        if not guided_setup(env):
            return 2
    elif not env.exists() and not args.check:
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
