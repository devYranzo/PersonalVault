from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.models import Assignment
from app.infrastructure.database.models import AssignmentModel
from app.infrastructure.database.repositories.base import BaseRepository


class AssignmentRepository(
    BaseRepository[AssignmentModel, Assignment],
):
    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def to_domain(self, model: AssignmentModel) -> Assignment:
        return Assignment(
            id=model.id,
            title=model.title,
            description=model.description,
            course_id=model.course_id,
            course_name=model.course_name,
            due_date=model.due_date,
            status=model.status,
            source=model.source,
            external_id=model.external_id,
            url=model.url,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def to_model(self, domain: Assignment) -> AssignmentModel:
        return AssignmentModel(
            id=domain.id,
            title=domain.title,
            description=domain.description,
            course_id=domain.course_id,
            course_name=domain.course_name,
            due_date=domain.due_date,
            status=domain.status.value,
            source=domain.source,
            external_id=domain.external_id,
            url=domain.url,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )

    def get(self, assignment_id: str) -> Assignment | None:
        statement = select(AssignmentModel).where(
            AssignmentModel.id == assignment_id,
        )

        model = self.session.scalar(statement)

        if model is None:
            return None

        return self.to_domain(model)

    def get_all(self) -> list[Assignment]:
        statement = select(AssignmentModel).order_by(
            AssignmentModel.title,
        )

        models = self.session.scalars(statement).all()

        return [self.to_domain(model) for model in models]

    def get_by_external_id(
        self,
        source: str,
        external_id: str,
    ) -> Assignment | None:
        statement = select(AssignmentModel).where(
            AssignmentModel.source == source,
            AssignmentModel.external_id == external_id,
        )

        model = self.session.scalar(statement)

        if model is None:
            return None

        return self.to_domain(model)

    def save(self, assignment: Assignment) -> Assignment:
        existing_model = self.session.get(
            AssignmentModel,
            assignment.id,
        )

        if existing_model is None:
            model = self.to_model(assignment)
            self.session.add(model)
            self.session.flush()

            return self.to_domain(model)

        existing_model.title = assignment.title
        existing_model.description = assignment.description
        existing_model.course_id = assignment.course_id
        existing_model.course_name = assignment.course_name
        existing_model.due_date = assignment.due_date
        existing_model.status = assignment.status.value
        existing_model.source = assignment.source
        existing_model.external_id = assignment.external_id
        existing_model.url = assignment.url
        existing_model.created_at = assignment.created_at
        existing_model.updated_at = assignment.updated_at

        self.session.flush()

        return self.to_domain(existing_model)

    def delete_by_id(self, assignment_id: str) -> bool:
        model = self.session.get(
            AssignmentModel,
            assignment_id,
        )

        if model is None:
            return False

        self.delete(model)
        self.session.flush()

        return True