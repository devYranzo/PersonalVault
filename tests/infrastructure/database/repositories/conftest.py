from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.database.base import Base
from app.infrastructure.database.models import (
    AssignmentModel,
    CourseModel,
    DocumentModel,
    EventModel,
)


@pytest.fixture
def session(tmp_path: Path) -> Session:
    database_path = tmp_path / "test.db"

    engine = create_engine(
        f"sqlite:///{database_path}",
        echo=False,
    )

    Base.metadata.create_all(
        engine,
        tables=[
            CourseModel.__table__,
            AssignmentModel.__table__,
            EventModel.__table__,
            DocumentModel.__table__,
        ],
    )

    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    with session_factory() as db_session:
        yield db_session

    engine.dispose()