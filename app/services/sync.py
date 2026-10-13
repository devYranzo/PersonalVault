from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.models import LOCAL_SOURCE, Assignment, Course, Document, Event
from app.core.plugins import Plugin
from app.infrastructure.database.repositories import (
    AssignmentRepository,
    CourseRepository,
    DocumentRepository,
    EventRepository,
)


class InvalidSyncSourceError(Exception):
    """Un plugin ha devuelto datos con un `source` que no le corresponde."""


@dataclass
class SyncResult:
    courses: int = 0
    assignments: int = 0
    events: int = 0
    documents: int = 0

    @property
    def total(self) -> int:
        return (
            self.courses
            + self.assignments
            + self.events
            + self.documents
        )


class SyncService:
    def __init__(
        self,
        session: Session,
        plugin: Plugin,
    ) -> None:
        self.session = session
        self.plugin = plugin

        self.course_repository = CourseRepository(session)
        self.assignment_repository = AssignmentRepository(session)
        self.event_repository = EventRepository(session)
        self.document_repository = DocumentRepository(session)

    def sync(self) -> SyncResult:
        if self.plugin.info.id == LOCAL_SOURCE:
            raise InvalidSyncSourceError(
                f"El ID '{LOCAL_SOURCE}' está reservado para los datos "
                "creados por el usuario y no puede usarlo un plugin."
            )

        result = SyncResult()

        try:
            result.courses = self.sync_courses()
            result.assignments = self.sync_assignments()
            result.events = self.sync_events()
            result.documents = self.sync_documents()

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        return result

    def sync_courses(self) -> int:
        courses = self.plugin.get_courses()
        self._validate_source(courses, "cursos")

        for course in courses:
            self.course_repository.save(course)

        return len(courses)

    def sync_assignments(self) -> int:
        assignments = self.plugin.get_assignments()
        self._validate_source(assignments, "tareas")

        for assignment in assignments:
            self.assignment_repository.save(assignment)

        return len(assignments)

    def sync_events(self) -> int:
        events = self.plugin.get_events()
        self._validate_source(events, "eventos")

        for event in events:
            self.event_repository.save(event)

        return len(events)

    def sync_documents(self) -> int:
        documents = self.plugin.get_documents()
        self._validate_source(documents, "documentos")

        for document in documents:
            self.document_repository.save(document)

        return len(documents)

    def _validate_source(
        self,
        items: Iterable[Assignment | Course | Document | Event],
        kind: str,
    ) -> None:
        """
        Cada plugin solo puede aportar datos con su propio ID como `source`.

        Evita que un plugin sobrescriba datos locales (source "local")
        o datos de otro plugin, ya que el guardado se identifica por
        (source, external_id).
        """
        expected = self.plugin.info.id

        for item in items:
            if item.source != expected:
                raise InvalidSyncSourceError(
                    f"El plugin '{expected}' ha devuelto {kind} con "
                    f"source '{item.source}'. Un plugin solo puede "
                    "aportar datos con su propio ID."
                )