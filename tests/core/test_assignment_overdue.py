from datetime import datetime, timedelta, timezone

from app.core.models import Assignment, AssignmentStatus

NOW = datetime(2026, 10, 13, 12, 0)


def make_task(
    status: AssignmentStatus = AssignmentStatus.PENDING,
    due_date: datetime | None = None,
) -> Assignment:
    return Assignment(
        id="task-1",
        title="Tarea",
        status=status,
        due_date=due_date,
        source="local",
        external_id="task-1",
    )


def test_pending_task_past_due_is_overdue() -> None:
    task = make_task(due_date=NOW - timedelta(hours=1))

    assert task.effective_status(NOW) == AssignmentStatus.OVERDUE


def test_in_progress_task_past_due_is_overdue() -> None:
    task = make_task(
        status=AssignmentStatus.IN_PROGRESS,
        due_date=NOW - timedelta(days=2),
    )

    assert task.effective_status(NOW) == AssignmentStatus.OVERDUE


def test_completed_task_past_due_stays_completed() -> None:
    task = make_task(
        status=AssignmentStatus.COMPLETED,
        due_date=NOW - timedelta(days=2),
    )

    assert task.effective_status(NOW) == AssignmentStatus.COMPLETED


def test_task_without_due_date_keeps_status() -> None:
    task = make_task()

    assert task.effective_status(NOW) == AssignmentStatus.PENDING


def test_task_with_future_due_date_keeps_status() -> None:
    task = make_task(due_date=NOW + timedelta(hours=1))

    assert task.effective_status(NOW) == AssignmentStatus.PENDING


def test_timezone_aware_dates_are_compared_correctly() -> None:
    now = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)
    task = make_task(due_date=datetime(2026, 10, 13, 9, 0, tzinfo=timezone.utc))

    assert task.effective_status(now) == AssignmentStatus.OVERDUE


def test_effective_status_does_not_modify_stored_status() -> None:
    task = make_task(due_date=NOW - timedelta(hours=1))

    task.effective_status(NOW)

    assert task.status == AssignmentStatus.PENDING
