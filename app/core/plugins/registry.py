import json
from pathlib import Path


class PluginRegistry:
    """
    Guarda la configuración persistente de los plugins.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._enabled_plugins: set[str] = set()

        self._load()

    def is_enabled(self, plugin_id: str) -> bool:
        """
        Comprueba si un plugin está configurado como activo.
        """

        return plugin_id in self._enabled_plugins

    def enable(self, plugin_id: str) -> None:
        """
        Marca un plugin como activo y guarda la configuración.
        """

        self._enabled_plugins.add(plugin_id)
        self._save()

    def disable(self, plugin_id: str) -> None:
        """
        Marca un plugin como desactivado y guarda la configuración.
        """

        self._enabled_plugins.discard(plugin_id)
        self._save()

    def get_enabled_plugins(self) -> set[str]:
        """
        Devuelve los IDs de los plugins configurados como activos.
        """

        return set(self._enabled_plugins)

    def _load(self) -> None:
        """
        Carga la configuración desde disco.
        """

        if not self._path.exists():
            return

        try:
            data = json.loads(
                self._path.read_text(encoding="utf-8")
            )

        except (OSError, json.JSONDecodeError):
            self._enabled_plugins = set()
            return

        enabled_plugins = data.get("enabled_plugins", [])

        if not isinstance(enabled_plugins, list):
            self._enabled_plugins = set()
            return

        self._enabled_plugins = {
            plugin_id
            for plugin_id in enabled_plugins
            if isinstance(plugin_id, str)
        }

    def _save(self) -> None:
        """
        Guarda la configuración en disco.
        """

        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "enabled_plugins": sorted(
                self._enabled_plugins
            )
        }

        self._path.write_text(
            json.dumps(
                data,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )