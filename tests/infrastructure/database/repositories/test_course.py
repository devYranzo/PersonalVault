from datetime import UTC, datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.models import Course
from app.infrastructure.database.base import Base
from app.infrastructure.database.models import CourseModel
from app.infrastructure.database.repositories import CourseRepository


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
        ],
    )

    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    return session_factory()


def create_course(
    course_id: str = "course-1",
    name: str = "Programación",
) -> Course:
    return Course(
        id=course_id,
        name=name,
        description="Curso de programación",
        source="example",
        external_id=f"external-{course_id}",
        url="https://example.com/course",
        teacher_name="Profesor Ejemplo",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def test_save_creates_course(tmp_path: Path) -> None:
    session = create_test_session(tmp_path)
    repository = CourseRepository(session)

    course = create_course()

    saved_course = repository.save(course)

    session.commit()

    assert saved_course.id == course.id
    assert saved_course.name == course.name
    assert saved_course.source == course.source
    assert saved_course.external_id == course.external_id


def test_get_returns_course(tmp_path: Path) -> None:
    session = create_test_session(tmp_path)
    repository = CourseRepository(session)

    course = create_course()

    repository.save(course)
    session.commit()

    result = repository.get(course.id)

    assert result is not None
    assert result.id == course.id
    assert result.name == course.name


def test_get_returns_none_for_unknown_course(
    tmp_path: Path,
) -> None:
    session = create_test_session(tmp_path)
    repository = CourseRepository(session)

    result = repository.get("does-not-exist")

    assert result is None


def test_get_all_returns_courses(
    tmp_path: Path,
) -> None:
    session = create_test_session(tmp_path)
    repository = CourseRepository(session)

    repository.save(
        create_course(
            course_id="course-2",
            name="Zoología",
        )
    )

    repository.save(
        create_course(
            course_id="course-1",
            name="Algoritmos",
        )
    )

    session.commit()

    courses = repository.get_all()

    assert len(courses) == 2
    assert courses[0].name == "Algoritmos"
    assert courses[1].name == "Zoología"


def test_get_by_external_id_returns_course(
    tmp_path: Path,
) -> None:
    session = create_test_session(tmp_path)
    repository = CourseRepository(session)

    course = create_course()

    repository.save(course)
    session.commit()

    result = repository.get_by_external_id(
        source="example",
        external_id="external-course-1",
    )

    assert result is not None
    assert result.id == course.id


def test_get_by_external_id_returns_none_when_not_found(
    tmp_path: Path,
) -> None:
    session = create_test_session(tmp_path)
    repository = CourseRepository(session)

    result = repository.get_by_external_id(
        source="google_classroom",
        external_id="does-not-exist",
    )

    assert result is None


def test_save_updates_existing_course(
    tmp_path: Path,
) -> None:
    session = create_test_session(tmp_path)
    repository = CourseRepository(session)

    course = create_course()

    repository.save(course)
    session.commit()

    updated_course = course.model_copy(
        update={
            "name": "Programación Avanzada",
            "teacher_name": "Nuevo Profesor",
        }
    )

    repository.save(updated_course)
    session.commit()

    result = repository.get(course.id)

    assert result is not None
    assert result.name == "Programación Avanzada"
    assert result.teacher_name == "Nuevo Profesor"


def test_delete_by_id_deletes_course(
    tmp_path: Path,
) -> None:
    session = create_test_session(tmp_path)
    repository = CourseRepository(session)

    course = create_course()

    repository.save(course)
    session.commit()

    deleted = repository.delete_by_id(course.id)
    session.commit()

    assert deleted is True
    assert repository.get(course.id) is None


def test_delete_by_id_returns_false_for_unknown_course(
    tmp_path: Path,
) -> None:
    session = create_test_session(tmp_path)
    repository = CourseRepository(session)

    deleted = repository.delete_by_id("does-not-exist")

    assert deleted is False