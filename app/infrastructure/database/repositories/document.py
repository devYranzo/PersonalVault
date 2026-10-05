from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.models import Document
from app.infrastructure.database.models import DocumentModel
from app.infrastructure.database.repositories.base import BaseRepository


class DocumentRepository(
    BaseRepository[DocumentModel, Document],
):
    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def to_domain(self, model: DocumentModel) -> Document:
        return Document(
            id=model.id,
            title=model.title,
            description=model.description,
            file_name=model.file_name,
            mime_type=model.mime_type,
            path=model.path,
            url=model.url,
            course_id=model.course_id,
            course_name=model.course_name,
            source=model.source,
            external_id=model.external_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def to_model(self, domain: Document) -> DocumentModel:
        return DocumentModel(
            id=domain.id,
            title=domain.title,
            description=domain.description,
            file_name=domain.file_name,
            mime_type=domain.mime_type,
            path=domain.path,
            url=domain.url,
            course_id=domain.course_id,
            course_name=domain.course_name,
            source=domain.source,
            external_id=domain.external_id,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )

    def get(self, document_id: str) -> Document | None:
        statement = select(DocumentModel).where(
            DocumentModel.id == document_id,
        )

        model = self.session.scalar(statement)

        if model is None:
            return None

        return self.to_domain(model)

    def get_all(self) -> list[Document]:
        statement = select(DocumentModel).order_by(
            DocumentModel.title,
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
    ) -> Document | None:
        statement = select(DocumentModel).where(
            DocumentModel.source == source,
            DocumentModel.external_id == external_id,
        )

        model = self.session.scalar(statement)

        if model is None:
            return None

        return self.to_domain(model)

    def save(self, document: Document) -> Document:
        existing_model = self.session.get(
            DocumentModel,
            document.id,
        )

        if existing_model is None:
            model = self.to_model(document)
            self.session.add(model)
            self.session.flush()

            return self.to_domain(model)

        existing_model.title = document.title
        existing_model.description = document.description
        existing_model.file_name = document.file_name
        existing_model.mime_type = document.mime_type
        existing_model.path = document.path
        existing_model.url = document.url
        existing_model.course_id = document.course_id
        existing_model.course_name = document.course_name
        existing_model.source = document.source
        existing_model.external_id = document.external_id
        existing_model.created_at = document.created_at
        existing_model.updated_at = document.updated_at

        self.session.flush()

        return self.to_domain(existing_model)

    def delete_by_id(self, document_id: str) -> bool:
        model = self.session.get(
            DocumentModel,
            document_id,
        )

        if model is None:
            return False

        self.delete(model)
        self.session.flush()

        return True