"""User-facing first-run setup followed by the existing monitoring runtime."""

from __future__ import annotations

from deal_watcher import cli, setup
from deal_watcher.logging_setup import redact_secrets
from deal_watcher.runtime import InstanceLockError, configure_console_utf8


def main() -> int:
    configure_console_utf8()
    print("\n🔥 Deal Watcher — Telegram fırsat takipçisi\n")
    try:
        result = setup.main(["--guided"])
        if result:
            print("Kurulum tamamlanmadı. docs/telegram-kurulum.md rehberini kontrol edin.")
            return result
        print("Takip başlıyor. İlk tarama eski konuları kaydeder; yeni fırsatlar Telegram'a gelir.")
        print("Bu pencereyi açık tutun. Durdurmak için Ctrl+C.\n")
        return cli.main(["run"])
    except InstanceLockError:
        print("Bot zaten başka pencerede veya otomatik serviste çalışıyor. İkinci kopya açılmadı.")
        return 2
    except (KeyboardInterrupt, EOFError):
        print("\nİşlem durduruldu. Daha sonra aynı başlatıcıyı tekrar açabilirsiniz.")
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Başlatılamadı: {redact_secrets(str(exc))}")
        print("docs/izinler-windows.md, izinler-macos.md veya izinler-linux.md rehberine bakın.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
