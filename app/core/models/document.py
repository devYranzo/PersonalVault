from datetime import datetime

from pydantic import BaseModel, Field


class Document(BaseModel):
    id: str = Field(description="ID interno de Personal Vault")

    title: str

    description: str | None = None

    file_name: str | None = None
    mime_type: str | None = None

    path: str | None = None
    url: str | None = None

    course_id: str | None = None
    course_name: str | None = None

    source: str = Field(
        description="Identificador del plugin que proporciona el documento"
    )

    external_id: str = Field(
        description="ID del documento en el servicio externo"
    )

    created_at: datetime | None = None
    updated_at: datetime | None = None