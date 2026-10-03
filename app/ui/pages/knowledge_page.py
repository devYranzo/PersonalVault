from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class KnowledgePage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("Knowledge")
        title.setObjectName("pageTitle")

        description = QLabel(
            "Aquí construiremos la base de conocimiento y posteriormente el RAG."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()
