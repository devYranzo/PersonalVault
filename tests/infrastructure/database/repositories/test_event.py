from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.models import Event, EventType
from app.infrastructure.database.repositories import EventRepository


def create_event(
    event_id: str = "event-1",
    title: str = "Clase de programación",
) -> Event:
    start = datetime.now(timezone.utc)

    return Event(
        id=event_id,
        title=title,
        description="Clase semanal",
        event_type=EventType.CLASS,
        start_at=start,
        end_at=start + timedelta(hours=2),
        course_id="course-1",
        course_name="Programación",
        location="Aula 101",
        url="https://example.com/event",
        source="example",
        external_id=f"external-{event_id}",
        created_at=start,
        updated_at=start,
    )


def test_save_creates_event(
    session: Session,
) -> None:
    repository = EventRepository(session)

    event = create_event()

    saved = repository.save(event)
    session.commit()

    assert saved.id == event.id
    assert saved.title == event.title
    assert saved.event_type == EventType.CLASS


def test_get_returns_event(
    session: Session,
) -> None:
    repository = EventRepository(session)

    event = create_event()

    repository.save(event)
    session.commit()

    result = repository.get(event.id)

    assert result is not None
    assert result.id == event.id
    assert result.title == event.title


def test_get_returns_none_for_unknown_event(
    session: Session,
) -> None:
    repository = EventRepository(session)

    assert repository.get("unknown") is None


def test_get_all_orders_by_start_time(
    session: Session,
) -> None:
    repository = EventRepository(session)

    now = datetime.now(timezone.utc)

    later = create_event(
        event_id="event-2",
        title="Clase posterior",
    ).model_copy(
        update={
            "start_at": now + timedelta(days=2),
        }
    )

    earlier = create_event(
        event_id="event-1",
        title="Clase anterior",
    ).model_copy(
        update={
            "start_at": now,
        }
    )

    repository.save(later)
    repository.save(earlier)
    session.commit()

    events = repository.get_all()

    assert len(events) == 2
    assert events[0].id == "event-1"
    assert events[1].id == "event-2"


def test_get_by_external_id(
    session: Session,
) -> None:
    repository = EventRepository(session)

    event = create_event()

    repository.save(event)
    session.commit()

    result = repository.get_by_external_id(
        "example",
        "external-event-1",
    )

    assert result is not None
    assert result.id == event.id


def test_save_updates_event(
    session: Session,
) -> None:
    repository = EventRepository(session)

    event = create_event()

    repository.save(event)
    session.commit()

    updated = event.model_copy(
        update={
            "title": "Clase actualizada",
            "location": "Aula 202",
            "event_type": EventType.EXAM,
        }
    )

    repository.save(updated)
    session.commit()

    result = repository.get(event.id)

    assert result is not None
    assert result.title == "Clase actualizada"
    assert result.location == "Aula 202"
    assert result.event_type == EventType.EXAM


def test_delete_event(
    session: Session,
) -> None:
    repository = EventRepository(session)

    event = create_event()

    repository.save(event)
    session.commit()

    assert repository.delete_by_id(event.id) is True

    session.commit()

    assert repository.get(event.id) is None


def test_delete_unknown_event_returns_false(
    session: Session,
) -> None:
    repository = EventRepository(session)

    assert repository.delete_by_id("unknown") is False