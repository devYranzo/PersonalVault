from pathlib import Path

from app.core.plugins import PluginRegistry


def test_registry_starts_empty(
    tmp_path: Path,
) -> None:
    registry = PluginRegistry(
        tmp_path / "plugins.json"
    )

    assert registry.get_enabled_plugins() == set()


def test_registry_can_enable_plugin(
    tmp_path: Path,
) -> None:
    registry = PluginRegistry(
        tmp_path / "plugins.json"
    )

    registry.enable("example")

    assert registry.is_enabled("example")


def test_registry_can_disable_plugin(
    tmp_path: Path,
) -> None:
    registry = PluginRegistry(
        tmp_path / "plugins.json"
    )

    registry.enable("example")
    registry.disable("example")

    assert not registry.is_enabled("example")


def test_registry_persists_state(
    tmp_path: Path,
) -> None:
    path = tmp_path / "plugins.json"

    registry = PluginRegistry(path)

    registry.enable("example")

    new_registry = PluginRegistry(path)

    assert new_registry.is_enabled("example")