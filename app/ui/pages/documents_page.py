from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class DocumentsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("Documentos")
        title.setObjectName("pageTitle")

        description = QLabel(
            "Gestiona apuntes, PDFs, documentos y otros archivos del Vault."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()
