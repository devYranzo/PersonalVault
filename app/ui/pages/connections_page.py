from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.core.plugins import (
    ManagedPlugin,
    PluginManager,
    PluginStatus,
)


class ConnectionsPage(QWidget):
    def __init__(self, plugin_manager: PluginManager) -> None:
        super().__init__()

        self.plugin_manager = plugin_manager
        self.plugin_cards: dict[str, QFrame] = {}

        self._setup_ui()
        self.refresh_plugins()

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(40, 40, 40, 40)
        root_layout.setSpacing(20)

        title = QLabel("Conexiones")
        title.setObjectName("pageTitle")

        description = QLabel(
            "Gestiona los plugins y conecta Personal Vault "
            "con servicios externos."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        root_layout.addWidget(title)
        root_layout.addWidget(description)

        self.plugins_container = QWidget()
        self.plugins_layout = QVBoxLayout(self.plugins_container)
        self.plugins_layout.setContentsMargins(0, 10, 0, 0)
        self.plugins_layout.setSpacing(12)

        root_layout.addWidget(self.plugins_container)
        root_layout.addStretch()

    def refresh_plugins(self) -> None:
        self._clear_plugin_cards()

        plugins = self.plugin_manager.get_plugins()

        if not plugins:
            empty_label = QLabel(
                "No hay plugins disponibles."
            )
            empty_label.setObjectName("pageDescription")
            self.plugins_layout.addWidget(empty_label)
            return

        for managed_plugin in plugins:
            card = self._create_plugin_card(managed_plugin)
            self.plugins_layout.addWidget(card)

    def _clear_plugin_cards(self) -> None:
        self.plugin_cards.clear()

        while self.plugins_layout.count():
            item = self.plugins_layout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def _create_plugin_card(
        self,
        managed_plugin: ManagedPlugin,
    ) -> QFrame:
        plugin = managed_plugin.plugin
        info = plugin.info

        card = QFrame()
        card.setObjectName("pluginCard")
        card.setFrameShape(QFrame.Shape.StyledPanel)

        self.plugin_cards[info.id] = card

        root_layout = QVBoxLayout(card)
        root_layout.setContentsMargins(20, 18, 20, 18)
        root_layout.setSpacing(10)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        name_layout = QVBoxLayout()
        name_layout.setSpacing(2)

        name_label = QLabel(info.name)
        name_label.setObjectName("pluginName")

        version_label = QLabel(f"Versión {info.version}")
        version_label.setObjectName("pluginVersion")

        name_layout.addWidget(name_label)
        name_layout.addWidget(version_label)

        header_layout.addLayout(name_layout)
        header_layout.addStretch()

        status_label = self._create_status_label(managed_plugin)
        header_layout.addWidget(status_label)

        root_layout.addLayout(header_layout)

        description_label = QLabel(info.description)
        description_label.setObjectName("pluginDescription")
        description_label.setWordWrap(True)

        root_layout.addWidget(description_label)

        capabilities_text = self._format_capabilities(
            info.capabilities
        )

        capabilities_label = QLabel(
            f"Capacidades: {capabilities_text}"
        )
        capabilities_label.setObjectName("pluginCapabilities")
        capabilities_label.setWordWrap(True)

        root_layout.addWidget(capabilities_label)

        if managed_plugin.error:
            error_label = QLabel(
                f"Error: {managed_plugin.error}"
            )
            error_label.setObjectName("pluginError")
            error_label.setWordWrap(True)

            root_layout.addWidget(error_label)

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)

        enabled = self.plugin_manager.is_enabled(info.id)

        toggle_button = QPushButton(
            "Desactivar" if enabled else "Activar"
        )
        toggle_button.setObjectName("pluginActionButton")
        toggle_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        toggle_button.clicked.connect(
            lambda checked=False, plugin_id=info.id: (
                self._toggle_plugin(plugin_id)
            )
        )

        buttons_layout.addWidget(toggle_button)

        connect_button = QPushButton(
            "Conectar"
            if not plugin.is_connected()
            else "Desconectar"
        )
        connect_button.setObjectName("pluginConnectButton")
        connect_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        connect_button.clicked.connect(
            lambda checked=False, plugin_id=info.id: (
                self._toggle_connection(plugin_id)
            )
        )

        buttons_layout.addWidget(connect_button)

        buttons_layout.addStretch()

        root_layout.addLayout(buttons_layout)

        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum,
        )

        return card

    def _create_status_label(
        self,
        managed_plugin: ManagedPlugin,
    ) -> QLabel:
        status_text = {
            PluginStatus.DISCOVERED: "Descubierto",
            PluginStatus.ENABLED: "Activo",
            PluginStatus.DISABLED: "Desactivado",
            PluginStatus.ERROR: "Error",
        }.get(
            managed_plugin.status,
            "Desconocido",
        )

        label = QLabel(status_text)
        label.setObjectName("pluginStatus")

        return label

    def _format_capabilities(self, capabilities) -> str:
        labels = {
            "courses": "Cursos",
            "assignments": "Tareas",
            "events": "Eventos",
            "documents": "Documentos",
        }

        formatted = [
            labels.get(
                capability.value,
                capability.value,
            )
            for capability in capabilities
        ]

        if not formatted:
            return "Ninguna"

        return ", ".join(formatted)

    def _toggle_plugin(self, plugin_id: str) -> None:
        if self.plugin_manager.is_enabled(plugin_id):
            try:
                self.plugin_manager.disable(plugin_id)
            except Exception as exc:
                self._show_error(
                    "No se pudo desactivar el plugin.",
                    str(exc),
                )
                return
        else:
            try:
                self.plugin_manager.enable(plugin_id)
            except Exception as exc:
                self._show_error(
                    "No se pudo activar el plugin.",
                    str(exc),
                )
                return

        self.refresh_plugins()

    def _toggle_connection(self, plugin_id: str) -> None:
        managed_plugin = self.plugin_manager.get_plugin(plugin_id)

        if managed_plugin is None:
            return

        plugin = managed_plugin.plugin

        try:
            if plugin.is_connected():
                plugin.disconnect()
            else:
                if not self.plugin_manager.is_enabled(plugin_id):
                    self._show_error(
                        "Plugin no activo",
                        "Activa el plugin antes de conectarlo.",
                    )
                    return

                plugin.connect()

        except Exception as exc:
            self._show_error(
                "No se pudo cambiar el estado de conexión.",
                str(exc),
            )
            return

        self.refresh_plugins()

    def _show_error(
        self,
        title: str,
        message: str,
    ) -> None:
        QMessageBox.critical(
            self,
            title,
            message,
        )