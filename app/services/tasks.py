from collections.abc import Callable
from datetime import datetime
from typing import TypeVar
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.models import LOCAL_SOURCE, Assignment, AssignmentStatus
from app.infrastructure.database.repositories import AssignmentRepository

T = TypeVar("T")


class TaskError(Exception):
    """Error base de las operaciones sobre tareas."""


class TaskNotFoundError(TaskError):
    def __init__(self, task_id: str) -> None:
        super().__init__(f"No existe ninguna tarea con ID '{task_id}'.")


class ReadOnlyTaskError(TaskError):
    def __init__(self) -> None:
        super().__init__(
            "Las tareas externas son de solo lectura: se completan "
            "cuando las completa el servicio externo."
        )


class InvalidTaskError(TaskError):
    """Los datos de la tarea no son válidos."""


class TaskService:
    """
    CRUD de tareas locales.

    Las tareas externas (las que traen los plugins) solo se leen:
    cualquier intento de modificarlas o borrarlas lanza ReadOnlyTaskError.
    """

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = AssignmentRepository(session)

    # ----------------------------------------------------------- lectura

    def list_tasks(self) -> list[Assignment]:
        return self.repository.get_all()

    # --------------------------------------------------------- escritura

    def create(
        self,
        *,
        title: str,
        description: str | None = None,
        course_name: str | None = None,
        due_date: datetime | None = None,
        status: AssignmentStatus = AssignmentStatus.PENDING,
    ) -> Assignment:
        task_id = uuid4().hex
        now = datetime.now()

        task = Assignment(
            id=task_id,
            title=self._clean_title(title),
            description=self._clean_optional(description),
            course_name=self._clean_optional(course_name),
            due_date=due_date,
            status=AssignmentStatus(status),
            source=LOCAL_SOURCE,
            external_id=task_id,
            created_at=now,
            updated_at=now,
        )

        return self._commit(lambda: self.repository.save(task))

    def update(
        self,
        task_id: str,
        *,
        title: str,
        description: str | None,
        course_name: str | None,
        due_date: datetime | None,
        status: AssignmentStatus,
    ) -> Assignment:
        task = self._get_local(task_id)

        updated = task.model_copy(
            update={
                "title": self._clean_title(title),
                "description": self._clean_optional(description),
                "course_name": self._clean_optional(course_name),
                "due_date": due_date,
                "status": AssignmentStatus(status),
                "updated_at": datetime.now(),
            }
        )

        return self._commit(lambda: self.repository.save(updated))

    def set_status(
        self,
        task_id: str,
        status: AssignmentStatus,
    ) -> Assignment:
        task = self._get_local(task_id)

        updated = task.model_copy(
            update={
                "status": AssignmentStatus(status),
                "updated_at": datetime.now(),
            }
        )

        return self._commit(lambda: self.repository.save(updated))

    def delete(self, task_id: str) -> None:
        self._get_local(task_id)

        self._commit(lambda: self.repository.delete_by_id(task_id))

    # --------------------------------------------------------- internos

    def _get_local(self, task_id: str) -> Assignment:
        task = self.repository.get(task_id)

        if task is None:
            raise TaskNotFoundError(task_id)

        if not task.is_local:
            raise ReadOnlyTaskError()

        return task

    def _commit(self, operation: Callable[[], T]) -> T:
        try:
            result = operation()
            self.session.commit()
            return result
        except Exception:
            self.session.rollback()
            raise

    @staticmethod
    def _clean_title(title: str) -> str:
        cleaned = (title or "").strip()

        if not cleaned:
            raise InvalidTaskError("El título de la tarea no puede estar vacío.")

        return cleaned

    @staticmethod
    def _clean_optional(value: str | None) -> str | None:
        if value is None:
            return None

        cleaned = value.strip()

        return cleaned or None