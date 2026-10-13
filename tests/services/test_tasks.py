from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.models import LOCAL_SOURCE, Assignment, AssignmentStatus
from app.infrastructure.database.base import Base
from app.infrastructure.database.models import (
    AssignmentModel,
    CourseModel,
    DocumentModel,
    EventModel,
)
from app.infrastructure.database.repositories import AssignmentRepository
from app.services import (
    InvalidTaskError,
    ReadOnlyTaskError,
    TaskNotFoundError,
    TaskService,
)


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


@pytest.fixture
def service(session: Session) -> TaskService:
    return TaskService(session)


def create_external_task(session: Session) -> Assignment:
    task = Assignment(
        id="external-1",
        title="Tarea de Classroom",
        source="google_classroom",
        external_id="gc-1",
    )

    saved = AssignmentRepository(session).save(task)
    session.commit()

    return saved


def test_create_builds_a_local_task(service: TaskService) -> None:
    due = datetime.now() + timedelta(days=3)

    task = service.create(
        title="  Estudiar SQL  ",
        description="Capítulos 1 a 3",
        course_name="Bases de Datos",
        due_date=due,
    )

    assert task.is_local
    assert task.source == LOCAL_SOURCE
    assert task.external_id == task.id
    assert task.title == "Estudiar SQL"
    assert task.status == AssignmentStatus.PENDING
    assert task.due_date == due
    assert task.created_at is not None

    assert service.list_tasks() == [task]


def test_create_rejects_empty_title(service: TaskService) -> None:
    with pytest.raises(InvalidTaskError):
        service.create(title="   ")

    assert service.list_tasks() == []


def test_blank_optional_fields_are_stored_as_none(
    service: TaskService,
) -> None:
    task = service.create(
        title="Tarea",
        description="   ",
        course_name="",
    )

    assert task.description is None
    assert task.course_name is None


def test_update_changes_local_task(service: TaskService) -> None:
    task = service.create(title="Original")

    updated = service.update(
        task.id,
        title="Modificada",
        description="Nueva descripción",
        course_name="Curso",
        due_date=None,
        status=AssignmentStatus.IN_PROGRESS,
    )

    assert updated.id == task.id
    assert updated.title == "Modificada"
    assert updated.description == "Nueva descripción"
    assert updated.status == AssignmentStatus.IN_PROGRESS
    assert updated.created_at == task.created_at

    assert len(service.list_tasks()) == 1


def test_update_rejects_empty_title_and_keeps_data(
    service: TaskService,
) -> None:
    task = service.create(title="Original")

    with pytest.raises(InvalidTaskError):
        service.update(
            task.id,
            title="",
            description=None,
            course_name=None,
            due_date=None,
            status=AssignmentStatus.PENDING,
        )

    assert service.list_tasks()[0].title == "Original"


def test_set_status_toggles_completion(service: TaskService) -> None:
    task = service.create(title="Tarea")

    done = service.set_status(task.id, AssignmentStatus.COMPLETED)
    assert done.status == AssignmentStatus.COMPLETED

    reopened = service.set_status(task.id, AssignmentStatus.PENDING)
    assert reopened.status == AssignmentStatus.PENDING


def test_delete_removes_local_task(service: TaskService) -> None:
    task = service.create(title="Tarea")

    service.delete(task.id)

    assert service.list_tasks() == []


def test_unknown_task_raises_not_found(service: TaskService) -> None:
    with pytest.raises(TaskNotFoundError):
        service.delete("does-not-exist")

    with pytest.raises(TaskNotFoundError):
        service.set_status("does-not-exist", AssignmentStatus.COMPLETED)


def test_external_task_is_read_only(
    session: Session,
    service: TaskService,
) -> None:
    external = create_external_task(session)

    assert not external.is_local

    with pytest.raises(ReadOnlyTaskError):
        service.update(
            external.id,
            title="Cambio",
            description=None,
            course_name=None,
            due_date=None,
            status=AssignmentStatus.PENDING,
        )

    with pytest.raises(ReadOnlyTaskError):
        service.set_status(external.id, AssignmentStatus.COMPLETED)

    with pytest.raises(ReadOnlyTaskError):
        service.delete(external.id)

    unchanged = service.list_tasks()[0]

    assert unchanged.title == "Tarea de Classroom"
    assert unchanged.status == AssignmentStatus.PENDING


def test_local_and_external_tasks_coexist(
    session: Session,
    service: TaskService,
) -> None:
    create_external_task(session)
    service.create(title="Mi tarea")

    tasks = service.list_tasks()

    assert len(tasks) == 2
    assert sorted(t.is_local for t in tasks) == [False, True]
