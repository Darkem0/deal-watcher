from __future__ import annotations

from deal_watcher.http_client import HttpClientError


def fetch_browser_html(url: str, *, headless: bool) -> str:
    """One normal Playwright navigation; no CAPTCHA handling, proxy, or fingerprint changes."""
    try:
        from playwright.sync_api import Error, sync_playwright
    except ImportError as exc:
        raise HttpClientError(
            "browser fallback is unavailable", error_type="browser_unavailable"
        ) from exc
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=headless)
            try:
                page = browser.new_page()
                response = page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                content = page.content()
                status = response.status if response else None
            finally:
                browser.close()
    except Error as exc:
        raise HttpClientError("browser fallback failed", error_type="browser_failure") from exc
    if status and status >= 400:
        raise HttpClientError(
            "browser source access denied", error_type="access_denied", status_code=status
        )
    if "captcha" in content[:20_000].casefold() or "challenge" in content[:20_000].casefold():
        raise HttpClientError(
            "access challenge detected", error_type="captcha_or_challenge", status_code=status
        )
    return content
