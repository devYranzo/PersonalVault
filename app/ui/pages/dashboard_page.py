from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.infrastructure.database.database import SessionLocal
from app.infrastructure.database.repositories import (
    AssignmentRepository,
    CourseRepository,
    DocumentRepository,
    EventRepository,
)


class DashboardPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)

        self.title = QLabel()
        self.title.setObjectName("pageTitle")

        description = QLabel(
            "Aquí tendrás una visión general de tus estudios, tareas y eventos."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        self.stats = QLabel()
        self.stats.setObjectName("dashboardStats")
        self.stats.setWordWrap(True)

        layout.addWidget(self.title)
        layout.addWidget(description)
        layout.addWidget(self.stats)
        layout.addStretch()

        self._update_greeting()
        self._refresh_data()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_greeting)
        self.timer.start(60000)

    def _get_greeting(self) -> str:
        hour = datetime.now().hour

        if 6 <= hour < 12:
            return "¡Buenos días, usuario!"
        elif 12 <= hour < 20:
            return "¡Buenas tardes, usuario!"
        else:
            return "¡Buenas noches, usuario!"

    def _update_greeting(self) -> None:
        """Actualiza el saludo según la hora actual."""
        new_greeting = self._get_greeting()

        if self.title.text() != new_greeting:
            self.title.setText(new_greeting)

    def _refresh_data(self) -> None:
        """Carga las estadísticas actuales desde SQLite."""
        try:
            with SessionLocal() as session:
                courses = CourseRepository(session).get_all()
                assignments = AssignmentRepository(session).get_all()
                events = EventRepository(session).get_all()
                documents = DocumentRepository(session).get_all()
        except Exception:
            self.stats.setText(
                "No se han podido cargar las estadísticas del Vault."
            )
            return

        pending_assignments = [
            assignment
            for assignment in assignments
            if assignment.status.value != "completed"
        ]

        self.stats.setText(
            f"Información del Vault\n\n"
            f"Cursos: {len(courses)}\n"
            f"Tareas: {len(assignments)}\n"
            f"Tareas pendientes: {len(pending_assignments)}\n"
            f"Eventos: {len(events)}\n"
            f"Documentos: {len(documents)}"
        )

    def showEvent(self, event) -> None:
        """Refresca los datos cada vez que se muestra el Dashboard."""
        super().showEvent(event)
        self._refresh_data()