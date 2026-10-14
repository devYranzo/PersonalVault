from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.models import LOCAL_SOURCE
from app.infrastructure.database.repositories import (
    AssignmentRepository,
    CourseRepository,
    DocumentRepository,
    EventRepository,
)
from app.services.sync import InvalidSyncSourceError


@dataclass
class PurgeResult:
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


class PluginDataService:
    """
    Gestiona los datos que un plugin ha sincronizado.

    Cuando el usuario desactiva un plugin, sus datos dejan de tener
    sentido en Personal Vault y se eliminan. Los datos locales
    (source "local") nunca se tocan.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

        self.course_repository = CourseRepository(session)
        self.assignment_repository = AssignmentRepository(session)
        self.event_repository = EventRepository(session)
        self.document_repository = DocumentRepository(session)

    def purge(self, plugin_id: str) -> PurgeResult:
        """
        Elimina todos los datos sincronizados por `plugin_id`.

        Todo ocurre en una única transacción: o se borra todo
        o no se borra nada.
        """
        if plugin_id == LOCAL_SOURCE:
            raise InvalidSyncSourceError(
                f"Los datos '{LOCAL_SOURCE}' los crea el usuario y no "
                "pertenecen a ningún plugin: no se pueden eliminar así."
            )

        result = PurgeResult()

        try:
            result.courses = self.course_repository.delete_by_source(plugin_id)
            result.assignments = self.assignment_repository.delete_by_source(
                plugin_id,
            )
            result.events = self.event_repository.delete_by_source(plugin_id)
            result.documents = self.document_repository.delete_by_source(
                plugin_id,
            )

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        return result
