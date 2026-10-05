from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class AssignmentModel(Base):
    __tablename__ = "assignments"

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

    course_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    course_name: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    due_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    external_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    url: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )