from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

# Valor reservado de `source` para las tareas creadas por el usuario en
# Personal Vault. Ningún plugin debe usar este identificador.
LOCAL_SOURCE = "local"


class AssignmentStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


_OPEN_STATUSES = (AssignmentStatus.PENDING, AssignmentStatus.IN_PROGRESS)


def _to_local_naive(value: datetime) -> datetime:
    """Normaliza a hora local sin zona horaria para poder comparar."""
    if value.tzinfo is None:
        return value

    return value.astimezone().replace(tzinfo=None)


class Assignment(BaseModel):
    id: str = Field(description="ID interno de Personal Vault")

    title: str
    description: str | None = None

    course_id: str | None = None
    course_name: str | None = None

    due_date: datetime | None = None

    status: AssignmentStatus = AssignmentStatus.PENDING

    source: str = Field(
        description="Identificador del plugin que proporciona la tarea"
    )

    external_id: str = Field(
        description="ID de la tarea en el servicio externo"
    )

    url: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def is_local(self) -> bool:
        """Las tareas locales se pueden editar y borrar; las externas no."""
        return self.source == LOCAL_SOURCE

    def effective_status(self, now: datetime | None = None) -> AssignmentStatus:
        """
        Estado que se debe mostrar al usuario.

        «Atrasada» no se guarda: se deriva. Una tarea pendiente o en
        progreso cuya fecha de entrega ya ha pasado se considera atrasada.
        El estado guardado (`status`) no se modifica.
        """
        if self.status not in _OPEN_STATUSES or self.due_date is None:
            return self.status

        current = _to_local_naive(now) if now else datetime.now()

        if _to_local_naive(self.due_date) < current:
            return AssignmentStatus.OVERDUE

        return self.status