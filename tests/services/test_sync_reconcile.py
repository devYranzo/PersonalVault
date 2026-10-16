from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.models import Assignment, Course, Event
from app.core.plugins import Plugin
from app.core.plugins.types import PluginCapabilities, PluginInfo
from app.infrastructure.database.base import Base
from app.infrastructure.database.models import (
    AssignmentModel,
    CourseModel,
    DocumentModel,
    EventModel,
)
from app.services import SyncService, TaskService


class MutablePlugin(Plugin):
    """Plugin cuyo contenido remoto se puede cambiar entre sincronizaciones."""

    def __init__(
        self,
        plugin_id: str = "remote",
        capabilities: list[PluginCapabilities] | None = None,
    ) -> None:
        self._plugin_id = plugin_id
        self._capabilities = (
            capabilities
            if capabilities is not None
            else [
                PluginCapabilities.COURSES,
                PluginCapabilities.ASSIGNMENTS,
                PluginCapabilities.EVENTS,
            ]
        )
        self.course_ids: list[str] = []
        self.assignment_ids: list[str] = []
        self.event_ids: list[str] = []
        self.fail = False

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            id=self._plugin_id,
            name="Mutable",
            version="1.0.0",
            description="Plugin de tests.",
            capabilities=self._capabilities,
        )

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def get_courses(self) -> list[Course]:
        return [
            Course(
                id=f"{self._plugin_id}-{ext}",
                name=ext,
                source=self._plugin_id,
                external_id=ext,
            )
            for ext in self.course_ids
        ]

    def get_assignments(self) -> list[Assignment]:
        if self.fail:
            raise RuntimeError("Servicio caído")

        return [
            Assignment(
                id=f"{self._plugin_id}-{ext}",
                title=ext,
                source=self._plugin_id,
                external_id=ext,
            )
            for ext in self.assignment_ids
        ]

    def get_events(self) -> list[Event]:
        return [
            Event(
                id=f"{self._plugin_id}-{ext}",
                title=ext,
                start_at="2026-10-20T10:00:00",
                source=self._plugin_id,
                external_id=ext,
            )
            for ext in self.event_ids
        ]


@pytest.fixture
def session(tmp_path: Path) -> Session:
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", echo=False)

    Base.metadata.create_all(
        engine,
        tables=[
            CourseModel.__table__,
            AssignmentModel.__table__,
            EventModel.__table__,
            DocumentModel.__table__,
        ],
    )

    factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    with factory() as db_session:
        yield db_session

    engine.dispose()


def external_ids(session: Session, model: type, source: str) -> set[str]:
    return {
        row.external_id
        for row in session.query(model).filter_by(source=source).all()
    }


def test_sync_removes_items_that_disappeared_from_source(
    session: Session,
) -> None:
    plugin = MutablePlugin()
    plugin.course_ids = ["c1", "c2"]
    plugin.assignment_ids = ["a1", "a2", "a3"]
    plugin.event_ids = ["e1", "e2"]

    SyncService(session, plugin).sync()

    plugin.course_ids = ["c1"]
    plugin.assignment_ids = ["a2"]
    plugin.event_ids = ["e1", "e2"]

    result = SyncService(session, plugin).sync()

    assert result.removed_courses == 1
    assert result.removed_assignments == 2
    assert result.removed_events == 0
    assert result.removed == 3

    assert external_ids(session, CourseModel, "remote") == {"c1"}
    assert external_ids(session, AssignmentModel, "remote") == {"a2"}
    assert external_ids(session, EventModel, "remote") == {"e1", "e2"}


def test_sync_removes_everything_when_source_is_now_empty(
    session: Session,
) -> None:
    plugin = MutablePlugin()
    plugin.assignment_ids = ["a1", "a2"]
    SyncService(session, plugin).sync()

    plugin.assignment_ids = []
    result = SyncService(session, plugin).sync()

    assert result.removed_assignments == 2
    assert session.query(AssignmentModel).count() == 0


def test_sync_is_idempotent(session: Session) -> None:
    plugin = MutablePlugin()
    plugin.assignment_ids = ["a1", "a2"]

    SyncService(session, plugin).sync()
    result = SyncService(session, plugin).sync()

    assert result.removed == 0
    assert session.query(AssignmentModel).count() == 2


def test_reconcile_does_not_touch_local_or_other_plugins(
    session: Session,
) -> None:
    local = TaskService(session).create(title="Mi tarea")

    other = MutablePlugin(plugin_id="other")
    other.assignment_ids = ["a1"]
    SyncService(session, other).sync()

    plugin = MutablePlugin(plugin_id="remote")
    plugin.assignment_ids = ["a1", "a2"]
    SyncService(session, plugin).sync()

    # `remote` ya no devuelve nada; `other` y la tarea local siguen intactas
    plugin.assignment_ids = []
    SyncService(session, plugin).sync()

    assert external_ids(session, AssignmentModel, "remote") == set()
    assert external_ids(session, AssignmentModel, "other") == {"a1"}
    assert local.id in {task.id for task in TaskService(session).list_tasks()}


def test_reconcile_skips_kinds_the_plugin_does_not_declare(
    session: Session,
) -> None:
    plugin = MutablePlugin(
        capabilities=[PluginCapabilities.ASSIGNMENTS],
    )
    plugin.assignment_ids = ["a1"]
    plugin.event_ids = ["e1"]
    SyncService(session, plugin).sync()

    # Sin EVENTS declarado, que get_events() devuelva [] no borra nada
    plugin.event_ids = []
    result = SyncService(session, plugin).sync()

    assert result.removed_events == 0
    assert external_ids(session, EventModel, "remote") == {"e1"}


def test_failed_sync_does_not_delete_anything(session: Session) -> None:
    plugin = MutablePlugin()
    plugin.course_ids = ["c1", "c2"]
    plugin.assignment_ids = ["a1"]
    SyncService(session, plugin).sync()

    # Los cursos se reconcilian antes de que fallen las tareas:
    # el rollback debe deshacerlo.
    plugin.course_ids = ["c1"]
    plugin.fail = True

    with pytest.raises(RuntimeError):
        SyncService(session, plugin).sync()

    assert external_ids(session, CourseModel, "remote") == {"c1", "c2"}
    assert external_ids(session, AssignmentModel, "remote") == {"a1"}


def test_reconcile_handles_more_items_than_one_batch(
    session: Session,
) -> None:
    plugin = MutablePlugin()
    plugin.assignment_ids = [f"a{i}" for i in range(1200)]
    SyncService(session, plugin).sync()

    plugin.assignment_ids = ["a0"]
    result = SyncService(session, plugin).sync()

    assert result.removed_assignments == 1199
    assert external_ids(session, AssignmentModel, "remote") == {"a0"}