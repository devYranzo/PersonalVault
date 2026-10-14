from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.models import Assignment, Course
from app.core.plugins import Plugin
from app.core.plugins.types import PluginCapabilities, PluginInfo
from app.infrastructure.database.base import Base
from app.infrastructure.database.models import (
    AssignmentModel,
    CourseModel,
    DocumentModel,
    EventModel,
)
from app.services import (
    InvalidSyncSourceError,
    PluginDataService,
    PluginNotConnectedError,
    SyncService,
    TaskService,
)


class FakeExternalPlugin(Plugin):
    """Plugin de tests que puede exigir conexión (como Google Classroom)."""

    def __init__(
        self,
        plugin_id: str = "sample",
        needs_connection: bool = True,
    ) -> None:
        self._plugin_id = plugin_id
        self._needs_connection = needs_connection
        self._connected = False

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            id=self._plugin_id,
            name="Fake",
            version="1.0.0",
            description="Plugin de tests.",
            capabilities=[
                PluginCapabilities.COURSES,
                PluginCapabilities.ASSIGNMENTS,
            ],
        )

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def requires_connection(self) -> bool:
        return self._needs_connection

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def get_courses(self) -> list[Course]:
        return [
            Course(
                id=f"{self._plugin_id}-course-1",
                name="Programación",
                source=self._plugin_id,
                external_id="ext-course-1",
            ),
        ]

    def get_assignments(self) -> list[Assignment]:
        return [
            Assignment(
                id=f"{self._plugin_id}-assignment-1",
                title="Práctica",
                source=self._plugin_id,
                external_id="ext-assignment-1",
            ),
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

    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    with session_factory() as db_session:
        yield db_session

    engine.dispose()


# ---------------------------------------------------------------- conexión


def test_sync_is_blocked_when_plugin_needs_connection(
    session: Session,
) -> None:
    plugin = FakeExternalPlugin(needs_connection=True)

    with pytest.raises(PluginNotConnectedError):
        SyncService(session=session, plugin=plugin).sync()

    assert session.query(CourseModel).count() == 0
    assert session.query(AssignmentModel).count() == 0


def test_sync_works_once_plugin_is_connected(session: Session) -> None:
    plugin = FakeExternalPlugin(needs_connection=True)
    plugin.connect()

    result = SyncService(session=session, plugin=plugin).sync()

    assert result.total == 2
    assert session.query(CourseModel).count() == 1
    assert session.query(AssignmentModel).count() == 1


def test_sync_is_blocked_again_after_disconnecting(session: Session) -> None:
    plugin = FakeExternalPlugin(needs_connection=True)
    plugin.connect()
    plugin.disconnect()

    with pytest.raises(PluginNotConnectedError):
        SyncService(session=session, plugin=plugin).sync()


def test_sync_does_not_need_connection_when_not_required(
    session: Session,
) -> None:
    plugin = FakeExternalPlugin(needs_connection=False)

    result = SyncService(session=session, plugin=plugin).sync()

    assert result.total == 2


# ------------------------------------------------------------ desactivación


def test_purge_removes_only_the_plugin_data(session: Session) -> None:
    for plugin_id in ("sample", "other"):
        plugin = FakeExternalPlugin(plugin_id=plugin_id, needs_connection=False)
        SyncService(session=session, plugin=plugin).sync()

    local = TaskService(session).create(title="Mi tarea")

    result = PluginDataService(session).purge("sample")

    assert result.courses == 1
    assert result.assignments == 1
    assert result.events == 0
    assert result.documents == 0
    assert result.total == 2

    assert session.query(CourseModel).filter_by(source="sample").count() == 0
    assert session.query(AssignmentModel).filter_by(source="sample").count() == 0

    # Los datos de otros plugins y los locales siguen ahí
    assert session.query(CourseModel).filter_by(source="other").count() == 1
    assert session.query(AssignmentModel).filter_by(source="other").count() == 1

    task_ids = {task.id for task in TaskService(session).list_tasks()}
    assert local.id in task_ids


def test_purge_unknown_plugin_deletes_nothing(session: Session) -> None:
    result = PluginDataService(session).purge("does-not-exist")

    assert result.total == 0


def test_purge_cannot_target_local_data(session: Session) -> None:
    TaskService(session).create(title="Mi tarea")

    with pytest.raises(InvalidSyncSourceError):
        PluginDataService(session).purge("local")

    assert len(TaskService(session).list_tasks()) == 1


def test_plugin_can_sync_again_after_purge(session: Session) -> None:
    plugin = FakeExternalPlugin(needs_connection=False)

    SyncService(session=session, plugin=plugin).sync()
    PluginDataService(session).purge("sample")

    result = SyncService(session=session, plugin=plugin).sync()

    assert result.total == 2
    assert session.query(CourseModel).count() == 1
