# Project status

## Current release

- **Release:** `v0.1.0-alpha`
- **Primary source:** Donanım Arşivi Sıcak Fırsatlar, first listing page
- **Default notification channel:** Telegram
- **Persistence:** local SQLite
- **Windows deployment:** current-user Task Scheduler task triggered at logon
- **Akakçe:** experimental, disabled by default, not live-verified

## Verified behavior

- The first successful forum scan establishes a silent baseline.
- Later scans create events for new topics and selected state changes.
- Persistent event and delivery keys prevent duplicate channel delivery.
- `runtime_started` is emitted once per process when enabled.
- `first_successful_scan` is emitted once per process after the first successful forum scan.
- There is no daily, hourly, or per-scan heartbeat.
- Telegram errors are isolated from source execution and redacted before persistence.
- Forum polling uses the configured three-minute interval plus bounded jitter.
- Windows autostart uses an `Interactive`/`Limited` current-user task and a controlled UAC fallback.
- CI runs deterministic offline tests and Ruff checks on Windows and Ubuntu.

## Source access decision

Controlled direct automated HTTP access to Akakçe returned HTTP 403. The production scheduler therefore does not create an Akakçe job. Parser code and fixtures remain available for offline regression work. The project does not add CAPTCHA solving, proxy rotation, stealth, fingerprint spoofing, or access-control bypass.

## Known limitations

- The production forum adapter currently focuses on the first listing page.
- Forum HTML changes may require reviewed fixture and selector updates.
- `digest` is currently a priority label, not a delayed batching queue.
- Telegram and Task Scheduler require local operator configuration.
- This is an alpha release and does not promise uninterrupted availability.

## Quality gate

Every release candidate must pass:

```powershell
uv sync --locked --extra dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run deal-watcher validate-config
git diff --check
```

Live websites, Telegram credentials, and Windows Task Scheduler are not CI dependencies.

---

# Durum — Türkçe özet

Deal Watcher’ın aktif üretim kaynağı Donanım Arşivi Sıcak Fırsatlar’ın ilk liste sayfasıdır. İlk tarama sessiz baseline oluşturur; sonraki uygun olaylar Telegram’a tekilleştirilmiş biçimde gönderilir. Windows’ta mevcut kullanıcı oturum açtığında başlayan Task Scheduler kurulumu desteklenir.

Akakçe kontrollü doğrulamada HTTP 403 döndürdüğü için deneysel ve varsayılan kapalıdır. CAPTCHA veya erişim kontrolü aşma uygulanmaz. Bilinen ana sınırlamalar ilk sayfaya odaklanma, forum HTML drift riski ve `digest` için ayrı bir toplu kuyruk bulunmamasıdır.
