from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class DocumentModel(Base):
    __tablename__ = "documents"

    __table_args__ = (
        UniqueConstraint(
            "source",
            "external_id",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    file_name: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    mime_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    path: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )

    url: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )

    course_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    course_name: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    external_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )