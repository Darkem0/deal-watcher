from __future__ import annotations

import random
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from time import monotonic

import httpx

RETRYABLE_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})


@dataclass(frozen=True, slots=True)
class HttpResult:
    url: str
    status_code: int
    content: bytes
    content_type: str
    attempts: int
    elapsed_ms: int


class HttpClientError(RuntimeError):
    def __init__(
        self, message: str, *, error_type: str = "http_error", status_code: int | None = None
    ):
        super().__init__(message)
        self.error_type = error_type
        self.status_code = status_code


def _retry_after(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            return max(0.0, parsedate_to_datetime(value).timestamp() - time.time())
        except (TypeError, ValueError, OverflowError):
            return None


class ControlledHttpClient:
    def __init__(
        self,
        *,
        timeout: httpx.Timeout | None = None,
        max_retries: int = 3,
        backoff_seconds: tuple[float, ...] = (2.0, 5.0, 15.0),
        min_interval_seconds: float = 3.0,
        max_response_bytes: int = 5_000_000,
        user_agent: str = "deal-watcher/0.2 (+offline-first monitor)",
        client: httpx.Client | None = None,
        sleeper=time.sleep,
        clock=monotonic,
    ):
        self.timeout = timeout or httpx.Timeout(20.0, connect=10.0)
        self.max_retries = max(0, max_retries)
        self.backoff_seconds = backoff_seconds
        self.min_interval_seconds = max(0.0, min_interval_seconds)
        self.max_response_bytes = max_response_bytes
        self.user_agent = user_agent
        self.client = client or httpx.Client(timeout=self.timeout, follow_redirects=True)
        self._last_request: dict[str, float] = {}
        self._sleep = sleeper
        self._clock = clock

    def close(self) -> None:
        self.client.close()

    def get_html(self, url: str) -> HttpResult:
        host = httpx.URL(url).host or "unknown"
        now = self._clock()
        wait = self.min_interval_seconds - (now - self._last_request.get(host, 0.0))
        if wait > 0:
            self._sleep(wait)
        started = self._clock()
        attempts = 0
        for attempt in range(self.max_retries + 1):
            attempts = attempt + 1
            self._last_request[host] = self._clock()
            try:
                response = self.client.get(
                    url,
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept": "text/html,application/xhtml+xml",
                    },
                )
            except httpx.RequestError as exc:
                if attempt >= self.max_retries:
                    raise HttpClientError(
                        "source request failed", error_type="network_error"
                    ) from exc
                self._backoff(attempt, None)
                continue
            if response.status_code in (401, 403):
                raise HttpClientError(
                    "source access denied",
                    error_type="access_denied",
                    status_code=response.status_code,
                )
            content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
            if response.status_code in RETRYABLE_STATUS and attempt < self.max_retries:
                self._backoff(attempt, response.headers.get("retry-after"))
                continue
            if response.status_code >= 400:
                raise HttpClientError(
                    "source returned an error status",
                    error_type="http_status",
                    status_code=response.status_code,
                )
            if (
                "captcha" in response.text[:20_000].casefold()
                or "challenge" in response.text[:20_000].casefold()
            ):
                raise HttpClientError(
                    "access challenge detected",
                    error_type="captcha_or_challenge",
                    status_code=response.status_code,
                )
            if not (
                content_type.startswith("text/html") or content_type == "application/xhtml+xml"
            ):
                raise HttpClientError(
                    "source did not return HTML",
                    error_type="unexpected_content_type",
                    status_code=response.status_code,
                )
            if len(response.content) > self.max_response_bytes:
                raise HttpClientError(
                    "source response exceeds configured limit",
                    error_type="response_too_large",
                    status_code=response.status_code,
                )
            return HttpResult(
                url,
                response.status_code,
                response.content,
                content_type,
                attempts,
                int((self._clock() - started) * 1000),
            )
        raise HttpClientError("source retry budget exhausted", error_type="retry_exhausted")

    def _backoff(self, attempt: int, retry_after: str | None) -> None:
        delay = _retry_after(retry_after)
        if delay is None:
            base = (
                self.backoff_seconds[min(attempt, len(self.backoff_seconds) - 1)]
                if self.backoff_seconds
                else 0.0
            )
            delay = base * (2**attempt) + random.uniform(0.0, min(1.0, base / 4 if base else 0.0))
        self._sleep(delay)
