## Summary

<!-- What changed and why? -->

## Validation

- [ ] `uv run pytest`
- [ ] `uv run ruff check .`
- [ ] `uv run ruff format --check .`
- [ ] `git diff --check`

## Safety checklist

- [ ] No `.env`, token, chat ID, database, log, or local secret is included.
- [ ] Tests are offline and deterministic.
- [ ] No CAPTCHA, proxy rotation, stealth, fingerprint spoofing, or access-control bypass was added.
- [ ] No purchase, cart, reservation, or payment behavior was added.
- [ ] Live verification, if any, was explicitly bounded and documented.

## Evidence and limitations

<!-- Include relevant output and remaining risk. -->
