from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.models import Course
from app.infrastructure.database.models import CourseModel
from app.infrastructure.database.repositories.base import BaseRepository


class CourseRepository(
    BaseRepository[CourseModel, Course],
):
    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def to_domain(self, model: CourseModel) -> Course:
        return Course(
            id=model.id,
            name=model.name,
            description=model.description,
            source=model.source,
            external_id=model.external_id,
            url=model.url,
            teacher_name=model.teacher_name,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def to_model(self, domain: Course) -> CourseModel:
        return CourseModel(
            id=domain.id,
            name=domain.name,
            description=domain.description,
            source=domain.source,
            external_id=domain.external_id,
            url=domain.url,
            teacher_name=domain.teacher_name,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )

    def get(self, course_id: str) -> Course | None:
        statement = select(CourseModel).where(
            CourseModel.id == course_id,
        )

        model = self.session.scalar(statement)

        if model is None:
            return None

        return self.to_domain(model)

    def get_all(self) -> list[Course]:
        statement = select(CourseModel).order_by(
            CourseModel.name,
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
    ) -> Course | None:
        statement = select(CourseModel).where(
            CourseModel.source == source,
            CourseModel.external_id == external_id,
        )

        model = self.session.scalar(statement)

        if model is None:
            return None

        return self.to_domain(model)

    def save(self, course: Course) -> Course:
        existing_model = self.session.get(
            CourseModel,
            course.id,
        )

        if existing_model is None:
            model = self.to_model(course)
            self.session.add(model)
            self.session.flush()

            return self.to_domain(model)

        existing_model.name = course.name
        existing_model.description = course.description
        existing_model.source = course.source
        existing_model.external_id = course.external_id
        existing_model.url = course.url
        existing_model.teacher_name = course.teacher_name
        existing_model.created_at = course.created_at
        existing_model.updated_at = course.updated_at

        self.session.flush()

        return self.to_domain(existing_model)

    def delete_by_id(self, course_id: str) -> bool:
        model = self.session.get(
            CourseModel,
            course_id,
        )

        if model is None:
            return False

        self.delete(model)
        self.session.flush()

        return True