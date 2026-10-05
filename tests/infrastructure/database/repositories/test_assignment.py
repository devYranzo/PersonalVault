from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.models import Assignment, AssignmentStatus
from app.infrastructure.database.repositories import AssignmentRepository


def create_assignment(
    assignment_id: str = "assignment-1",
    title: str = "Práctica de Python",
) -> Assignment:
    now = datetime.now(timezone.utc)

    return Assignment(
        id=assignment_id,
        title=title,
        description="Descripción de la práctica",
        course_id="course-1",
        course_name="Programación",
        due_date=now + timedelta(days=7),
        status=AssignmentStatus.PENDING,
        source="example",
        external_id=f"external-{assignment_id}",
        url="https://example.com/assignment",
        created_at=now,
        updated_at=now,
    )


def test_save_creates_assignment(
    session: Session,
) -> None:
    repository = AssignmentRepository(session)

    assignment = create_assignment()

    saved = repository.save(assignment)
    session.commit()

    assert saved.id == assignment.id
    assert saved.title == assignment.title
    assert saved.status == AssignmentStatus.PENDING


def test_get_returns_assignment(
    session: Session,
) -> None:
    repository = AssignmentRepository(session)

    assignment = create_assignment()

    repository.save(assignment)
    session.commit()

    result = repository.get(assignment.id)

    assert result is not None
    assert result.id == assignment.id
    assert result.title == assignment.title


def test_get_returns_none_for_unknown_assignment(
    session: Session,
) -> None:
    repository = AssignmentRepository(session)

    assert repository.get("unknown") is None


def test_get_all_returns_assignments(
    session: Session,
) -> None:
    repository = AssignmentRepository(session)

    repository.save(
        create_assignment(
            assignment_id="assignment-2",
            title="Zeta",
        )
    )

    repository.save(
        create_assignment(
            assignment_id="assignment-1",
            title="Alpha",
        )
    )

    session.commit()

    assignments = repository.get_all()

    assert len(assignments) == 2
    assert assignments[0].title == "Alpha"
    assert assignments[1].title == "Zeta"


def test_get_by_external_id(
    session: Session,
) -> None:
    repository = AssignmentRepository(session)

    assignment = create_assignment()

    repository.save(assignment)
    session.commit()

    result = repository.get_by_external_id(
        "example",
        "external-assignment-1",
    )

    assert result is not None
    assert result.id == assignment.id


def test_save_updates_assignment(
    session: Session,
) -> None:
    repository = AssignmentRepository(session)

    assignment = create_assignment()

    repository.save(assignment)
    session.commit()

    updated = assignment.model_copy(
        update={
            "title": "Práctica avanzada",
            "status": AssignmentStatus.COMPLETED,
        }
    )

    repository.save(updated)
    session.commit()

    result = repository.get(assignment.id)

    assert result is not None
    assert result.title == "Práctica avanzada"
    assert result.status == AssignmentStatus.COMPLETED


def test_delete_assignment(
    session: Session,
) -> None:
    repository = AssignmentRepository(session)

    assignment = create_assignment()

    repository.save(assignment)
    session.commit()

    assert repository.delete_by_id(assignment.id) is True

    session.commit()

    assert repository.get(assignment.id) is None


def test_delete_unknown_assignment_returns_false(
    session: Session,
) -> None:
    repository = AssignmentRepository(session)

    assert repository.delete_by_id("unknown") is False