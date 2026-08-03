# WINDOWS TASK SCHEDULER PERMISSION FIX REPORT

## 1. Root cause

The previous installer called Register-ScheduledTask without an explicit
current-user principal, logon type, or limited run level. Windows therefore
returned access denied (0x80070005) in the observed non-admin setup.

## 2. Previous task principal/settings

The previous script did not specify Principal and relied on Task Scheduler
defaults. It also had no controlled elevation path, no complete preflight, and
no UTF-8 output setup.

## 3. New permission model

The task now uses the current Windows identity, Interactive logon, and Limited
run level. It does not use SYSTEM, Highest, stored credentials, or a root
admin-only principal. It runs only when the user is logged on by default.

## 4. Self-elevation behavior

Registration first runs as the current user. Only an access-denied result
triggers one UAC self-elevation attempt. -NoElevation returns a clear
non-zero error, -Elevated prevents an elevation loop, and child exit codes are
propagated.

## 5. UTF-8 fix

Both scripts set UTF-8 output when the host permits it. PowerShell 7 is the
documented default; powershell.exe remains a fallback.

## 6. Install script changes

Preflight checks the project root, pyproject.toml, .venv Python, .env, config,
and creates logs. It validates the scheduler import and configuration before
registration. It configures battery operation, start-when-available, restart
count, and verifies the registered task afterward.

## 7. Uninstall script changes

Uninstall targets only the requested task, reports a missing task without a
stack trace, and uses the same single-attempt elevation behavior on access
denied.

## 8. Offline tests

Python tests, Ruff lint, Ruff format, config validation, and git diff check
passed. Both PowerShell scripts passed PowerShell 7 parser validation.

## 9. Live installation result

The installer was executed once with PowerShell 7 and succeeded. The task
DealWatcher is registered for user emre with Interactive/Limited principal.

## 10. Manual task run result

Start-ScheduledTask succeeded. After 15 seconds the task was still Running,
which is expected for the continuous scheduler loop. No second task instance
was started.

## 11. LastTaskResult

During the active continuous run, LastTaskResult was 267009, the Windows
running-task result. The task state was Running and NumberOfMissedRuns was 0.

## 12. Log verification

logs/deal-watcher.log exists. No token or chat ID was written to the log.
Akakçe remains disabled and the scheduled action points to the forum runtime.

## 13. Git state

Changes are based on commit be582a5. The configured local identity is
Emre Aslan / darkemyedekhesap@gmail.com. No push was performed.

## 14. Remaining issues

The task is intentionally left running after the authorized manual smoke run.
The continuous scheduler has no normal completion code while active; a future
manual health check should inspect State and LastTaskResult after stopping or
after a controlled restart.

## 15. Final verdict

WINDOWS_TASK_READY

## 16. Commands executed

pwsh PowerShell parser validation for both scripts
pwsh install_windows_task.ps1 -ProjectRoot C:\Projects\deal-watcher
Get-ScheduledTask -TaskName DealWatcher
Get-ScheduledTaskInfo -TaskName DealWatcher
Start-ScheduledTask -TaskName DealWatcher
Start-Sleep -Seconds 15
Get-ScheduledTaskInfo -TaskName DealWatcher
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run deal-watcher validate-config
git diff --check
