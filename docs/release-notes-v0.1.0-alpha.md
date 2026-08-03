# Deal Watcher v0.1.0-alpha

This is an alpha release for local experimentation and controlled deployment. It does not provide a production availability guarantee.

## Included

- Donanım Arşivi Sıcak Fırsatlar forum monitoring.
- Category classification, urgent signals, baseline, and deduplication.
- Telegram delivery through the shared dispatcher and delivery records.
- One process-local `runtime_started` and one first-successful-scan notification; no periodic heartbeat.
- Windows Task Scheduler autostart with current-user Interactive/Limited behavior and controlled UAC fallback.
- Configurable polling, retry, backoff, and jitter.
- Offline deterministic tests, bilingual documentation, CI, issue forms, and prompt library.

## Source-access boundary

Akakçe parser code and offline fixtures remain experimental, but Akakçe is disabled by default. Direct automated HTTP access returned HTTP 403 during controlled verification. CAPTCHA solving, proxy rotation, stealth browser behavior, fingerprint spoofing, cookie theft, and access-control bypass are not included.

Use the official Akakçe “Fiyatı Takip Edin” feature for price alerts. Follow source terms, robots policies, rate limits, and applicable law.

## Setup

See [README.md](../README.md), [README.tr.md](../README.tr.md), and the [Windows deployment guide](windows-deployment.md).
