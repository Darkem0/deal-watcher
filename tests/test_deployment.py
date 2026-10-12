import importlib.util
import plistlib
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/manage_service.py"
spec = importlib.util.spec_from_file_location("service_manager", SCRIPT)
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)


def test_macos_uses_runtime_cli_and_preserves_special_paths() -> None:
    root = Path("/example/Projects & spaces/deal-watcher")
    data = plistlib.loads(manager.macos_plist(root))
    assert data["ProgramArguments"] == [
        str(root / ".venv/bin/python"),
        "-m",
        "deal_watcher.cli",
        "run",
    ]
    assert data["WorkingDirectory"] == str(root)
    assert "EnvironmentVariables" not in data


def test_linux_service_quotes_paths_and_escapes_specifiers() -> None:
    unit = manager.linux_unit(Path('/example/project with 100% "quotes"'))
    assert '100%% \\"quotes\\"' in unit
    assert "-m deal_watcher.cli run" in unit
    assert "Restart=on-failure" in unit


def test_linux_service_rejects_newline_injection() -> None:
    with pytest.raises(ValueError):
        manager.linux_unit(Path("/example\nExecStart=bad"))
