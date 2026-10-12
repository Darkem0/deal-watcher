# Changelog

## [0.2.0-alpha] — 2026-10-12

- Shared interactive setup for Windows, Linux and macOS; hidden token input and optional Chat ID discovery.
- Linux current-user systemd installer; macOS launchd uses the real runtime CLI and safely renders paths.
- Forum scheduler reads jitter from validated configuration instead of a hard-coded maximum.
- Platform defaults to auto; Linux config and macOS CI coverage added.
- Concise Turkish entry point, unified installation and source-based project comparison.
- Replaced an existing notification-test Chat ID that matched the production configuration with a synthetic value. Previous public Git history is unchanged.
- No personal credentials, databases, logs or Mac-specific deployment state are distributed.

## Earlier unreleased fixes

### Fixed

- Windows Task Scheduler no longer stops the continuous runtime when the user leaves idle state.
- Forum first-page polling default is five minutes.

- Turkish/ASCII normalization now applies consistently to category exclusions, urgent signals, stock phrases, and state-change signals.
- Common low-stock phrases such as `1 adet`, `2 adet`, and `sınırlı stok` map correctly to configured urgency codes.
- The documented polling jitter now matches the current runtime policy.
- Telegram is the safe default notification channel; Windows toast remains an explicit optional extra.

### Documentation

- Clarified that the observed topic count is not a fixed parser limit.
- Clarified that `digest` is currently a priority label rather than a delayed batching queue.
- Added CI visibility, bilingual security/contribution guidance, and a public roadmap.

## [0.1.0-alpha]

This is an alpha release. It is useful for local experimentation and controlled deployment; no production availability guarantee is made.

- Donanım Arşivi forum monitoring.
- Category classification and urgent signals.
- Baseline and persistent deduplication.
- Telegram delivery through dispatcher and delivery records.
- Process-local runtime lifecycle notifications.
- Windows Task Scheduler autostart with Interactive/Limited user model.
- Configurable polling, retry, backoff, and jitter.
- Offline deterministic parser and runtime tests.
- Akakçe experimental adapter retained but disabled by default.
- English and Turkish documentation, responsible source-access policy, and release templates.
- Vibe coding guide and reusable prompt library.

Akakçe direct automated HTTP access returned HTTP 403 during controlled verification. No CAPTCHA or anti-bot bypass is included.
