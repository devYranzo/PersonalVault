from app.infrastructure.database.repositories.assignment import (
    AssignmentRepository,
)
from app.infrastructure.database.repositories.base import (
    BaseRepository,
)
from app.infrastructure.database.repositories.course import (
    CourseRepository,
)
from app.infrastructure.database.repositories.document import (
    DocumentRepository,
)
from app.infrastructure.database.repositories.event import (
    EventRepository,
)

__all__ = [
    "AssignmentRepository",
    "BaseRepository",
    "CourseRepository",
    "DocumentRepository",
    "EventRepository",
]
