# Windows deployment

This guide uses `C:\Projects\deal-watcher` as a neutral example path.

## Requirements and setup

Install Python 3.12+ and [uv](https://docs.astral.sh/uv/), then:

```powershell
git clone https://github.com/Darkem0/deal-watcher.git C:\Projects\deal-watcher
Set-Location C:\Projects\deal-watcher
uv sync --locked
Copy-Item .env.example .env
uv run deal-watcher validate-config
```

Create a Telegram bot with BotFather, identify the chat ID, and keep both values only in `.env`. Preview with `uv run deal-watcher test-notification --dry-run`; a real notification requires the explicit `--send` command and operator approval.

## Forum operation

```powershell
uv run deal-watcher once --source forum --dry-run
uv run deal-watcher run
```

The first successful scan establishes baseline and does not bulk-send existing topics. The first page is polled about every five minutes with jitter. Akakçe is experimental and disabled by default.

## Task Scheduler installation

The installer first registers a current-user `Interactive`/`Limited` task with an `AtLogOn` trigger. Idle termination is explicitly disabled and the continuous task has no execution time limit. If Windows denies registration, it performs one controlled UAC self-elevation attempt. `-NoElevation` disables that fallback; `-Force` is required to replace an existing task.

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\scripts\install_windows_task.ps1" -ProjectRoot "C:\Projects\deal-watcher"
Get-ScheduledTask -TaskName DealWatcher
Get-ScheduledTaskInfo -TaskName DealWatcher
```

The action runs the project’s windowless `pythonw.exe` with `-m deal_watcher.cli run`, uses the project root as working directory, and loads `.env` from that root. No console window is opened, so closing a terminal window cannot stop the task. The task is configured to tolerate battery operation, user idle-state changes, and transient failures.

`LastTaskResult` `267009` / `0x41301` means the continuous task is currently running. It is not an error. Inspect `logs/deal-watcher.log` without exposing credentials.

## Stop, start, uninstall

```powershell
Stop-ScheduledTask -TaskName DealWatcher
Start-ScheduledTask -TaskName DealWatcher
pwsh -NoProfile -ExecutionPolicy Bypass -File ".\scripts\uninstall_windows_task.ps1" -TaskName DealWatcher
```

The uninstaller targets only the named task and reports a missing task clearly. For troubleshooting, rerun config validation, inspect UAC policy, and keep 403/CAPTCHA sources disabled rather than attempting a bypass.
