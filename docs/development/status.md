# Project status

## Current release

- **Release candidate:** `v0.3.0-alpha`
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
- Forum polling uses the configured five-minute interval plus 10–45 second jitter.
- Windows autostart uses an `Interactive`/`Limited` current-user task and a controlled UAC fallback.
- CI runs deterministic offline tests and Ruff checks on Windows, Ubuntu and macOS.

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

- Windows Task Scheduler idle termination is disabled (`StopOnIdleEnd=false`) and the Forum first-page polling default is five minutes.

## 2026-10-12 portable release preparation

- Production Mac source was compared with public main 831a006; application code matches after newline normalization.
- Personal runtime state and credentials are excluded. Existing Windows windowless startup is preserved.
- Shared setup, Linux user service and repaired macOS launchd entry point are implemented.
- Forum jitter is taken from YAML. Core baseline, storage and notification behavior are preserved.
- Ubuntu local offline tests: 76 passed; Ruff and package build passed.
- GitHub CI passed on macOS, Ubuntu and Windows for code commit 557f2ed: https://github.com/Darkem0/deal-watcher/actions/runs/38235657335.
- Published source contains no production token, Chat ID, SQLite or logs. A matching legacy test Chat ID was replaced; existing public Git history was retained.
- No real Telegram message or live forum access was performed for this release preparation.
- Native autostart/live Telegram verification remains a per-user deployment check, separate from offline CI.

## 2026-10-12 project introduction and resource documentation

- Added purpose, implemented features, usage and Telegram integration before installation steps.
- Documented a Linux-only offline fixture scan plus scheduler idle probe: 44.09 MiB peak RSS, 0.30 CPU seconds over 12.01 seconds. No live network or Telegram messages.
- Clarified that these are not production averages, hardware minimums or Windows/macOS measurements.

## 2026-10-12 beginner-facing package and README redesign

- Administrative and duplicate root Markdown files moved under docs/development, docs/reports and .github; README, AGENTS and LICENSE remain at root.
- Three platform ZIPs include the appropriate visible start file, shared bootstrap and guided Telegram setup.
- Guided setup discovers Chat ID after the user sends /start and fills only missing .env fields; existing settings are preserved.
- README uses repository SVG graphics, prominent downloads and OS-specific commands. Telegram/permissions guides are separate.
- Owner reports prior Windows/macOS/Linux use near 1% CPU and stable RAM; documentation labels this as owner observation, distinct from the Linux-only offline measurement.
- No live monitoring or Telegram delivery has been started on this Linux workstation. Service remains off; packaging work is independent of the erased/disconnected Mac.
- New ZIP launcher smoke tests run offline on all CI platforms, including a project folder with spaces.

- Local verification: 83 offline tests, Ruff lint/format, package build, Markdown link checks and Linux ZIP launcher smoke test passed. Secret scan found no source credentials in tracked files or the three ZIPs.
