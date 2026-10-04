from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class EventType(StrEnum):
    CLASS = "class"
    EXAM = "exam"
    MEETING = "meeting"
    DEADLINE = "deadline"
    OTHER = "other"


class Event(BaseModel):
    id: str = Field(description="ID interno de Personal Vault")

    title: str
    description: str | None = None

    event_type: EventType = EventType.OTHER

    start_at: datetime
    end_at: datetime | None = None

    course_id: str | None = None
    course_name: str | None = None

    location: str | None = None
    url: str | None = None

    source: str = Field(
        description="Identificador del plugin que proporciona el evento"
    )

    external_id: str = Field(
        description="ID del evento en el servicio externo"
    )

    created_at: datetime | None = None
    updated_at: datetime | None = None