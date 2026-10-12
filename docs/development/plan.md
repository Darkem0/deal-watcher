# Roadmap

Deal Watcher is intentionally small: a local forum monitor, persistent baseline/deduplication, and bounded notification delivery. Roadmap items must preserve responsible source access and deterministic offline tests.

## Completed foundation

- Layered Python 3.12 package with source, service, storage, notifier, runtime, and CLI boundaries.
- YAML configuration validated with Pydantic.
- SQLite migrations, baseline state, forum topics, events, delivery records, and backups.
- Donanım Arşivi first-page parser with redacted/synthetic fixtures.
- Turkish-aware category classification and urgent-signal handling.
- Persistent event and channel-delivery deduplication.
- Telegram notifier with retry, rate-limit handling, message limits, and secret redaction.
- Process-start and first-success lifecycle notifications without periodic heartbeat.
- Single-instance scheduler with interval, jitter, failure backoff, and graceful shutdown.
- Windows Task Scheduler install/uninstall scripts using current-user `AtLogOn`.
- English/Turkish public documentation, prompt library, Vibe Coding guide, issue templates, and cross-platform CI.
- Akakçe parser experiments retained offline while live scheduling remains disabled.

## Near-term priorities

### 1. Forum pagination

Add an explicitly configured second-page adapter without increasing request frequency unnecessarily.

Acceptance criteria:

- page-one failure and page-two failure remain isolated;
- duplicate sticky topics across pages are collapsed by topic ID;
- first-run baseline remains silent;
- polling intervals remain independently configurable;
- fixtures cover page overlap and partial success.

### 2. Operational status command

Provide a read-only CLI status view for the last successful source run, last failure, item count, task/runtime hints, and last delivered event.

Acceptance criteria:

- no secret output;
- works with an empty database;
- does not contact live sources;
- timezone display is explicit.

### 3. Digest semantics

Decide whether `digest` should remain a label or become an actual delayed batching queue. Do not imply batching until the queue, retry, persistence, and tests exist.

### 4. Parser drift diagnostics

Improve minimal redacted failure artifacts and selector diagnostics while avoiding storage of full user-generated pages.

## Later candidates

- Additional public forum or feed sources with documented normal access.
- Optional restoration/retention tooling for SQLite backups.
- More classification fixtures for mixed-product, accessory, and Turkish spelling edge cases.
- Packaging and installation improvements beyond repository-based `uv` setup.

## Explicitly out of scope

- CAPTCHA solving or anti-bot bypass.
- Proxy rotation, stealth, fingerprint spoofing, or cookie theft.
- Automatic purchasing, cart operations, payments, or stock reservation.
- Enabling a source by default before normal access and live maintenance are verified.

## Change gate

Each roadmap change should define:

1. context and source-access boundary;
2. observable acceptance criteria;
3. deterministic offline tests;
4. migration and rollback impact;
5. live verification limits;
6. documentation changes;
7. Git and release evidence.

---

# Yol haritası — Türkçe özet

Kısa vadeli odaklar: forum ikinci sayfa desteği, secret göstermeyen bir durum komutu, `digest` davranışının açık biçimde karara bağlanması ve parser drift tanılamasının geliştirilmesidir. CAPTCHA/anti-bot aşma, proxy/stealth yöntemleri ve otomatik satın alma kapsam dışıdır.
