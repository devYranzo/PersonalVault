from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.models import Event
from app.infrastructure.database.models import EventModel
from app.infrastructure.database.repositories.base import BaseRepository


class EventRepository(
    BaseRepository[EventModel, Event],
):
    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def to_domain(self, model: EventModel) -> Event:
        return Event(
            id=model.id,
            title=model.title,
            description=model.description,
            event_type=model.event_type,
            start_at=model.start_at,
            end_at=model.end_at,
            course_id=model.course_id,
            course_name=model.course_name,
            location=model.location,
            url=model.url,
            source=model.source,
            external_id=model.external_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def to_model(self, domain: Event) -> EventModel:
        return EventModel(
            id=domain.id,
            title=domain.title,
            description=domain.description,
            event_type=domain.event_type.value,
            start_at=domain.start_at,
            end_at=domain.end_at,
            course_id=domain.course_id,
            course_name=domain.course_name,
            location=domain.location,
            url=domain.url,
            source=domain.source,
            external_id=domain.external_id,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )

    def get(self, event_id: str) -> Event | None:
        statement = select(EventModel).where(
            EventModel.id == event_id,
        )

        model = self.session.scalar(statement)

        if model is None:
            return None

        return self.to_domain(model)

    def get_all(self) -> list[Event]:
        statement = select(EventModel).order_by(
            EventModel.start_at,
        )

        models = self.session.scalars(statement).all()

        return [
            self.to_domain(model)
            for model in models
        ]

    def get_by_external_id(
        self,
        source: str,
        external_id: str,
    ) -> Event | None:
        statement = select(EventModel).where(
            EventModel.source == source,
            EventModel.external_id == external_id,
        )

        model = self.session.scalar(statement)

        if model is None:
            return None

        return self.to_domain(model)

    def save(self, event: Event) -> Event:
        existing_model = self.session.get(
            EventModel,
            event.id,
        )

        if existing_model is None:
            model = self.to_model(event)
            self.session.add(model)
            self.session.flush()

            return self.to_domain(model)

        existing_model.title = event.title
        existing_model.description = event.description
        existing_model.event_type = event.event_type.value
        existing_model.start_at = event.start_at
        existing_model.end_at = event.end_at
        existing_model.course_id = event.course_id
        existing_model.course_name = event.course_name
        existing_model.location = event.location
        existing_model.url = event.url
        existing_model.source = event.source
        existing_model.external_id = event.external_id
        existing_model.created_at = event.created_at
        existing_model.updated_at = event.updated_at

        self.session.flush()

        return self.to_domain(existing_model)

    def delete_by_id(self, event_id: str) -> bool:
        model = self.session.get(
            EventModel,
            event_id,
        )

        if model is None:
            return False

        self.delete(model)
        self.session.flush()

        return True