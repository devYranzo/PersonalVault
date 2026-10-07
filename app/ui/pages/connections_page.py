from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from app.core.plugins import (
    ManagedPlugin,
    PluginManager,
    PluginStatus,
)
from app.infrastructure.database.database import SessionLocal
from app.services import SyncResult, SyncService
from app.ui.layouts.flow_layout import FlowLayout, FlowScrollArea  # ajusta las rutas
from app.ui.resources.icons import IconButton, svg_pixmap

CARD_WIDTH = 420

# capability.value -> (icono, etiqueta)
CAPABILITIES = {
    "courses": ("school", "Cursos"),
    "assignments": ("assignment", "Tareas"),
    "events": ("event", "Eventos"),
    "documents": ("description", "Documentos"),
}

STATUS_LABELS = {
    PluginStatus.DISCOVERED: ("Descubierto", "discovered"),
    PluginStatus.ENABLED: ("Activo", "enabled"),
    PluginStatus.DISABLED: ("Desactivado", "disabled"),
    PluginStatus.ERROR: ("Error", "error"),
}


class ConnectionsPage(QWidget):
    def __init__(self, plugin_manager: PluginManager) -> None:
        super().__init__()

        self.plugin_manager = plugin_manager
        self.plugin_cards: dict[str, QFrame] = {}

        self._setup_ui()
        self.refresh_plugins()

    # ------------------------------------------------------------------ UI

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(40, 40, 40, 30)
        root_layout.setSpacing(8)

        title = QLabel("Conexiones")
        title.setObjectName("pageTitle")

        description = QLabel(
            "Activa los plugins que necesites, conéctalos con tus "
            "servicios externos y sincroniza tus datos en Personal Vault."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        self.summary_label = QLabel()
        self.summary_label.setObjectName("pageSummary")

        root_layout.addWidget(title)
        root_layout.addWidget(description)
        root_layout.addWidget(self.summary_label)
        root_layout.addSpacing(12)

        # Rejilla dinámica: tarjetas de ancho fijo que saltan de fila
        self.plugins_container = QWidget()
        self.plugins_container.setObjectName("pluginsContainer")

        self.plugins_layout = FlowLayout(
            self.plugins_container,
            h_spacing=16,
            v_spacing=16,
        )
        self.plugins_layout.setContentsMargins(0, 0, 8, 8)

        self.scroll = FlowScrollArea()
        self.scroll.setObjectName("pluginsScroll")
        self.scroll.setWidget(self.plugins_container)

        root_layout.addWidget(self.scroll, 1)

    def refresh_plugins(self) -> None:
        self._clear_plugin_cards()

        plugins = self.plugin_manager.get_plugins()

        self._refresh_summary(plugins)

        if not plugins:
            self.plugins_layout.addWidget(self._create_empty_state())
        else:
            for managed_plugin in plugins:
                self.plugins_layout.addWidget(
                    self._create_plugin_card(managed_plugin),
                )

        QTimer.singleShot(0, self.scroll.sync_height)

    def _clear_plugin_cards(self) -> None:
        self.plugin_cards.clear()

        while self.plugins_layout.count():
            item = self.plugins_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    # ------------------------------------------------------------- resumen

    def _refresh_summary(self, plugins: list[ManagedPlugin]) -> None:
        total = len(plugins)
        active = sum(
            1 for p in plugins if self.plugin_manager.is_enabled(p.plugin.info.id)
        )
        connected = sum(1 for p in plugins if p.plugin.is_connected())

        self.summary_label.setText(
            f"{total} plugins  ·  {active} activos  ·  {connected} conectados"
        )

    def _create_empty_state(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("emptyState")
        frame.setFixedWidth(CARD_WIDTH)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(30, 36, 30, 36)
        layout.setSpacing(8)

        icon = QLabel()
        icon.setPixmap(svg_pixmap("extension", "#9ca3af", 40))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("No hay plugins disponibles")
        title.setObjectName("emptyTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        hint = QLabel("Añade un plugin a la carpeta de plugins y reinicia la app.")
        hint.setObjectName("emptyHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)

        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(hint)

        return frame

    # ---------------------------------------------------------------- card

    def _create_plugin_card(self, managed_plugin: ManagedPlugin) -> QFrame:
        plugin = managed_plugin.plugin
        info = plugin.info

        enabled = self.plugin_manager.is_enabled(info.id)
        connected = plugin.is_connected()
        status_text, status_state = STATUS_LABELS.get(
            managed_plugin.status, ("Desconocido", "discovered"),
        )

        card = QFrame()
        card.setObjectName("pluginCard")
        card.setFixedWidth(CARD_WIDTH)

        self.plugin_cards[info.id] = card

        root_layout = QVBoxLayout(card)
        root_layout.setContentsMargins(20, 18, 20, 18)
        root_layout.setSpacing(12)

        # --- Cabecera: avatar + nombre/versión + estado
        header = QHBoxLayout()
        header.setSpacing(12)

        avatar = QLabel(info.name[:1].upper() or "?")
        avatar.setObjectName("pluginAvatar")
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedSize(40, 40)
        header.addWidget(avatar)

        name_layout = QVBoxLayout()
        name_layout.setSpacing(1)

        name_label = QLabel(info.name)
        name_label.setObjectName("pluginName")

        version_label = QLabel(f"Versión {info.version}")
        version_label.setObjectName("pluginVersion")

        name_layout.addWidget(name_label)
        name_layout.addWidget(version_label)
        header.addLayout(name_layout, 1)

        header.addLayout(
            self._create_status(status_text, status_state, connected),
        )

        root_layout.addLayout(header)

        # --- Descripción
        description_label = QLabel(info.description)
        description_label.setObjectName("pluginDescription")
        description_label.setWordWrap(True)
        root_layout.addWidget(description_label)

        # --- Capacidades (fila que salta de línea si no caben)
        root_layout.addWidget(
            self._create_capabilities(self._format_capabilities(info.capabilities)),
        )

        # --- Error
        if managed_plugin.error:
            root_layout.addWidget(self._create_error_box(managed_plugin.error))

        # --- Acciones
        buttons = QHBoxLayout()
        buttons.setSpacing(8)

        connect_button = IconButton(
            "Desconectar" if connected else "Conectar",
            "link_off" if connected else "link",
            variant="secondary" if connected else "primary",
        )
        connect_button.clicked.connect(
            lambda checked=False, pid=info.id: self._toggle_connection(pid),
        )

        if not connected and not enabled:
            connect_button.setEnabled(False)
            connect_button.setToolTip("Activa el plugin antes de conectarlo")

        buttons.addWidget(connect_button)

        if enabled:
            sync_button = IconButton("Sincronizar", "sync")
            sync_button.clicked.connect(
                lambda checked=False, pid=info.id: self._sync_plugin(pid),
            )
            buttons.addWidget(sync_button)

        buttons.addStretch()

        toggle_button = IconButton(
            "Desactivar" if enabled else "Activar",
            "power_settings_new",
            variant="danger" if enabled else "secondary",
        )
        toggle_button.clicked.connect(
            lambda checked=False, pid=info.id: self._toggle_plugin(pid),
        )
        buttons.addWidget(toggle_button)

        root_layout.addLayout(buttons)

        return card

    def _create_status(
        self,
        status_text: str,
        state: str,
        connected: bool,
    ) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(6)

        dot = QLabel()
        dot.setObjectName("statusDot")
        dot.setProperty("state", state)
        dot.setFixedSize(8, 8)

        text = status_text + ("  ·  Conectado" if connected else "")
        label = QLabel(text)
        label.setObjectName("pluginStatus")

        layout.addWidget(dot, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label)

        return layout

    def _create_capabilities(self, capabilities: list[tuple[str, str]]) -> QWidget:
        container = QWidget()

        flow = FlowLayout(container, h_spacing=14, v_spacing=4)
        flow.setContentsMargins(0, 0, 0, 0)

        if not capabilities:
            capabilities = [("extension", "Sin capacidades")]

        for icon_name, text in capabilities:
            item = QWidget()
            layout = QHBoxLayout(item)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(5)

            icon = QLabel()
            icon.setPixmap(svg_pixmap(icon_name, "#7b8390", 16))

            label = QLabel(text)
            label.setObjectName("capabilityText")

            layout.addWidget(icon)
            layout.addWidget(label)

            flow.addWidget(item)

        return container

    def _create_error_box(self, message: str) -> QFrame:
        box = QFrame()
        box.setObjectName("pluginError")

        layout = QHBoxLayout(box)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(8)

        icon = QLabel()
        icon.setPixmap(svg_pixmap("error", "#b91c1c", 18))
        icon.setAlignment(Qt.AlignmentFlag.AlignTop)

        text = QLabel(message)
        text.setObjectName("pluginErrorText")
        text.setWordWrap(True)

        layout.addWidget(icon)
        layout.addWidget(text, 1)

        return box

    def _format_capabilities(self, capabilities) -> list[tuple[str, str]]:
        return [
            CAPABILITIES.get(capability.value, ("extension", capability.value))
            for capability in capabilities
        ]

    # ------------------------------------------------------------- acciones

    def _toggle_plugin(self, plugin_id: str) -> None:
        if self.plugin_manager.is_enabled(plugin_id):
            try:
                self.plugin_manager.disable(plugin_id)
            except Exception as exc:
                self._show_error("No se pudo desactivar el plugin.", str(exc))
                return
        else:
            try:
                self.plugin_manager.enable(plugin_id)
            except Exception as exc:
                self._show_error("No se pudo activar el plugin.", str(exc))
                return

        self.refresh_plugins()

    def _toggle_connection(self, plugin_id: str) -> None:
        plugin = self.plugin_manager.get_plugin(plugin_id)

        if plugin is None:
            return

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

    def _sync_plugin(self, plugin_id: str) -> None:
        plugin = self.plugin_manager.get_plugin(plugin_id)

        if plugin is None:
            return

        if not self.plugin_manager.is_enabled(plugin_id):
            self._show_error(
                "Plugin no activo",
                "Activa el plugin antes de sincronizarlo.",
            )
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        try:
            with SessionLocal() as session:
                service = SyncService(session=session, plugin=plugin)
                result = service.sync()

        except Exception as exc:
            QApplication.restoreOverrideCursor()
            self._show_error("No se pudo sincronizar el plugin.", str(exc))
            return

        QApplication.restoreOverrideCursor()

        self._show_sync_result(plugin.info.name, result)

    def _show_sync_result(self, plugin_name: str, result: SyncResult) -> None:
        QMessageBox.information(
            self,
            "Sincronización completada",
            (
                f"La sincronización de {plugin_name} "
                "ha terminado correctamente.\n\n"
                f"Cursos: {result.courses}\n"
                f"Tareas: {result.assignments}\n"
                f"Eventos: {result.events}\n"
                f"Documentos: {result.documents}\n\n"
                f"Total: {result.total}"
            ),
        )

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)