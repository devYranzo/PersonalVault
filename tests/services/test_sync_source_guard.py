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
from app.services import InvalidSyncSourceError, SyncService, TaskService


class SamplePlugin(Plugin):
    def __init__(
        self,
        plugin_id: str = "sample",
        source: str | None = None,
    ) -> None:
        self._plugin_id = plugin_id
        self._source = source or plugin_id

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            id=self._plugin_id,
            name="Sample",
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

    def get_courses(self) -> list[Course]:
        return [
            Course(
                id="course-1",
                name="Programación",
                source=self._source,
                external_id="ext-course-1",
            ),
        ]

    def get_assignments(self) -> list[Assignment]:
        return [
            Assignment(
                id="assignment-1",
                title="Práctica",
                source=self._source,
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


def test_plugin_cannot_use_reserved_local_id(session: Session) -> None:
    service = SyncService(session=session, plugin=SamplePlugin(plugin_id="local"))

    with pytest.raises(InvalidSyncSourceError):
        service.sync()

    assert session.query(AssignmentModel).count() == 0


def test_plugin_cannot_emit_data_with_another_source(
    session: Session,
) -> None:
    plugin = SamplePlugin(plugin_id="sample", source="local")

    with pytest.raises(InvalidSyncSourceError):
        SyncService(session=session, plugin=plugin).sync()

    # Nada se guarda, ni siquiera los cursos que sí eran válidos
    assert session.query(CourseModel).count() == 0
    assert session.query(AssignmentModel).count() == 0


def test_sync_does_not_touch_local_tasks(session: Session) -> None:
    local = TaskService(session).create(title="Mi tarea")

    result = SyncService(session=session, plugin=SamplePlugin()).sync()

    assert result.assignments == 1

    tasks = TaskService(session).list_tasks()

    assert len(tasks) == 2
    assert local.id in {task.id for task in tasks}
