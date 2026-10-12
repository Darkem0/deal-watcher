# Deal Watcher

Local Donanım Arşivi deal monitoring with Telegram notifications. Windows, Linux and macOS use the same Python 3.12 runtime. [Türkçe](README.md).

## Quick start

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Git, then:

```sh
git clone https://github.com/Darkem0/deal-watcher.git
cd deal-watcher
uv sync --locked
uv run deal-watcher-setup
```

Create your own bot using [BotFather](https://core.telegram.org/bots/tutorial), send it `/start`, and keep its token in local `.env`. The setup prompt hides the token. If you do not know your Chat ID, leave it blank, run `uv run deal-watcher-setup --find-chat`, and fill `TELEGRAM_CHAT_ID` in `.env`. Chat discovery reads Telegram getUpdates; it sends no message.

```sh
uv run deal-watcher-setup --check
uv run deal-watcher test-notification --send
uv run deal-watcher run
```

The test command sends one real Telegram message. `run` monitors until Ctrl+C; the computer must remain awake and online. The first successful scan silently records existing topics; subsequent new/relevant events are delivered. Runtime startup and first-success notifications are separate from deal alerts.

## Features and limits

- Forum first-page monitoring every five minutes, plus configured 10–45 second jitter.
- Turkish-aware product classification and urgency signals.
- Persistent SQLite baseline, event keys and channel delivery records.
- Configurable bounded HTTP retry/backoff and Telegram notifications.
- Current-user Windows Task Scheduler, macOS launchd and Linux systemd installation.
- Akakçe parsers are experimental and disabled by default after HTTP 403 observations.
- `digest` is a priority label, not a delayed batching queue.
- No cloud account or AI model is needed to run locally; GitHub Actions only runs offline CI.
- This is a pre-release. Forum HTML changes can break parsing. One active host per bot avoids duplicate alerts from independent databases.

See [cross-platform setup](KURULUM.md), [architecture](docs/architecture.md), [comparison with reference projects](docs/proje-farklari.tr.md), [access policy](docs/source-access-policy.md), [security](SECURITY.md) and [MIT license](LICENSE).

## Development

```sh
uv sync --locked --extra dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv build
```

CI checks these on Windows, Ubuntu and macOS. Live Telegram and website calls are not CI tests.
