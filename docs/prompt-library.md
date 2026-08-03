# Prompt library

These templates are intentionally bounded. Replace bracketed values and keep the forbidden actions intact.

## Shared contract

Every task should use:

```text
Context: [repository, current behavior, relevant files]
Goal: [one measurable outcome]
Allowed actions: inspect files, edit scoped files, run offline checks
Forbidden actions: secrets, anti-bot bypass, purchases, unapproved external messages
Acceptance criteria: [observable behavior]
Tests: [offline deterministic commands]
Live verification limits: [none or exact authorized action]
Git rules: stage only scoped files; no push unless explicitly requested
Expected report: changes, evidence, failures, remaining risk, verdict
```

## 1. Initial project planning

```text
Context: I have a repository for [purpose]. Inspect its docs and current tree.
Goal: Produce a phased implementation plan with dependencies and rollback points.
Allowed actions: read-only inspection and plan updates.
Forbidden actions: implementation, live requests, secret access.
Acceptance criteria: every phase has files, tests, risks, and a clear gate.
Tests: none beyond read-only checks.
Live verification limits: none.
Git rules: do not change Git state.
Expected report: plan and unresolved decisions.
```

## 2. Architecture design

```text
Context: [existing modules and constraints].
Goal: Design a modular source→parser→domain→storage→notification flow.
Allowed actions: inspect and propose interfaces.
Forbidden actions: bypasses, schema changes without approval.
Acceptance criteria: type-hinted boundaries, error ownership, test seams, Mermaid flow.
Tests: list fixture and integration tests before implementation.
Live verification limits: offline only.
Git rules: no commit.
Expected report: architecture, tradeoffs, migration impact.
```

## 3. Source adapter implementation

```text
Context: Add public source [name] with [URL/policy].
Goal: Implement a controlled adapter using timeout, rate limits, and explicit failures.
Allowed actions: edit source adapter, models, fixtures, tests.
Forbidden actions: CAPTCHA, proxy rotation, stealth, fingerprint spoofing, purchases.
Acceptance criteria: disabled behavior, parser errors, source status, deterministic fixtures.
Tests: pytest fixture suite and lint.
Live verification limits: only if separately authorized, one bounded request.
Git rules: stage only source-scoped files.
Expected report: access policy, code, tests, limitations.
```

## 4. HTML parser implementation

```text
Context: Parse saved HTML fixture [file] into [model].
Goal: Extract [fields] without live-site coupling.
Allowed actions: parser, synthetic/redacted fixtures, unit tests.
Forbidden actions: live scraping in tests, bypass code, invented selectors without evidence.
Acceptance criteria: valid data, missing fields, malformed HTML, and drift failure are covered.
Tests: pytest [target], ruff.
Live verification limits: none.
Git rules: no unrelated rewrites.
Expected report: fields, fixture provenance, edge cases.
```

## 5. Baseline and deduplication

```text
Context: Existing source has first-scan baseline and event delivery tables.
Goal: Prevent bulk baseline notifications and duplicate event/channel delivery.
Allowed actions: repository, service, migration, fixture tests.
Forbidden actions: deleting user data or adding periodic heartbeat state.
Acceptance criteria: baseline silent, new item once, retryable failed delivery, stable event key.
Tests: first/second scan and delivery retry tests.
Live verification limits: offline only.
Git rules: explain any migration and rollback.
Expected report: event sequence and database assertions.
```

## 6. Telegram integration

```text
Context: Use the existing notifier/dispatcher; credentials are in local .env.
Goal: Add or fix delivery without direct calls outside the notifier adapter.
Allowed actions: notifier tests with fake responses and redaction checks.
Forbidden actions: printing token/chat ID, sending without explicit approval, logging payload secrets.
Acceptance criteria: timeout/retry, delivery status, redacted errors, dry-run.
Tests: offline mock notifier tests.
Live verification limits: one approved test message only.
Git rules: never stage .env or databases.
Expected report: delivery result with masked identifiers.
```

## 7. Windows Task Scheduler setup

```text
Context: Task [name] runs [command] from [neutral project path].
Goal: Configure current-user Interactive/Limited AtLogOn with safe UAC fallback.
Allowed actions: scripts, docs, parser checks, approved local task test.
Forbidden actions: SYSTEM by default, credential guessing, unrelated task deletion.
Acceptance criteria: preflight, UTF-8, -Force, -NoElevation, verify state and 267009 meaning.
Tests: PowerShell parse and offline Python checks.
Live verification limits: stop/start only when explicitly authorized.
Git rules: no secrets or local paths in public docs.
Expected report: principal, action, state, LastTaskResult.
```

## 8. Security audit

```text
Context: Audit repository [path] for public release.
Goal: Find credentials, local paths, unsafe access behavior, and sensitive artifacts.
Allowed actions: read-only scans and redacted documentation fixes.
Forbidden actions: exposing findings containing secrets, rotating credentials without approval.
Acceptance criteria: working tree/history scan, ignore rules, secret remediation plan.
Tests: git grep, git ls-files, check-ignore, test suite.
Live verification limits: no live requests.
Git rules: do not push if exposure is found.
Expected report: findings, evidence, severity, verdict.
```

## 9. Independent production audit

```text
Context: Review claimed production readiness for [feature].
Goal: Compare claims with code, config, tests, and actual evidence.
Allowed actions: read-only inspection and report.
Forbidden actions: silently fixing claims or running unapproved live operations.
Acceptance criteria: each claim is verified, missing, or contradicted.
Tests: inspect existing results; run safe offline checks only.
Live verification limits: none unless separately authorized.
Git rules: no mutation.
Expected report: evidence matrix and verdict.
```

## 10. Bug-fix prompt

```text
Context: Reproduce [failure] in [file/command].
Goal: Fix the smallest scoped cause without changing unrelated behavior.
Allowed actions: inspect, patch, regression test.
Forbidden actions: broad rewrite, bypass, deleting tests or data.
Acceptance criteria: regression reproduces before fix and passes after fix.
Tests: targeted test, full suite, lint/format.
Live verification limits: only the exact approved command.
Git rules: show diff and stage only relevant files.
Expected report: root cause, patch, checks, remaining risk.
```

## 11. Test coverage improvement

```text
Context: Coverage gap [module/branch].
Goal: Add deterministic tests for behavior, not arbitrary line coverage.
Allowed actions: fixtures, fakes, temporary databases, tests.
Forbidden actions: network calls, real Telegram, sleeps longer than necessary.
Acceptance criteria: failure, retry, disabled, baseline, and secret-redaction paths are covered.
Tests: targeted pytest then full pytest and ruff.
Live verification limits: none.
Git rules: do not stage generated coverage.
Expected report: cases added and final result.
```

## 12. Documentation generation

```text
Context: Current behavior is in [code/config/tests].
Goal: Write accurate [language] docs for [audience].
Allowed actions: inspect source and edit docs.
Forbidden actions: inventing capabilities, publishing secrets or local paths.
Acceptance criteria: commands work, limitations are explicit, links resolve.
Tests: config validation, command help, link/path scan.
Live verification limits: none.
Git rules: docs-only scope unless a blocker is proven.
Expected report: claims cross-checked against files.
```

## 13. GitHub release preparation

```text
Context: Prepare repository [name] for a public alpha release.
Goal: Add bilingual docs, CI, templates, changelog, and security audit.
Allowed actions: scoped public-facing files and offline checks.
Forbidden actions: secrets, local paths, fake CI badges, bypass claims.
Acceptance criteria: clean package, neutral paths, public README, release notes.
Tests: uv sync --locked, pytest, ruff, config validation, git diff check.
Live verification limits: do not repeat live tests unless explicitly requested.
Git rules: confirm scope, commit intentionally, push/tag only when authorized.
Expected report: files, commit, repo, tag, CI, verdict.
```

## 14. Adding a new public source

```text
Context: Proposed source [name] exposes [public page/API/feed].
Goal: Assess and implement only if normal access and maintenance are acceptable.
Allowed actions: policy review, adapter, fixture, opt-in config.
Forbidden actions: bypass, credential collection, high-frequency polling.
Acceptance criteria: source permission, rate limit, disabled fallback, parser tests.
Tests: offline deterministic fixtures and failure tests.
Live verification limits: one approved smoke request.
Git rules: document provenance and do not enable by default without evidence.
Expected report: go/no-go decision and reason.
```

## 15. Disabling a source that returns 403/CAPTCHA

```text
Context: Source [name] returned [status/challenge] during controlled access.
Goal: Disable live production scheduling while preserving offline parser work.
Allowed actions: config, scheduler guard, docs, fixture tests.
Forbidden actions: CAPTCHA, proxy, stealth, fingerprint, cookie or access-control bypass.
Acceptance criteria: no job, no source failure notification, clear CLI result.
Tests: disabled config and scheduler tests.
Live verification limits: no retry beyond approved normal check.
Git rules: record decision; no secret or bypass code.
Expected report: evidence, policy, user alternative, verdict.
```

## 16. Secret leakage inspection

```text
Context: Public release candidate [repo].
Goal: Scan working tree and history for token, chat ID, cookies, auth, DB, logs, and local secrets.
Allowed actions: read-only Git scans and safe ignore-rule changes.
Forbidden actions: printing secret values, pushing after exposure.
Acceptance criteria: patterns checked, files excluded, history finding disposition.
Tests: git grep, git ls-files, check-ignore, diff scan.
Live verification limits: none.
Git rules: stop publication on confirmed secret exposure.
Expected report: masked findings and verdict.
```

## 17. Regression test prompt

```text
Context: Behavior [description] previously worked or was fixed.
Goal: Add a small deterministic regression test.
Allowed actions: fixture/fake/temp DB test changes.
Forbidden actions: live network, real credentials, brittle timing.
Acceptance criteria: test fails for the old behavior and passes for the current behavior.
Tests: targeted and full suite.
Live verification limits: none.
Git rules: test-only scope unless implementation is required.
Expected report: reproduction and assertion.
```

## 18. Live verification prompt

```text
Context: Offline checks passed for [feature].
Goal: Perform exactly [one bounded live action] and inspect [evidence].
Allowed actions: the named command, target, duration, and read-only verification.
Forbidden actions: extra messages, bypasses, purchases, credential output, destructive cleanup.
Acceptance criteria: [exact state/event/count].
Tests: offline suite must already pass.
Live verification limits: stop after the named evidence is collected.
Git rules: do not commit runtime artifacts; report any external side effect.
Expected report: command, evidence, side effects, verdict.
```
