# Changelog

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

## Unreleased

- Windows Task Scheduler no longer stops the continuous runtime when the user leaves idle state.
- Forum first-page polling default is now five minutes; existing event keys and delivery deduplication remain unchanged.
