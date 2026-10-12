"""Build platform ZIPs from tracked files; never include local runtime state."""

from __future__ import annotations

import argparse
import hashlib
import stat
import subprocess
import tomllib
import zipfile
from pathlib import Path

ENTRYPOINTS = {
    "windows": "Baslat-Windows.cmd",
    "macos": "Baslat-macOS.command",
    "linux": "Baslat-Linux.sh",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("dist/releases"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    version = tomllib.loads((root / "pyproject.toml").read_text())["project"]["version"]
    tag = f"v{version}-alpha"
    names = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
    files = []
    for name in names:
        if not name or name == "AGENTS.md":
            continue
        path = Path(name)
        if path.name == ".gitkeep":
            continue
        if (
            name == ".env"
            or (path.name.startswith(".env.") and path.name != ".env.example")
            or any(part in path.parts for part in (".venv", "venv", "data", "logs", "dist"))
            or path.suffix in (".db", ".sqlite3", ".log")
        ):
            raise RuntimeError(f"Runtime state unexpectedly tracked: {name}")
        files.append(name)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    checksums = []
    for target, entry in ENTRYPOINTS.items():
        archive = args.output_dir / f"deal-watcher-{target}-{tag}.zip"
        if entry not in files:
            raise RuntimeError(
                f"Entrypoint is not tracked: {entry}; stage intended source files first"
            )
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
            for name in files:
                if name in ENTRYPOINTS.values() and name != entry:
                    continue
                source = root / name
                info = zipfile.ZipInfo("deal-watcher/" + name)
                info.create_system = 3
                mode = 0o755 if name.endswith((".sh", ".command")) else 0o644
                info.external_attr = (stat.S_IFREG | mode) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                output.writestr(info, source.read_bytes())
        checksums.append(hashlib.sha256(archive.read_bytes()).hexdigest() + "  " + archive.name)
        print(archive)
    (args.output_dir / "SHA256SUMS.txt").write_text("\n".join(checksums) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
