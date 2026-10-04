from datetime import datetime

from pydantic import BaseModel, Field


class Course(BaseModel):
    id: str = Field(description="ID interno de Personal Vault")

    name: str
    description: str | None = None

    source: str = Field(
        description="Identificador del plugin que proporciona el curso"
    )

    external_id: str = Field(
        description="ID del curso en el servicio externo"
    )

    url: str | None = None

    teacher_name: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None