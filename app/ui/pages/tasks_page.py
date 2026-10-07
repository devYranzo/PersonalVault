from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.infrastructure.database.database import SessionLocal
from app.infrastructure.database.repositories import AssignmentRepository


class TasksPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)

        title = QLabel("Tareas")
        title.setObjectName("pageTitle")

        description = QLabel(
            "Aquí aparecerán tus tareas de Google Classroom, Moodle y otras fuentes."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        self.tasks_container = QVBoxLayout()
        self.tasks_container.setSpacing(10)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(self.tasks_container)
        layout.addStretch()

        self._refresh_tasks()

    def _clear_tasks(self) -> None:
        """Elimina las etiquetas de tareas existentes."""
        while self.tasks_container.count():
            item = self.tasks_container.takeAt(0)

            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _refresh_tasks(self) -> None:
        """Carga las tareas actuales desde SQLite."""
        self._clear_tasks()

        try:
            with SessionLocal() as session:
                tasks = AssignmentRepository(session).get_all()
        except Exception:
            error_label = QLabel(
                "No se han podido cargar las tareas."
            )
            error_label.setObjectName("pageDescription")
            self.tasks_container.addWidget(error_label)
            return

        if not tasks:
            empty_label = QLabel(
                "No hay tareas sincronizadas todavía."
            )
            empty_label.setObjectName("pageDescription")
            self.tasks_container.addWidget(empty_label)
            return

        for task in tasks:
            task_label = self._create_task_label(task)
            self.tasks_container.addWidget(task_label)

    def _create_task_label(self, task) -> QLabel:
        """Crea la representación visual de una tarea."""
        status = task.status.value

        status_labels = {
            "pending": "Pendiente",
            "in_progress": "En progreso",
            "completed": "Completada",
            "overdue": "Atrasada",
        }

        status_text = status_labels.get(status, status)

        text = f"{task.title} — {status_text}"

        if task.course_name:
            text += f"\nCurso: {task.course_name}"

        if task.due_date:
            due_date = task.due_date.strftime("%d/%m/%Y %H:%M")
            text += f"\nEntrega: {due_date}"

        if task.description:
            text += f"\n{task.description}"

        if task.url:
            text += f"\n{task.url}"

        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.setObjectName("taskItem")

        return label

    def showEvent(self, event) -> None:
        """Refresca las tareas cada vez que se muestra la página."""
        super().showEvent(event)
        self._refresh_tasks()