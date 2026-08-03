# Architecture

Deal Watcher keeps source adapters, parsing, domain decisions, storage, and notification delivery separate. The core is platform-independent; Windows Task Scheduler is a deployment adapter.

```mermaid
flowchart TD
    A[Windows Task Scheduler] --> B[deal-watcher run]
    B --> C[Scheduler]
    C --> D[Forum Source Adapter]
    D --> E[Parser]
    E --> F[Classification]
    F --> G[Baseline / Dedup]
    G --> H[Notification Event]
    H --> I[Dispatcher / Delivery]
    I --> J[Telegram]
```

## Lifecycle flow

```mermaid
sequenceDiagram
    participant S as Scheduler
    participant R as Runtime state
    participant F as Forum
    participant D as Dispatcher
    S->>R: runtime_started (once per process)
    R->>D: persist and deliver
    S->>F: successful scan
    F->>R: first_successful_scan (once per process)
    R->>D: persist and deliver
    F->>D: new_deal / forum event
```

## Modules

- `sources/`: controlled HTTP source adapters and fixture parsers.
- `services/`: forum processing, classification, price history, and notification conversion.
- `storage/`: SQLite schema, migrations, repositories, event and delivery records.
- `notifiers/`: channel adapters and the shared dispatcher.
- `runtime.py`: UTF-8 console setup, timezone conversion, shutdown, instance lock, and process-local lifecycle state.
- `scheduler.py`: jittered jobs, failure backoff, and one-start callback.
- `cli.py`: configuration loading and command orchestration.

The first successful Forum scan establishes baseline state. Event persistence happens before dispatch; delivery status is tracked per event and channel. Lifecycle state is deliberately not persisted as a daily heartbeat.

## Source boundary

Donanım Arşivi is the active Forum source. Akakçe parser code and fixtures are retained for offline/experimental work, but live Akakçe is disabled by default because controlled direct HTTP verification returned 403. No access-control bypass is implemented.
