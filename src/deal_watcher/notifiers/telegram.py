from __future__ import annotations

import time

import httpx

from deal_watcher.models.domain import NotificationEvent
from deal_watcher.notifiers.base import format_event


class TelegramNotifier:
    """OS-independent adapter; credentials must be injected from a secure source."""

    channel = "telegram"

    def __init__(
        self, bot_token: str, chat_id: str, timeout_seconds: float = 20, max_retries: int = 2
    ):
        if not bot_token or not chat_id:
            raise ValueError("Telegram bot token and chat id are required")
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.last_message_id: int | None = None

    def send(self, event: NotificationEvent) -> None:
        text = format_event(event)[:4096]
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        for attempt in range(self.max_retries + 1):
            try:
                response = httpx.post(
                    url, json={"chat_id": self.chat_id, "text": text}, timeout=self.timeout_seconds
                )
            except httpx.HTTPError as exc:
                if attempt >= self.max_retries:
                    raise RuntimeError("Telegram request failed") from exc
                time.sleep(min(2**attempt, 4))
                continue
            if response.status_code == 429 and attempt < self.max_retries:
                time.sleep(min(float(response.headers.get("Retry-After", "1")), 30))
                continue
            if response.is_error:
                raise RuntimeError(f"Telegram delivery failed with HTTP {response.status_code}")
            payload = response.json()
            result = payload.get("result", {}) if isinstance(payload, dict) else {}
            message_id = result.get("message_id") if isinstance(result, dict) else None
            self.last_message_id = int(message_id) if isinstance(message_id, int) else None
            return
