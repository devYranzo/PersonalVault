from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ConnectionsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("Conexiones")
        title.setObjectName("pageTitle")

        description = QLabel(
            "Conecta Google Classroom, Moodle, Google Drive, Calendar y otros servicios."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()
