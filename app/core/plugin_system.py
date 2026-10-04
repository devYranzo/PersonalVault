from app.core.config import PLUGIN_REGISTRY_FILE
from app.core.plugins import PluginManager, PluginRegistry


def create_plugin_manager() -> PluginManager:
    registry = PluginRegistry(
        PLUGIN_REGISTRY_FILE
    )

    manager = PluginManager(
        registry=registry
    )

    manager.discover_plugins()
    manager.restore_enabled_plugins()

    return manager