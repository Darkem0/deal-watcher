# DEAL-WATCHER DEPLOYMENT AND RELEASE PREPARATION REPORT

## 1. Initial Git state

- Repository had no commits on master.
- The index was partially staged and did not represent the complete working tree.
- A safety record was created outside the repository before index cleanup.
- No reset, clean, checkout, merge, rebase, remote update, or push was performed.

## 2. Final test results

- uv sync --locked --extra dev: passed.
- pytest: 45 passed.
- Coverage: 72% total branch-aware coverage.
- Ruff lint: passed.
- Ruff format check: passed.
- git diff --check: passed.
- Config validation: passed.
- Forum fixture dry-run: passed.
- Scheduler single iteration: passed.
- Notification dry-run: passed.

## 3. Live Forum smoke test

One normal HTTP request was made to the configured Donanım Arşivi page-1 URL.

- HTTP 200, final URL unchanged, 129160 response bytes.
- Parser reported no parser errors and extracted 15 topics.
- No 403, 429, CAPTCHA, or challenge was observed.
- No real notification was sent and the normal database was not used.
- The verification script stopped while printing details because it used the
  wrong local field name, canonical_url; the domain field is
  canonical_topic_url. No second live request was made.
- Existing offline parser and baseline tests cover topic ID, canonical URL,
  prefixes, timestamps, reply/view parsing, Turkish text, emoji, and baseline
  notification suppression.

## 4. Akakçe disabled verification

- Default configuration is enabled=false and status=experimental.
- Scheduler does not add an Akakçe job when disabled.
- once --source all skips disabled Akakçe.
- once --source akakce returns source disabled without a stack trace.
- Akakçe source failure notification is not created while disabled.
- Playwright is only in the experimental optional extra.
- Akakçe parser, migration, fixtures, and offline tests remain present.

## 5. Telegram deployment readiness

Dry-run passed. No real Telegram message was sent. The real test is documented
but was not executed:

    uv run deal-watcher test-notification --send

It requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in the local .env.

## 6. Windows Task Scheduler readiness

The installer uses the project-root .venv Python, sets WorkingDirectory to the
project root, validates config before registration, creates logging through the
CLI preflight, requires -Force to replace an existing task, and does not send
Telegram messages. Uninstall targets only the named task.

Exact user command:

    powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\install_windows_task.ps1" -ProjectRoot "C:\Projects\deal-watcher"

No real task was created.

## 7. Documentation and licensing

README, STATUS, PLAN, DECISIONS, LICENSE, ACKNOWLEDGEMENTS, SECURITY,
CONTRIBUTING, and deployment documentation were updated. The MIT copyright
line uses the neutral project contributor designation because no local Git
identity was configured; no owner name was invented.

## 8. Security and secret scan

No real token, chat ID, .env, database, log, coverage, cache, or Playwright
browser binary is included. The only secret-pattern scan hits were README
placeholder examples using three dots. CAPTCHA, proxy, stealth, fingerprint
changes, and access-control bypass are not implemented.

## 9. Git index cleanup

The intended release scope is staged only from src, tests, redacted fixtures,
config, scripts, docs, project documentation, packaging files, and uv.lock.
Runtime artifacts remain ignored.

## 10. Initial commit

Commit was not created because the repository has no configured Git author or
committer identity. No name or email was invented.

## 11. Recommended GitHub repository settings

- Keep the repository public only after reviewing the staged diff.
- Protect the default branch and require CI checks.
- Enable secret scanning and push protection.
- Do not publish .env, SQLite, logs, coverage, or browser binaries.
- Add a CI job for uv lock validation, pytest, Ruff lint, Ruff format, and diff
  or equivalent repository checks.

## 12. Exact local deployment commands

    uv sync --locked
    Copy-Item .env.example .env
    uv run deal-watcher validate-config
    uv run deal-watcher once --source forum --dry-run
    uv run deal-watcher test-notification --dry-run

## 13. Exact publication commands

After configuring Git identity and reviewing the staged diff:

    git commit -m "Initial release of Donanim Arsivi deal watcher"
    git remote add origin <PUBLIC_REPOSITORY_URL>
    git push -u origin master

The remote and push commands were not run.

## 14. Remaining user actions

1. Configure Git user.name and user.email for the local commit.
2. Review staged files and create the initial commit.
3. Configure real Telegram secrets only when ready for a delivery test.
4. Decide whether to install the Windows Task Scheduler task.
5. Create the public GitHub repository and push manually.

## 15. Final verdict

RELEASE_BLOCKED

The local deployment configuration is prepared and tests pass, but the initial
commit is blocked by missing Git identity. The live smoke parser verification
also needs a corrected offline verification script before claiming all live
field assertions.

## 16. Commands executed

git status --short --branch
git diff --cached --stat
git diff --stat
git ls-files --others --exclude-standard
uv sync --locked --extra dev
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
git diff --check
uv run deal-watcher validate-config
uv run deal-watcher once --source forum --dry-run
uv run deal-watcher run --max-iterations 1
uv run deal-watcher test-notification --dry-run
uv run deal-watcher once --source akakce
one normal HTTP request to the Donanım Arşivi page-1 URL
secret pattern scan with rg
