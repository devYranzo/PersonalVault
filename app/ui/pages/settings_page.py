from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SettingsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("Ajustes")
        title.setObjectName("pageTitle")

        description = QLabel(
            "Configuración general, apariencia, almacenamiento y preferencias."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()
