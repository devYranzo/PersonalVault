from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.models import Document
from app.infrastructure.database.repositories import DocumentRepository


def create_document(
    document_id: str = "document-1",
    title: str = "Apuntes de Python",
) -> Document:
    now = datetime.now(timezone.utc)

    return Document(
        id=document_id,
        title=title,
        description="Apuntes del curso",
        file_name="python.pdf",
        mime_type="application/pdf",
        path="/documents/python.pdf",
        url="https://example.com/python.pdf",
        course_id="course-1",
        course_name="Programación",
        source="example",
        external_id=f"external-{document_id}",
        created_at=now,
        updated_at=now,
    )


def test_save_creates_document(
    session: Session,
) -> None:
    repository = DocumentRepository(session)

    document = create_document()

    saved = repository.save(document)
    session.commit()

    assert saved.id == document.id
    assert saved.title == document.title
    assert saved.file_name == "python.pdf"


def test_get_returns_document(
    session: Session,
) -> None:
    repository = DocumentRepository(session)

    document = create_document()

    repository.save(document)
    session.commit()

    result = repository.get(document.id)

    assert result is not None
    assert result.id == document.id
    assert result.title == document.title


def test_get_returns_none_for_unknown_document(
    session: Session,
) -> None:
    repository = DocumentRepository(session)

    assert repository.get("unknown") is None


def test_get_all_returns_documents(
    session: Session,
) -> None:
    repository = DocumentRepository(session)

    repository.save(
        create_document(
            document_id="document-2",
            title="Zeta",
        )
    )

    repository.save(
        create_document(
            document_id="document-1",
            title="Alpha",
        )
    )

    session.commit()

    documents = repository.get_all()

    assert len(documents) == 2
    assert documents[0].title == "Alpha"
    assert documents[1].title == "Zeta"


def test_get_by_external_id(
    session: Session,
) -> None:
    repository = DocumentRepository(session)

    document = create_document()

    repository.save(document)
    session.commit()

    result = repository.get_by_external_id(
        "example",
        "external-document-1",
    )

    assert result is not None
    assert result.id == document.id


def test_save_updates_document(
    session: Session,
) -> None:
    repository = DocumentRepository(session)

    document = create_document()

    repository.save(document)
    session.commit()

    updated = document.model_copy(
        update={
            "title": "Apuntes avanzados",
            "file_name": "python-avanzado.pdf",
        }
    )

    repository.save(updated)
    session.commit()

    result = repository.get(document.id)

    assert result is not None
    assert result.title == "Apuntes avanzados"
    assert result.file_name == "python-avanzado.pdf"


def test_delete_document(
    session: Session,
) -> None:
    repository = DocumentRepository(session)

    document = create_document()

    repository.save(document)
    session.commit()

    assert repository.delete_by_id(document.id) is True

    session.commit()

    assert repository.get(document.id) is None


def test_delete_unknown_document_returns_false(
    session: Session,
) -> None:
    repository = DocumentRepository(session)

    assert repository.delete_by_id("unknown") is False