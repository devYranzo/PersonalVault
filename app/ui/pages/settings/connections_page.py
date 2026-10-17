from collections.abc import Callable
from dataclasses import dataclass
from itertools import count
from typing import Any

from PySide6.QtCore import Qt, QThreadPool, QTimer, Slot
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from sqlalchemy.orm import Session

from app.core.plugins import (
    ManagedPlugin,
    PluginManager,
    PluginStatus,
)
from app.infrastructure.database.database import SessionLocal
from app.services import PluginDataService, SyncResult, SyncService
from app.ui.layouts.flow_layout import FlowLayout, FlowScrollArea
from app.ui.resources.icons import IconButton, svg_pixmap
from app.ui.workers import Worker

CARD_WIDTH = 420

# capability.value -> (icono, etiqueta)
CAPABILITIES = {
    "courses": ("school", "Cursos"),
    "assignments": ("tasks", "Tareas"),
    "events": ("event", "Eventos"),
    "documents": ("description", "Documentos"),
}

STATUS_LABELS = {
    PluginStatus.DISCOVERED: ("Descubierto", "discovered"),
    PluginStatus.ENABLED: ("Activo", "enabled"),
    PluginStatus.DISABLED: ("Desactivado", "disabled"),
    PluginStatus.ERROR: ("Error", "error"),
}

@dataclass
class _BackgroundJob:
    plugin_id: str
    worker: Worker
    error_title: str
    on_success: Callable[[Any], None] | None

class ConnectionsPage(QWidget):
    def __init__(self, plugin_manager: PluginManager, session_factory: Callable[[], Session] = SessionLocal,) -> None:
        super().__init__()

        self.plugin_manager = plugin_manager
        self._session_factory = session_factory
        self.plugin_cards: dict[str, QFrame] = {}

        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(1)

        self._job_ids = count(1)
        self._jobs: dict[int, _BackgroundJob] = {}

        self._busy: dict[str, str] = {}

        self._setup_ui()
        self.refresh_plugins()

    # ------------------------------------------------------------------ UI

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(8)

        self.summary_label = QLabel()
        self.summary_label.setObjectName("pageSummary")

        root_layout.addWidget(self.summary_label)
        root_layout.addSpacing(12)

        # Rejilla dinámica: tarjetas de ancho fijo que saltan de fila
        self.plugins_container = QWidget()
        self.plugins_container.setObjectName("pageContainer")

        self.plugins_layout = FlowLayout(
            self.plugins_container,
            h_spacing=16,
            v_spacing=16,
        )
        self.plugins_layout.setContentsMargins(0, 0, 8, 8)

        self.scroll = FlowScrollArea()
        self.scroll.setObjectName("pageScroll")
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

        busy_text = self._busy.get(info.id)

        if busy_text:
            status_text, status_state = busy_text, "discovered"

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

        if busy_text:
            connect_button.setEnabled(False)
            connect_button.setToolTip("Hay una operación en curso")

        buttons.addWidget(connect_button)

        if enabled:
            sync_button = IconButton("Sincronizar", "sync")
            sync_button.clicked.connect(
                lambda checked=False, pid=info.id: self._sync_plugin(pid),
            )

            # Un plugin que necesita autenticación no puede sincronizar
            # hasta que esté conectado.
            if plugin.requires_connection() and not connected:
                sync_button.setEnabled(False)
                sync_button.setToolTip("Conecta el plugin antes de sincronizar")

            if busy_text:
                sync_button.setEnabled(False)
                sync_button.setToolTip("Hay una operación en curso")

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

        if busy_text:
            toggle_button.setEnabled(False)
            toggle_button.setToolTip("Hay una operación en curso")

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
        if plugin_id in self._busy:
            return
        
        if self.plugin_manager.is_enabled(plugin_id):
            if not self._disable_plugin(plugin_id):
                return
        else:
            try:
                self.plugin_manager.enable(plugin_id)
            except Exception as exc:
                self._show_error("No se pudo activar el plugin.", str(exc))
                return

        self.refresh_plugins()

    def _disable_plugin(self, plugin_id: str) -> bool:
        """
        Desactiva un plugin y elimina todos sus datos sincronizados.

        Antes de hacer nada pide confirmación al usuario. Primero se
        borran los datos y después se desactiva el plugin, de modo que
        si el borrado falla no queden datos huérfanos de un plugin
        desactivado.

        Devuelve False si el usuario cancela o si el borrado falla
        (en ambos casos no se ha cambiado nada).
        """
        plugin_name = self.plugin_manager.get_plugin(plugin_id).info.name

        if not self._confirm_disable(plugin_name):
            return False

        try:
            with self._session_factory() as session:
                PluginDataService(session).purge(plugin_id)
        except Exception as exc:
            self._show_error(
                "No se pudieron eliminar los datos del plugin.",
                str(exc),
            )
            return False

        try:
            self.plugin_manager.disable(plugin_id)
        except Exception as exc:
            # Los datos ya se han eliminado: se refresca para mostrar
            # el estado real del plugin (error) antes de avisar.
            self.refresh_plugins()
            self._show_error("No se pudo desactivar el plugin.", str(exc))
            return False

        return True

    def _confirm_disable(self, plugin_name: str) -> bool:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("Desactivar plugin")
        box.setText(f"¿Desactivar «{plugin_name}»?")
        box.setInformativeText(
            "Se eliminarán de Personal Vault todos los datos que este "
            "plugin ha sincronizado: cursos, tareas, eventos y documentos.\n\n"
            "Tus tareas locales no se verán afectadas. Si vuelves a "
            "activar el plugin, tendrás que sincronizar de nuevo."
        )

        confirm_button = box.addButton(
            "Desactivar y eliminar datos",
            QMessageBox.ButtonRole.DestructiveRole,
        )
        cancel_button = box.addButton(
            "Cancelar",
            QMessageBox.ButtonRole.RejectRole,
        )
        box.setDefaultButton(cancel_button)
        box.setEscapeButton(cancel_button)

        box.exec()

        return box.clickedButton() is confirm_button

    def _toggle_connection(self, plugin_id: str) -> None:
        if plugin_id in self._busy:
            return

        plugin = self.plugin_manager.get_plugin(plugin_id)

        if plugin is None:
            return

        if plugin.is_connected():
            label, job = "Desconectando…", plugin.disconnect
        else:
            if not self.plugin_manager.is_enabled(plugin_id):
                self._show_error(
                    "Plugin no activo",
                    "Activa el plugin antes de conectarlo.",
                )
                return

            label, job = "Conectando…", plugin.connect

        self._run_in_background(
            plugin_id,
            label,
            job,
            error_title="No se pudo cambiar el estado de conexión.",
        )

    def _sync_plugin(self, plugin_id: str) -> None:
        if plugin_id in self._busy:
            return

        plugin = self.plugin_manager.get_plugin(plugin_id)

        if plugin is None:
            return

        if not self.plugin_manager.is_enabled(plugin_id):
            self._show_error(
                "Plugin no activo",
                "Activa el plugin antes de sincronizarlo.",
            )
            return

        if plugin.requires_connection() and not plugin.is_connected():
            self._show_error(
                "Plugin no conectado",
                "Conecta el plugin con su servicio externo antes de "
                "sincronizarlo.",
            )
            return

        def job() -> SyncResult:
            # Se ejecuta en el hilo de trabajo: la sesión se crea y se
            # cierra aquí dentro, nunca se comparte con la interfaz.
            with self._session_factory() as session:
                return SyncService(session=session, plugin=plugin).sync()

        self._run_in_background(
            plugin_id,
            "Sincronizando…",
            job,
            error_title="No se pudo sincronizar el plugin.",
            on_success=lambda result: self._show_sync_result(
                plugin.info.name,
                result,
            ),
        )

    # ----------------------------------------------------- segundo plano

    def is_busy(self, plugin_id: str) -> bool:
        """True mientras el plugin conecta, desconecta o sincroniza."""
        return plugin_id in self._busy

    def wait_for_background_jobs(self, timeout_ms: int = 5000) -> bool:
        """Espera a que acaben las operaciones en segundo plano."""
        return self._pool.waitForDone(timeout_ms)

    def _run_in_background(
        self,
        plugin_id: str,
        label: str,
        job: Callable[[], Any],
        *,
        error_title: str,
        on_success: Callable[[Any], None] | None = None,
    ) -> None:
        """
        Ejecuta `job` en un hilo y marca el plugin como ocupado.

        `on_success` y el mensaje de error se ejecutan de nuevo en el
        hilo de la interfaz. Mientras el plugin está ocupado no se puede
        activar, desactivar, conectar ni sincronizar.
        """
        job_id = next(self._job_ids)

        worker = Worker(job_id, job)
        worker.signals.succeeded.connect(self._on_job_succeeded)
        worker.signals.failed.connect(self._on_job_failed)

        self._jobs[job_id] = _BackgroundJob(
            plugin_id=plugin_id,
            worker=worker,
            error_title=error_title,
            on_success=on_success,
        )
        self._busy[plugin_id] = label

        self.refresh_plugins()

        self._pool.start(worker)

    @Slot(int, object)
    def _on_job_succeeded(self, job_id: int, result: object) -> None:
        job = self._finish_job(job_id)

        if job is not None and job.on_success is not None:
            job.on_success(result)

    @Slot(int, object)
    def _on_job_failed(self, job_id: int, error: object) -> None:
        job = self._finish_job(job_id)

        if job is not None:
            self._show_error(job.error_title, str(error))

    def _finish_job(self, job_id: int) -> _BackgroundJob | None:
        job = self._jobs.pop(job_id, None)

        if job is None:
            return None

        self._busy.pop(job.plugin_id, None)
        self.refresh_plugins()

        return job

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
                + (
                    f"\nEliminados por ya no existir en el origen: {result.removed}"
                    if result.removed
                    else ""
                )
            ),
        )

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)