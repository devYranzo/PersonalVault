from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class DashboardPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("Dashboard")
        title.setObjectName("pageTitle")

        description = QLabel(
            "Aquí tendrás una visión general de tus estudios, tareas y eventos."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()
