"""Exercise the packaged OS entrypoint without Telegram, websites or credentials."""

from __future__ import annotations

import argparse
import platform
import stat
import subprocess
import tempfile
import tomllib
import zipfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-dir", type=Path, default=Path("dist/releases"))
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    version = tomllib.loads((repo / "pyproject.toml").read_text())["project"]["version"]
    system = {"Windows": "windows", "Darwin": "macos", "Linux": "linux"}[platform.system()]
    archive = args.archive_dir / f"deal-watcher-{system}-v{version}-alpha.zip"
    with tempfile.TemporaryDirectory(prefix="Deal Watcher package ") as temporary:
        with zipfile.ZipFile(archive) as package:
            package.extractall(temporary)
            if system != "windows":
                for member in package.infolist():
                    Path(temporary, member.filename).chmod(stat.S_IMODE(member.external_attr >> 16))
        root = Path(temporary) / "deal-watcher"
        if system == "windows":
            # /s requires an outer quoted command when the executable path contains spaces.
            command = ["cmd.exe", "/d", "/s", "/c", f'""{root / "Baslat-Windows.cmd"}" -Check"']
        else:
            entry = "Baslat-macOS.command" if system == "macos" else "Baslat-Linux.sh"
            command = [str(root / entry), "--check"]
        subprocess.run(command, cwd=root, check=True, timeout=180)
        assert not (root / ".env").exists(), "Offline launcher unexpectedly saved credentials"
        print(f"{system}: ZIP entrypoint with spaced path passed; no Telegram calls or credentials")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
