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