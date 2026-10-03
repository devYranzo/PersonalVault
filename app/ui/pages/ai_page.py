from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class AIPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("AI")
        title.setObjectName("pageTitle")

        description = QLabel(
            "Chat con tu conocimiento personal, planificación de estudio y otras funciones de IA."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()
