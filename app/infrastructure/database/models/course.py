from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class CourseModel(Base):
    __tablename__ = "courses"

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

    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
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

    url: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )

    teacher_name: Mapped[str | None] = mapped_column(
        String(500),
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