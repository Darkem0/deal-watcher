# Contributing

Contributions are welcome when they preserve the project’s local-first, offline-tested, and responsible-access boundaries.

## Development setup

```powershell
git clone https://github.com/Darkem0/deal-watcher.git
cd deal-watcher
uv sync --locked --extra dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Pull request expectations

- Keep the change focused and explain the user-visible impact.
- Add deterministic regression tests for behavior changes.
- Use synthetic or redacted fixtures; do not make unit tests depend on live sites.
- Update English and Turkish documentation when public behavior changes.
- Run the full test, lint, format, and `git diff --check` suite.
- Do not commit `.env`, SQLite databases, locks, logs, caches, coverage output, cookies, tokens, or chat IDs.
- Redact local usernames and absolute paths from reports and examples.

## Source adapters

Before proposing a source, document:

- whether the page/API/feed is public;
- expected polling frequency and rate limits;
- terms-of-service or robots considerations;
- whether normal HTTP access succeeds;
- how parser drift will be detected;
- how the source can be disabled cleanly.

Do not add CAPTCHA solving, proxy rotation, stealth browser behavior, fingerprint spoofing, cookie theft, credential collection, automatic purchases, or access-control bypass. See [`docs/source-access-policy.md`](docs/source-access-policy.md).

## Live verification

Live source requests, Telegram sends, Task Scheduler changes, release publication, and other external side effects require explicit, bounded approval. CI must remain offline and must not require secrets.

## Commit and PR hygiene

- Use clear commit messages.
- Keep generated runtime artifacts out of Git.
- Describe test evidence and known limitations in the pull request.
- Do not weaken tests merely to make a change pass.

---

# Katkı rehberi — Türkçe özet

- Python 3.12 ve `uv` kullanın.
- Canlı sitelere bağlı kırılgan test eklemeyin; redakte veya sentetik fixture kullanın.
- Davranış değişikliğine regresyon testi ekleyin.
- Kullanıcıya görünen davranış değiştiğinde İngilizce ve Türkçe belgeleri birlikte güncelleyin.
- Secret, `.env`, SQLite, lock, log, cache, coverage, token, chat ID ve cookie dosyalarını commit etmeyin.
- CAPTCHA, proxy rotation, stealth, fingerprint değiştirme, credential toplama, otomatik satın alma veya erişim kontrolü aşma kodu eklemeyin.
- Değişikliklerden sonra `uv run pytest`, Ruff kontrolleri ve `git diff --check` çalıştırın.
