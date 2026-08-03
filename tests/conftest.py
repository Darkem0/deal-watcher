from pathlib import Path

import pytest

from deal_watcher.models.config import AppConfig, load_config

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def app_config() -> AppConfig:
    return load_config(ROOT / "config")
