from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class TasksPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("Tareas")
        title.setObjectName("pageTitle")

        description = QLabel(
            "Aquí aparecerán tus tareas de Google Classroom, Moodle y otras fuentes."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()
