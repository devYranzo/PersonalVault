from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.models import Assignment, Course
from app.core.plugins import Plugin
from app.core.plugins.types import (
    PluginCapabilities,
    PluginInfo,
)
from app.infrastructure.database.base import Base
from app.infrastructure.database.models import (
    AssignmentModel,
    CourseModel,
    DocumentModel,
    EventModel,
)
from app.services import SyncService


class TestPlugin(Plugin):
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            description="Plugin utilizado para tests.",
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
                source="test-plugin",
                external_id="external-course-1",
            ),
            Course(
                id="course-2",
                name="Bases de Datos",
                source="test-plugin",
                external_id="external-course-2",
            ),
        ]

    def get_assignments(self) -> list[Assignment]:
        return [
            Assignment(
                id="assignment-1",
                title="Práctica de Python",
                course_id="course-1",
                course_name="Programación",
                source="test-plugin",
                external_id="external-assignment-1",
            ),
        ]


def create_test_session(tmp_path: Path) -> Session:
    database_path = tmp_path / "test.db"

    engine = create_engine(
        f"sqlite:///{database_path}",
        echo=False,
    )

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

    return session_factory()


def test_sync_saves_plugin_data(
    tmp_path: Path,
) -> None:
    session = create_test_session(tmp_path)
    plugin = TestPlugin()

    service = SyncService(
        session=session,
        plugin=plugin,
    )

    result = service.sync()

    assert result.courses == 2
    assert result.assignments == 1
    assert result.events == 0
    assert result.documents == 0
    assert result.total == 3

    courses = session.query(CourseModel).all()
    assignments = session.query(AssignmentModel).all()

    assert len(courses) == 2
    assert len(assignments) == 1

    assert courses[0].name in {
        "Programación",
        "Bases de Datos",
    }

    assert assignments[0].title == "Práctica de Python"

    session.close()


def test_sync_updates_existing_external_entities(
    tmp_path: Path,
) -> None:
    session = create_test_session(tmp_path)

    plugin = TestPlugin()

    service = SyncService(
        session=session,
        plugin=plugin,
    )

    first_result = service.sync()

    assert first_result.total == 3

    course = session.query(CourseModel).filter_by(
        source="test-plugin",
        external_id="external-course-1",
    ).one()

    original_id = course.id

    course.name = "Nombre antiguo"

    session.commit()

    service.sync()

    updated_course = session.query(CourseModel).filter_by(
        source="test-plugin",
        external_id="external-course-1",
    ).one()

    assert updated_course.name == "Programación"

    assert updated_course.id == original_id

    courses = session.query(CourseModel).filter_by(
        source="test-plugin",
    ).all()

    assert len(courses) == 2

    session.close()


def test_sync_rolls_back_when_plugin_fails(
    tmp_path: Path,
) -> None:
    class FailingPlugin(TestPlugin):
        def get_assignments(self) -> list[Assignment]:
            raise RuntimeError("Error de sincronización")

    session = create_test_session(tmp_path)

    plugin = FailingPlugin()

    service = SyncService(
        session=session,
        plugin=plugin,
    )

    try:
        service.sync()
        raise AssertionError(
            "Se esperaba RuntimeError",
        )
    except RuntimeError as exc:
        assert str(exc) == "Error de sincronización"

    courses = session.query(CourseModel).all()

    assert courses == []

    assignments = session.query(AssignmentModel).all()

    assert assignments == []

    session.close()