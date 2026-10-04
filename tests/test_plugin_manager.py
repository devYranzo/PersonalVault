import pytest

from app.core.plugins import PluginStatus
from app.core.plugins.manager import PluginManager
from app.plugins.example import ExamplePlugin


def test_plugin_manager_discovers_example_plugin(manager: PluginManager) -> None:

    plugins = manager.discover_plugins()

    assert len(plugins) == 1
    assert plugins[0].info.id == "example"


def test_plugin_manager_registers_plugin(manager: PluginManager) -> None:

    plugin = ExamplePlugin()

    manager.register(plugin)

    plugins = manager.get_plugins()

    assert len(plugins) == 1
    assert plugins[0].plugin.info.id == "example"
    assert plugins[0].status == PluginStatus.DISCOVERED


def test_plugin_manager_enables_plugin(manager: PluginManager) -> None:

    plugin = ExamplePlugin()

    manager.register(plugin)
    manager.enable("example")

    assert manager.is_enabled("example")
    assert plugin.info.id == "example"


def test_plugin_manager_disables_plugin(manager: PluginManager) -> None:

    plugin = ExamplePlugin()

    manager.register(plugin)
    manager.enable("example")
    manager.disable("example")

    assert not manager.is_enabled("example")


def test_plugin_manager_get_plugin(manager: PluginManager) -> None:

    plugin = ExamplePlugin()

    manager.register(plugin)

    result = manager.get_plugin("example")

    assert result is plugin


def test_plugin_manager_duplicate_plugin(manager: PluginManager) -> None:

    manager.register(ExamplePlugin())

    with pytest.raises(ValueError):
        manager.register(ExamplePlugin())


def test_plugin_manager_unknown_plugin(manager: PluginManager) -> None:

    with pytest.raises(KeyError):
        manager.get_plugin("does-not-exist")


def test_plugin_manager_shutdown_all(manager: PluginManager) -> None:

    manager.register(ExamplePlugin())
    manager.enable("example")

    manager.shutdown_all()

    assert not manager.is_enabled("example")
