import importlib
import pkgutil
from dataclasses import dataclass
from types import ModuleType

from app.core.plugins.base import Plugin
from app.core.plugins.types import PluginStatus


@dataclass
class ManagedPlugin:
    plugin: Plugin
    status: PluginStatus = PluginStatus.DISCOVERED
    error: str | None = None


class PluginManager:
    def __init__(self) -> None:
        self._plugins: dict[str, ManagedPlugin] = {}

    def discover_plugins(self) -> list[Plugin]:
        """
        Busca automáticamente plugins dentro de app.plugins.
        Devuelve los plugins encontrados.
        """

        discovered: list[Plugin] = []

        import app.plugins

        package: ModuleType = app.plugins

        for module_info in pkgutil.iter_modules(
            package.__path__,
            package.__name__ + ".",
        ):
            module = importlib.import_module(module_info.name)

            plugin = self._find_plugin_in_module(module)

            if plugin is None:
                continue

            self.register(plugin)
            discovered.append(plugin)

        return discovered

    def _find_plugin_in_module(
        self,
        module: ModuleType,
    ) -> Plugin | None:
        """
        Busca una instancia de Plugin dentro de un módulo.
        """

        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)

            if not isinstance(attribute, type):
                continue

            if not issubclass(attribute, Plugin):
                continue

            if attribute is Plugin:
                continue

            return attribute()

        return None

    def register(self, plugin: Plugin) -> None:
        """
        Registra un plugin en el manager.
        """

        plugin_id = plugin.info.id

        if plugin_id in self._plugins:
            raise ValueError(
                f"El plugin '{plugin_id}' ya está registrado."
            )

        self._plugins[plugin_id] = ManagedPlugin(
            plugin=plugin,
        )

    def unregister(self, plugin_id: str) -> None:
        """
        Elimina un plugin del manager.

        Si estaba activo, primero lo desactiva.
        """

        if plugin_id not in self._plugins:
            return

        managed_plugin = self._plugins[plugin_id]

        if managed_plugin.status == PluginStatus.ENABLED:
            self.disable(plugin_id)

        del self._plugins[plugin_id]

    def enable(self, plugin_id: str) -> None:
        """
        Inicializa y activa un plugin.
        """

        managed_plugin = self._get_managed_plugin(plugin_id)

        if managed_plugin.status == PluginStatus.ENABLED:
            return

        try:
            managed_plugin.plugin.initialize()
            managed_plugin.status = PluginStatus.ENABLED
            managed_plugin.error = None

        except Exception as exc:
            managed_plugin.status = PluginStatus.ERROR
            managed_plugin.error = str(exc)

            raise

    def disable(self, plugin_id: str) -> None:
        """
        Desactiva un plugin.
        """

        managed_plugin = self._get_managed_plugin(plugin_id)

        if managed_plugin.status != PluginStatus.ENABLED:
            managed_plugin.status = PluginStatus.DISABLED
            return

        try:
            managed_plugin.plugin.shutdown()
            managed_plugin.status = PluginStatus.DISABLED
            managed_plugin.error = None

        except Exception as exc:
            managed_plugin.status = PluginStatus.ERROR
            managed_plugin.error = str(exc)

            raise

    def get_plugin(self, plugin_id: str) -> Plugin:
        """
        Devuelve una instancia de plugin por ID.
        """

        return self._get_managed_plugin(plugin_id).plugin

    def get_plugins(self) -> list[ManagedPlugin]:
        """
        Devuelve todos los plugins registrados.
        """

        return list(self._plugins.values())

    def get_enabled_plugins(self) -> list[ManagedPlugin]:
        """
        Devuelve únicamente los plugins activos.
        """

        return [
            managed_plugin
            for managed_plugin in self._plugins.values()
            if managed_plugin.status == PluginStatus.ENABLED
        ]

    def is_enabled(self, plugin_id: str) -> bool:
        """
        Comprueba si un plugin está activo.
        """

        managed_plugin = self._get_managed_plugin(plugin_id)

        return managed_plugin.status == PluginStatus.ENABLED

    def shutdown_all(self) -> None:
        """
        Desactiva todos los plugins activos.
        """

        for plugin_id in list(self._plugins):
            managed_plugin = self._plugins[plugin_id]

            if managed_plugin.status != PluginStatus.ENABLED:
                continue

            self.disable(plugin_id)

    def _get_managed_plugin(self, plugin_id: str) -> ManagedPlugin:
        """
        Obtiene un plugin gestionado o lanza un error.
        """

        try:
            return self._plugins[plugin_id]
        except KeyError as exc:
            raise KeyError(
                f"No existe ningún plugin con ID '{plugin_id}'."
            ) from exc