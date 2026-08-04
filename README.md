# Deal Watcher

A lightweight, local-first deal monitoring and Telegram notification tool for public forum listings.

Türkçe dokümantasyon: [README.tr.md](README.tr.md)

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows-0078D4?logo=windows&logoColor=white)](docs/windows-deployment.md)

## Project overview

Deal Watcher watches the public Donanım Arşivi “Sıcak Fırsatlar” forum listing, classifies relevant topics, stores local state in SQLite, and delivers deduplicated Telegram notifications. It is local-first: configuration, baseline state, delivery history, and logs stay on the operator’s machine.

The current alpha focuses on one production source: the public forum listing. Akakçe adapters and offline fixtures remain available for experimental development, but Akakçe is disabled by default and is not live-verified.

## Current capabilities

- Public forum polling with controlled HTTP timeouts, retry/backoff, jitter, and response checks.
- Baseline on the first successful scan; existing topics are not sent as a bulk notification.
- Topic classification, urgent signals, persistent event keys, and delivery deduplication.
- Process-local `runtime_started` and `first_successful_scan` lifecycle notifications, with no periodic heartbeat.
- Telegram delivery through the shared dispatcher/outbox flow.
- Windows Task Scheduler autostart for the current interactive user.
- Offline HTML fixtures and deterministic tests.
- Akakçe parser code and fixtures retained under an experimental, disabled-by-default policy.

## How it works

1. Validate YAML configuration and open/migrate SQLite.
2. Acquire the single-instance lock.
3. Emit one process-start event if enabled.
4. Poll the forum listing through the controlled HTTP client.
5. Parse and classify topics, then apply baseline and deduplication rules.
6. Emit the first-success event once after the first successful Forum scan.
7. Persist notification events before dispatching them to Telegram.

## Architecture

See [architecture.md](docs/architecture.md) for module boundaries, lifecycle events, and Mermaid diagrams.

## Supported source

The active source is Donanım Arşivi Sıcak Fırsatlar. It is a public forum listing and the project uses normal, rate-limited HTTP access. The first page is polled about every five minutes with jitter; the configured second-page interval is retained for future pagination support.

Akakçe is experimental and disabled by default. Controlled verification of direct automated HTTP access returned HTTP 403. The project does not use CAPTCHA solving, proxy rotation, stealth browsers, fingerprint spoofing, or access-control bypass. For price alerts, use Akakçe’s official “Fiyatı Takip Edin” feature.

## Notification flow

Forum events are persisted in SQLite, then passed through the existing dispatcher and channel delivery records. Telegram failures are isolated from source execution and redacted before logs or delivery records. A new runtime emits `runtime_started` once and the first successful Forum scan emits `first_successful_scan` once. There is no daily, hourly, or per-scan heartbeat.

## Category classification

The configured category names and their human-readable meanings are:

| Priority | Code | Meaning |
| --- | --- | --- |
| Urgent | `gpu` | Graphics cards |
| Urgent | `cpu` | Processors |
| Urgent | `motherboard` | Motherboards |
| Urgent | `cpu_cooler` | CPU coolers and thermal products |
| Normal | `cooling_and_fans` | Cooling and fans |
| Normal | `memory` | RAM and memory |
| Normal | `storage` | SSD, NVMe, HDD, and storage |
| Normal | `power_supply` | Power supplies |
| Normal | `pc_case` | PC cases |
| Normal | `monitor` | Monitors |
| Normal | `laptop` | Laptops |
| Normal | `complete_system` | Prebuilt/complete systems |
| Normal | `peripherals` | Keyboard, mouse, webcam, and peripherals |
| Normal | `networking` | Networking equipment |
| Normal | `phone_tablet_watch` | Phones, tablets, and watches |
| Normal | `audio` | Headphones, microphones, and speakers |
| Normal | `supplement` | Supplements |
| Normal | `bank_campaign` | Bank campaigns |
| Normal | `grocery` | Grocery and household products |
| Digest/other | `other` | Unclassified or lower-priority topics |

Urgent signals are `fiyat_hatasi`, `son_stok`, `bir_veya_iki_stok`, `sinirli_stok`, `tekrar_stokta`, `guclu_kupon`, `sepette_indirim`, and `olagan_disi_dusuk_fiyat`. Negative rules prevent accessory or cable topics from being misclassified as the target product.

## Baseline and deduplication

The first successful scan establishes a local baseline and does not send all existing topics. Later scans compare stable topic identifiers and topic state. New or eligible changes create persistent event keys; delivery records prevent the same event/channel pair from being delivered twice.

## Installation

Requirements: Python 3.12+, [uv](https://docs.astral.sh/uv/), and a Windows or development environment supported by the project.

```powershell
git clone https://github.com/Darkem0/deal-watcher.git
cd deal-watcher
uv sync --locked
Copy-Item .env.example .env
uv run deal-watcher validate-config
```

Do not commit `.env`, databases, logs, or credentials.

## Telegram setup

Create a bot with BotFather, identify the destination chat, and set the values only in the local `.env` file:

```dotenv
TELEGRAM_BOT_TOKEN=replace-with-your-local-token
TELEGRAM_CHAT_ID=replace-with-your-local-chat-id
```

Preview without sending:

```powershell
uv run deal-watcher test-notification --dry-run
```

The controlled real notification command is opt-in and sends only when explicitly requested:

```powershell
uv run deal-watcher test-notification --send
```

## Windows autostart

The installer first creates a current-user `Interactive`/`Limited` task triggered at logon. It uses one controlled UAC self-elevation fallback only when Windows denies registration. See [Windows deployment](docs/windows-deployment.md) for neutral-path examples, verification, stop/start, and uninstall instructions.

## Configuration

- `config/forum.yaml` defines the forum URL, polling intervals, categories, and urgent signals.
- `config/settings.yaml` defines network, storage, notification, rules, and Akakçe settings.
- `akakce.enabled` is `false` and `status` is `experimental` by default.
- `notifications.send_runtime_started` and `notifications.send_first_successful_scan` default to `true`.

## Running manually

```powershell
uv run deal-watcher once --source forum --dry-run
uv run deal-watcher once --source all --dry-run
uv run deal-watcher run
```

For fixture-based development:

```powershell
uv run deal-watcher forum-scan --fixture tests/fixtures/forum_baseline.html --database data/demo.sqlite3
uv run deal-watcher once --source forum --dry-run --forum-fixture tests/fixtures/forum_update.html --database data/demo.sqlite3
```

## Testing

```powershell
uv sync --locked --extra dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Tests are offline and deterministic. Live websites, Telegram credentials, and Task Scheduler are not used by CI.

## Vibe coding development process

This repository was developed iteratively with human direction and an AI coding agent: plan, implement, test, independently audit, perform explicitly authorized live verification, and prepare a release. The human remains responsible for scope, credentials, live actions, review, and release decisions. See [Building Deal Watcher with Vibe Coding](docs/vibe-coding-guide.md) and the [prompt library](docs/prompt-library.md).

## Prompt examples

Reusable task templates for source adapters, parser changes, security audits, regression tests, and release work are in [docs/prompt-library.md](docs/prompt-library.md).

## Limitations

- The forum adapter currently focuses on the first listing page.
- HTML structure can change and should be covered by reviewed fixtures.
- Telegram and Windows Task Scheduler require operator setup.
- This is an alpha release; no production availability guarantee is made.
- Akakçe live access is not verified and is not part of the default production path.

## CAPTCHA and anti-bot policy

The project does not solve CAPTCHAs or bypass access controls. It does not add stealth browser behavior, proxy rotation, fingerprint spoofing, cookie theft, or anti-bot evasion. A source that does not permit normal automated access remains disabled or experimental. Read [source access policy](docs/source-access-policy.md).

## Privacy and security

Credentials stay in the local environment and are redacted from errors. SQLite and logs are local artifacts and ignored by Git. Do not put tokens, chat IDs, cookies, authorization headers, or personal data in issues, fixtures, pull requests, or reports. See [SECURITY.md](SECURITY.md).

## Responsible use

Use only public, permitted sources; respect terms of service, robots policies, rate limits, and applicable law. Poll conservatively. The project never purchases, carts, reserves, or pays for anything.

## Roadmap

- Improve forum pagination while preserving baseline and deduplication.
- Expand fixture coverage for DOM drift and classification edge cases.
- Improve operational diagnostics and public release automation.
- Consider a new source only when normal access, permission, and maintenance boundaries are clear.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md), use offline fixtures, run the quality checks, and keep secrets and live-site dependencies out of tests.

## License

Released under the [MIT License](LICENSE).

## Acknowledgements

See [ACKNOWLEDGEMENTS.md](ACKNOWLEDGEMENTS.md) for projects that informed research and design discussions.
