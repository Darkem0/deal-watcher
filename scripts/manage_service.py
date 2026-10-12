"""Install a current-user service. Run after uv sync and local .env setup."""

from __future__ import annotations

import argparse
import os
import platform
import plistlib
import subprocess
from pathlib import Path

LABEL = "com.dealwatcher.agent"


def linux_unit(root: Path) -> str:
    def quote(value: str) -> str:
        if "\n" in value or "\r" in value:
            raise ValueError("Project path must not contain newlines")
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("%", "%%") + '"'

    return (
        "[Unit]\nDescription=Deal Watcher forum and Telegram monitor\n\n"
        "[Service]\nType=simple\n"
        f"WorkingDirectory={quote(str(root))}\n"
        f"ExecStart={quote(str(root / '.venv/bin/python'))} -m deal_watcher.cli run\n"
        "Restart=on-failure\nRestartSec=30\n\n[Install]\nWantedBy=default.target\n"
    )


def macos_plist(root: Path) -> bytes:
    return plistlib.dumps(
        {
            "Label": LABEL,
            "ProgramArguments": [str(root / ".venv/bin/python"), "-m", "deal_watcher.cli", "run"],
            "WorkingDirectory": str(root),
            "RunAtLoad": True,
            "KeepAlive": {"SuccessfulExit": False},
            "ThrottleInterval": 30,
            "StandardOutPath": str(root / "logs/launchd.out.log"),
            "StandardErrorPath": str(root / "logs/launchd.err.log"),
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "uninstall"))
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--platform", choices=("linux", "macos"))
    parser.add_argument("--dry-run", action="store_true", help="Render only; no service changes")
    args = parser.parse_args()
    target_os = args.platform or {"Linux": "linux", "Darwin": "macos"}.get(platform.system())
    if target_os is None:
        parser.error("Windows için install_windows_task.ps1 kullanın")
    root = args.project_root.resolve()
    if target_os == "linux":
        target = Path.home() / ".config/systemd/user/deal-watcher.service"
        content = linux_unit(root).encode()
    else:
        target = Path.home() / f"Library/LaunchAgents/{LABEL}.plist"
        content = macos_plist(root)
    if args.dry_run:
        print(content.decode())
        return 0
    expected_os = "Linux" if target_os == "linux" else "Darwin"
    if platform.system() != expected_os:
        parser.error("Kurulum hedef işletim sisteminde çalıştırılmalıdır")
    if args.action == "install":
        if target.exists():
            parser.error("Servis dosyası zaten var; güncellemeden önce uninstall kullanın")
        python = root / ".venv/bin/python"
        if not python.is_file() or not (root / ".env").is_file():
            parser.error("Önce uv sync ve deal-watcher-setup ile kurulumu tamamlayın")
        subprocess.run(
            [str(python), "-m", "deal_watcher.cli", "validate-config"], cwd=root, check=True
        )
        (root / "logs").mkdir(exist_ok=True)
        (root / "data").mkdir(exist_ok=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(content)
        if target_os == "linux":
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "--user", "enable", "--now", target.name], check=True)
        else:
            subprocess.run(
                ["launchctl", "bootstrap", f"gui/{os.getuid()}", str(target)], check=True
            )
        print(f"Kuruldu: {target}")
    elif target.exists():
        if target_os == "linux":
            subprocess.run(["systemctl", "--user", "disable", "--now", target.name], check=True)
        else:
            subprocess.run(["launchctl", "bootout", f"gui/{os.getuid()}", str(target)], check=False)
        target.unlink()
        if target_os == "linux":
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        print("Servis kaldırıldı; .env, veritabanı ve loglar korundu.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
