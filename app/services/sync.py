from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.models import LOCAL_SOURCE, Assignment, Course, Document, Event
from app.core.plugins import Plugin, PluginCapabilities
from app.infrastructure.database.repositories import (
    AssignmentRepository,
    CourseRepository,
    DocumentRepository,
    EventRepository,
)


class InvalidSyncSourceError(Exception):
    """Un plugin ha devuelto datos con un `source` que no le corresponde."""


class PluginNotConnectedError(Exception):
    """El plugin necesita conexión con su servicio externo y no está conectado."""

    def __init__(self, plugin_name: str) -> None:
        super().__init__(
            f"El plugin '{plugin_name}' necesita estar conectado a su "
            "servicio externo para poder sincronizar. Conéctalo primero."
        )


@dataclass
class SyncResult:
    courses: int = 0
    assignments: int = 0
    events: int = 0
    documents: int = 0

    # Elementos que ya no existen en la fuente externa y se han borrado.
    removed_courses: int = 0
    removed_assignments: int = 0
    removed_events: int = 0
    removed_documents: int = 0

    @property
    def removed(self) -> int:
        return (
            self.removed_courses
            + self.removed_assignments
            + self.removed_events
            + self.removed_documents
        )

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

        # Un plugin que necesita autenticación (p. ej. Google Classroom)
        # no puede sincronizar sin estar conectado. Se comprueba antes de
        # tocar la base de datos.
        if self.plugin.requires_connection() and not self.plugin.is_connected():
            raise PluginNotConnectedError(self.plugin.info.name)

        result = SyncResult()

        try:
            result.courses, result.removed_courses = self.sync_courses()
            (
                result.assignments,
                result.removed_assignments,
            ) = self.sync_assignments()
            result.events, result.removed_events = self.sync_events()
            result.documents, result.removed_documents = self.sync_documents()

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        return result

    def sync_courses(self) -> tuple[int, int]:
        courses = self.plugin.get_courses()
        self._validate_source(courses, "cursos")

        for course in courses:
            self.course_repository.save(course)

        removed = self._reconcile(
            PluginCapabilities.COURSES,
            self.course_repository,
            courses,
        )

        return len(courses), removed

    def sync_assignments(self) -> tuple[int, int]:
        assignments = self.plugin.get_assignments()
        self._validate_source(assignments, "tareas")

        for assignment in assignments:
            self.assignment_repository.save(assignment)

        removed = self._reconcile(
            PluginCapabilities.ASSIGNMENTS,
            self.assignment_repository,
            assignments,
        )

        return len(assignments), removed

    def sync_events(self) -> tuple[int, int]:
        events = self.plugin.get_events()
        self._validate_source(events, "eventos")

        for event in events:
            self.event_repository.save(event)

        removed = self._reconcile(
            PluginCapabilities.EVENTS,
            self.event_repository,
            events,
        )

        return len(events), removed

    def sync_documents(self) -> tuple[int, int]:
        documents = self.plugin.get_documents()
        self._validate_source(documents, "documentos")

        for document in documents:
            self.document_repository.save(document)

        removed = self._reconcile(
            PluginCapabilities.DOCUMENTS,
            self.document_repository,
            documents,
        )

        return len(documents), removed

    def _reconcile(
        self,
        capability: PluginCapabilities,
        repository: (
            CourseRepository
            | AssignmentRepository
            | EventRepository
            | DocumentRepository
        ),
        items: Iterable[Assignment | Course | Document | Event],
    ) -> int:
        """
        Borra lo que el plugin sincronizó antes y ya no devuelve.

        Solo se reconcilian los tipos que el plugin declara en sus
        `capabilities`: si no declara, por ejemplo, EVENTS, no se le
        atribuye ningún evento y nunca se le borra ninguno por
        devolver una lista vacía por defecto.

        Un plugin debe lanzar una excepción si falla al consultar su
        servicio. Devolver [] significa "ya no hay nada" y se borra.
        """
        if capability not in self.plugin.info.capabilities:
            return 0

        return repository.delete_missing(
            self.plugin.info.id,
            {item.external_id for item in items},
        )

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