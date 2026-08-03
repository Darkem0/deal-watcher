from __future__ import annotations

import platform
import subprocess

from deal_watcher.models.domain import NotificationEvent
from deal_watcher.notifiers.base import format_event


class WindowsToastNotifier:
    channel = "windows_toast"

    def send(self, event: NotificationEvent) -> None:
        if platform.system() != "Windows":
            raise RuntimeError("WindowsToastNotifier requires Windows")
        try:
            from winotify import Notification
        except ImportError as exc:
            raise RuntimeError("install the 'notifications' extra for Windows toast") from exc
        Notification(app_id="Deal Watcher", title=event.title, msg=format_event(event)).show()


class MacOSNotifier:
    channel = "macos_notification"

    def send(self, event: NotificationEvent) -> None:
        if platform.system() != "Darwin":
            raise RuntimeError("MacOSNotifier requires macOS")
        safe_title = event.title.replace("\\", "\\\\").replace('"', '\\"')
        safe_message = format_event(event).replace("\\", "\\\\").replace('"', '\\"')
        script = f'display notification "{safe_message}" with title "{safe_title}"'
        subprocess.run(["osascript", "-e", script], check=True)
