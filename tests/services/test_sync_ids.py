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
from app.services import SyncService


class IdPlugin(Plugin):
    """Plugin que pone IDs propios (y repetidos entre plugins) a propósito."""

    def __init__(self, plugin_id: str) -> None:
        self._plugin_id = plugin_id

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            id=self._plugin_id,
            name=self._plugin_id,
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
                source=self._plugin_id,
                external_id="ext-course",
            ),
        ]

    def get_assignments(self) -> list[Assignment]:
        return [
            Assignment(
                id="assignment-1",
                title="Práctica",
                course_id="ext-course",
                source=self._plugin_id,
                external_id="ext-assignment",
            ),
            Assignment(
                id="assignment-2",
                title="Sin curso",
                source=self._plugin_id,
                external_id="ext-assignment-2",
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

    factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    with factory() as db_session:
        yield db_session

    engine.dispose()


def test_service_generates_ids_and_ignores_plugin_ids(
    session: Session,
) -> None:
    SyncService(session, IdPlugin("alpha")).sync()

    course = session.query(CourseModel).one()
    assignments = {
        row.external_id: row for row in session.query(AssignmentModel).all()
    }

    assert course.id == "alpha:ext-course"
    assert assignments["ext-assignment"].id == "alpha:ext-assignment"
    assert assignments["ext-assignment-2"].id == "alpha:ext-assignment-2"


def test_course_id_points_to_the_internal_course_id(
    session: Session,
) -> None:
    SyncService(session, IdPlugin("alpha")).sync()

    course = session.query(CourseModel).one()
    assignment = (
        session.query(AssignmentModel)
        .filter_by(external_id="ext-assignment")
        .one()
    )
    without_course = (
        session.query(AssignmentModel)
        .filter_by(external_id="ext-assignment-2")
        .one()
    )

    assert assignment.course_id == course.id
    assert without_course.course_id is None


def test_two_plugins_with_same_ids_do_not_collide(session: Session) -> None:
    SyncService(session, IdPlugin("alpha")).sync()
    SyncService(session, IdPlugin("beta")).sync()

    assert session.query(CourseModel).count() == 2
    assert session.query(AssignmentModel).count() == 4

    ids = {row.id for row in session.query(AssignmentModel).all()}

    assert "alpha:ext-assignment" in ids
    assert "beta:ext-assignment" in ids


def test_ids_are_stable_across_syncs(session: Session) -> None:
    plugin = IdPlugin("alpha")

    SyncService(session, plugin).sync()
    first = {row.id for row in session.query(AssignmentModel).all()}

    SyncService(session, plugin).sync()
    second = {row.id for row in session.query(AssignmentModel).all()}

    assert first == second
    assert session.query(AssignmentModel).count() == 2