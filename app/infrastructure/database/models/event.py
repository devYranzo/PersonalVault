from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class EventModel(Base):
    __tablename__ = "events"

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

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="other",
    )

    start_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    end_at: Mapped[datetime | None] = mapped_column(
        DateTime,
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

    location: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    url: Mapped[str | None] = mapped_column(
        String(2000),
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