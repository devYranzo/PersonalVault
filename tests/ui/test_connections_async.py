import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.models import Assignment
from app.core.plugins import Plugin
from app.core.plugins.manager import PluginManager
from app.core.plugins.registry import PluginRegistry
from app.core.plugins.types import PluginCapabilities, PluginInfo
from app.infrastructure.database.base import Base
from app.infrastructure.database.models import (
    AssignmentModel,
    CourseModel,
    DocumentModel,
    EventModel,
)
from app.services import SyncResult
from app.ui.pages.settings.connections_page import ConnectionsPage
from app.ui.workers import Worker

PLUGIN_ID = "slow"


class SlowPlugin(Plugin):
    """Plugin que se queda esperando hasta que el test lo libere."""

    def __init__(self) -> None:
        self.release = threading.Event()
        self.connected = False
        self.fail_connect = False
        self.threads: dict[str, threading.Thread] = {}
        self.get_assignments_calls = 0

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            id=PLUGIN_ID,
            name="Slow",
            version="1.0.0",
            description="Plugin de tests.",
            capabilities=[PluginCapabilities.ASSIGNMENTS],
        )

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def requires_connection(self) -> bool:
        return True

    def is_connected(self) -> bool:
        return self.connected

    def connect(self) -> None:
        self.threads["connect"] = threading.current_thread()
        self.release.wait(timeout=5)

        if self.fail_connect:
            raise RuntimeError("OAuth cancelado")

        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def get_assignments(self) -> list[Assignment]:
        self.threads["sync"] = threading.current_thread()
        self.get_assignments_calls += 1
        self.release.wait(timeout=5)

        return [
            Assignment(
                id="x",
                title="Tarea remota",
                source=PLUGIN_ID,
                external_id="remote-1",
            ),
        ]


@dataclass
class Harness:
    """La página, el plugin y lo que la página ha intentado mostrar."""

    page: ConnectionsPage
    plugin: SlowPlugin
    session_factory: sessionmaker[Session]
    sync_results: list[tuple[SyncResult, threading.Thread]] = field(
        default_factory=list,
    )
    errors: list[tuple[str, str, threading.Thread]] = field(
        default_factory=list,
    )

    def button(self, text: str) -> QPushButton:
        # Las tarjetas se reconstruyen al refrescar: se busca cada vez.
        for candidate in self.page.findChildren(QPushButton):
            if candidate.text() == text:
                return candidate

        raise AssertionError(f"No hay ningún botón «{text}»")

    def click(self, qtbot, text: str) -> None:
        qtbot.mouseClick(self.button(text), Qt.MouseButton.LeftButton)


@pytest.fixture
def ui(qtbot, tmp_path: Path, monkeypatch) -> Iterator[Harness]:
    engine = create_engine(f"sqlite:///{tmp_path / 'ui.db'}")

    Base.metadata.create_all(
        engine,
        tables=[
            CourseModel.__table__,
            AssignmentModel.__table__,
            EventModel.__table__,
            DocumentModel.__table__,
        ],
    )

    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    plugin = SlowPlugin()
    manager = PluginManager(PluginRegistry(tmp_path / "plugins.json"))
    manager.register(plugin)
    manager.enable(PLUGIN_ID)

    page = ConnectionsPage(manager, session_factory=factory)
    qtbot.addWidget(page)

    harness = Harness(page=page, plugin=plugin, session_factory=factory)

    # Sin diálogos modales: se anotan y se registra en qué hilo se llaman.
    monkeypatch.setattr(
        page,
        "_show_sync_result",
        lambda name, result: harness.sync_results.append(
            (result, threading.current_thread()),
        ),
    )
    monkeypatch.setattr(
        page,
        "_show_error",
        lambda title, message: harness.errors.append(
            (title, message, threading.current_thread()),
        ),
    )

    yield harness

    plugin.release.set()
    page.wait_for_background_jobs()
    engine.dispose()


def test_sync_does_not_block_the_ui_thread(qtbot, ui: Harness) -> None:
    ui.plugin.connected = True
    ui.page.refresh_plugins()

    ui.click(qtbot, "Sincronizar")  # vuelve al instante aunque el plugin espere

    assert ui.page.is_busy(PLUGIN_ID)
    assert ui.sync_results == []

    ui.plugin.release.set()
    qtbot.waitUntil(lambda: bool(ui.sync_results), timeout=5000)

    result, callback_thread = ui.sync_results[0]

    assert ui.plugin.threads["sync"] is not threading.main_thread()
    assert callback_thread is threading.main_thread()
    assert result.assignments == 1
    assert not ui.page.is_busy(PLUGIN_ID)

    with ui.session_factory() as session:
        assert session.query(AssignmentModel).count() == 1


def test_connect_runs_in_background_and_updates_state(
    qtbot,
    ui: Harness,
) -> None:
    ui.click(qtbot, "Conectar")

    assert ui.page.is_busy(PLUGIN_ID)
    assert not ui.plugin.is_connected()

    ui.plugin.release.set()
    qtbot.waitUntil(lambda: not ui.page.is_busy(PLUGIN_ID), timeout=5000)

    assert ui.plugin.threads["connect"] is not threading.main_thread()
    assert ui.plugin.is_connected()
    assert ui.errors == []
    assert ui.button("Desconectar").isEnabled()


def test_failure_is_reported_on_the_ui_thread(qtbot, ui: Harness) -> None:
    ui.plugin.fail_connect = True
    ui.plugin.release.set()

    ui.click(qtbot, "Conectar")
    qtbot.waitUntil(lambda: bool(ui.errors), timeout=5000)

    title, message, thread = ui.errors[0]

    assert title == "No se pudo cambiar el estado de conexión."
    assert message == "OAuth cancelado"
    assert thread is threading.main_thread()
    assert not ui.page.is_busy(PLUGIN_ID)
    assert not ui.plugin.is_connected()


def test_buttons_are_disabled_while_the_plugin_is_busy(
    qtbot,
    ui: Harness,
) -> None:
    ui.plugin.connected = True
    ui.page.refresh_plugins()

    ui.click(qtbot, "Sincronizar")

    assert not ui.button("Sincronizar").isEnabled()
    assert not ui.button("Desconectar").isEnabled()
    assert not ui.button("Desactivar").isEnabled()

    # Clics durante la operación: no hacen nada (ni abren el diálogo de
    # desactivar, que bloquearía el test).
    ui.click(qtbot, "Sincronizar")
    ui.click(qtbot, "Desconectar")
    ui.click(qtbot, "Desactivar")

    ui.plugin.release.set()
    qtbot.waitUntil(lambda: bool(ui.sync_results), timeout=5000)
    qtbot.waitUntil(lambda: not ui.page.is_busy(PLUGIN_ID), timeout=5000)

    assert ui.plugin.get_assignments_calls == 1
    assert ui.plugin.is_connected()
    assert ui.button("Sincronizar").isEnabled()


def test_worker_reports_success_and_failure(qtbot) -> None:
    ok = Worker(1, lambda: 42)

    with qtbot.waitSignal(ok.signals.succeeded, timeout=5000) as blocker:
        ok.run()

    assert blocker.args == [1, 42]

    def boom() -> None:
        raise ValueError("fallo")

    bad = Worker(2, boom)

    with qtbot.waitSignal(bad.signals.failed, timeout=5000) as blocker:
        bad.run()

    assert blocker.args[0] == 2
    assert str(blocker.args[1]) == "fallo"