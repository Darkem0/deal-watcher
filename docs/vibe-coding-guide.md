# Building Deal Watcher with Vibe Coding

Vibe coding is an AI-assisted development style in which a person describes intent, constraints, acceptance criteria, and evidence requirements while an agent helps inspect, implement, test, and document the work. It is not a replacement for engineering judgment.

## Roles and workflow

The human owns scope, permissions, credentials, legal boundaries, live actions, review, and release decisions. The coding agent can inspect the repository, propose a plan, implement bounded changes, run local checks, and report evidence. A safe loop is:

```text
plan → implementation → audit → live verification → release
```

This project followed that loop through an initial implementation, independent audit, scheduler and dispatcher fixes, authorized Telegram verification, Windows Task Scheduler permission remediation, runtime lifecycle notifications, baseline/dedup tests, secret checks, and public-release preparation.

## Why short prompts are insufficient

“Build the app” omits source permissions, failure behavior, data retention, test boundaries, secrets, and deployment conditions. A useful task names allowed actions, forbidden actions, acceptance criteria, deterministic tests, live-verification limits, and Git rules.

## Acceptance criteria and tests

State observable outcomes: event types, exact message text, counts, exit codes, task principal, and delivery status. Require offline fixtures for parsers. A live check should be separately authorized and should never become a CI dependency.

## Secrets and live access

Use `.env` or a secure store; never paste secrets into prompts, logs, fixtures, commits, or reports. Treat live Telegram sends, task registration, external publication, and source access as explicit gates. Do not weaken CAPTCHA, robots, rate-limit, or access-control protections.

## Preventing wrong assumptions

Ask the agent to inspect current files and verify claims against code/config. Require it to label unknowns, preserve existing behavior, and stop when a missing credential or policy decision materially changes scope. The user should inspect real output, especially notification recipients, database paths, and release contents.

## Ownership and responsibility

AI-generated code is still adopted, reviewed, and operated by people. Human direction and iterative evidence—not a claim that AI worked alone—explain this repository’s history. Use an independent audit before a public release, then review the diff, history, package contents, and release page yourself.

## Safe and unsafe agent scopes

Good tasks include adding fixture tests, documenting a parser contract, auditing secret patterns, or preparing a release diff. Do not grant an agent permission to bypass anti-bot controls, collect credentials, purchase goods, publish unknown files, or send external messages without an explicit, bounded request.

See [prompt-library.md](prompt-library.md) for copyable task templates.
