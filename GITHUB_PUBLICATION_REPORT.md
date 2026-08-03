# GitHub public publication report

## 1. Initial repository state

- Local repository was on `master`, commit `68e5f66`.
- No GitHub remote was configured at the start of this publication task.
- GitHub CLI is installed and authenticated as `Darkem0`.
- The Windows `DealWatcher` task was left running as requested.

## 2. Documentation changes

The public package now has bilingual READMEs, English and Turkish Windows guides, architecture and lifecycle diagrams, source-access policy, examples, contribution templates, changelog, and Vibe Coding/prompt-library documents. Historical technical reports were moved under `docs/reports/` and local paths were redacted to neutral examples.

## 3. English README

`README.md` documents current capabilities, categories, baseline/deduplication, Telegram, Windows autostart, limitations, responsible use, and links to Turkish documentation.

## 4. Turkish README

`README.tr.md` explains Forum tracking, baseline, classification, Telegram, AtLogOn, jitter, Akakçe’s disabled status, installation, testing, and uninstall.

## 5. Vibe coding guide

`docs/vibe-coding-guide.md` and `.tr.md` describe human/agent responsibilities, plan→implementation→audit→live verification→release, acceptance criteria, secret safety, and the project’s iterative development history.

## 6. Prompt library

`docs/prompt-library.md` and `.tr.md` provide 18 bounded prompt templates, including source adapters, parser work, baseline/dedup, Telegram, Task Scheduler, security audit, release preparation, disabling 403/CAPTCHA sources, secret inspection, regression tests, and live verification.

## 7. Source access and CAPTCHA policy

`docs/source-access-policy.md` and `.tr.md` state that controlled direct automated Akakçe HTTP access returned HTTP 403. No CAPTCHA, proxy, stealth, fingerprint, cookie, or access-control bypass is used.

## 8. Windows deployment documentation

The English and Turkish deployment guides use neutral paths, document `uv`, `.env`, dry-run, Task Scheduler `Interactive`/`Limited`/`AtLogOn`, UAC fallback, `267009 / 0x41301`, logs, stop/start, and uninstall.

## 9. CI workflow

`.github/workflows/ci.yml` runs locked `uv` sync, pytest, Ruff lint, and Ruff format on Ubuntu and Windows with Python 3.12. It does not call live sources, Telegram, or Task Scheduler.

## 10. GitHub templates

Added bug-report and feature-request forms plus a pull-request checklist covering OS/runtime evidence, redacted logs, source access policy, and secret safety.

## 11. Security scan

The working tree was checked for `.env`, SQLite, logs, authorization headers, bearer tokens, bot-token patterns, chat IDs, and user-specific paths. Public docs use neutral paths. `.gitignore` excludes `.env`, databases, locks, logs, caches, coverage, and build artifacts.

## 12. Secret scan

No real token or chat ID was staged. `.env` is ignored and remains local. Token-looking values in tests are synthetic fixtures used only to verify redaction.

## 13. Files excluded

`.env`, `.venv`, SQLite databases, lock files, logs, cache directories, coverage outputs, and local runtime artifacts are excluded from the public commit.

## 14. Tests and quality checks

Before publication preparation: `55 passed`, Ruff lint passed, Ruff format passed, config validation passed, and `git diff --check` passed. The `laptop` config/classification mismatch found during audit was corrected with a regression test.

## 15. Commit history

The repository currently has a single initial commit. Publication preparation will use a separate readable commit rather than amending the initial commit.

## 16. GitHub repository

Target: `https://github.com/Darkem0/deal-watcher` (public, default branch `main`).

## 17. Release

Target tag: `v0.1.0-alpha`, pre-release. It must state the alpha limitation, active Donanım Arşivi source, Akakçe disabled status, and responsible source-access policy.

## 18. CI status

CI status will be recorded after the first push and workflow dispatch. No passing CI badge is claimed before GitHub reports a result.

## 19. Remaining limitations

The Forum adapter focuses on the first listing page. Akakçe is not live-verified and is disabled by default. Telegram and Task Scheduler require operator-local setup. This is an alpha release with no production availability guarantee.

## 20. Final verdict

`DOCUMENTATION_FIXES_REQUIRED`

This report is updated after GitHub authentication, repository creation, push, tag, release, and CI verification. Until those steps complete, publication is not claimed.

## 21. Commands executed

Representative checks:

```powershell
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run deal-watcher validate-config
git diff --check
git ls-files
git check-ignore -v .env
gh auth status
```
