from pathlib import Path

import pytest

from app.core.plugins.manager import PluginManager
from app.core.plugins.registry import PluginRegistry


@pytest.fixture
def registry(tmp_path: Path) -> PluginRegistry:
    return PluginRegistry(tmp_path / "plugins.json")


@pytest.fixture
def manager(registry: PluginRegistry) -> PluginManager:
    return PluginManager(registry)