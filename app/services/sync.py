from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.models import Assignment, Course, Document, Event
from app.core.plugins import Plugin
from app.infrastructure.database.repositories import (
    AssignmentRepository,
    CourseRepository,
    DocumentRepository,
    EventRepository,
)


@dataclass
class SyncResult:
    courses: int = 0
    assignments: int = 0
    events: int = 0
    documents: int = 0

    @property
    def total(self) -> int:
        return (
            self.courses
            + self.assignments
            + self.events
            + self.documents
        )


class SyncService:
    def __init__(
        self,
        session: Session,
        plugin: Plugin,
    ) -> None:
        self.session = session
        self.plugin = plugin

        self.course_repository = CourseRepository(session)
        self.assignment_repository = AssignmentRepository(session)
        self.event_repository = EventRepository(session)
        self.document_repository = DocumentRepository(session)

    def sync(self) -> SyncResult:
        result = SyncResult()

        try:
            result.courses = self.sync_courses()
            result.assignments = self.sync_assignments()
            result.events = self.sync_events()
            result.documents = self.sync_documents()

            self.session.commit()

        except Exception:
            self.session.rollback()
            raise

        return result

    def sync_courses(self) -> int:
        courses = self.plugin.get_courses()

        for course in courses:
            self.course_repository.save(course)

        return len(courses)

    def sync_assignments(self) -> int:
        assignments = self.plugin.get_assignments()

        for assignment in assignments:
            self.assignment_repository.save(assignment)

        return len(assignments)

    def sync_events(self) -> int:
        events = self.plugin.get_events()

        for event in events:
            self.event_repository.save(event)

        return len(events)

    def sync_documents(self) -> int:
        documents = self.plugin.get_documents()

        for document in documents:
            self.document_repository.save(document)

        return len(documents)