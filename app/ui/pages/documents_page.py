from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.infrastructure.database.database import SessionLocal
from app.infrastructure.database.repositories import DocumentRepository


class DocumentsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)

        title = QLabel("Documentos")
        title.setObjectName("pageTitle")

        description = QLabel(
            "Gestiona apuntes, PDFs, documentos y otros archivos del Vault."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        self.documents_container = QVBoxLayout()
        self.documents_container.setSpacing(10)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(self.documents_container)
        layout.addStretch()

        self._refresh_documents()

    def _clear_documents(self) -> None:
        """Elimina los elementos de documentos existentes."""
        while self.documents_container.count():
            item = self.documents_container.takeAt(0)

            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _refresh_documents(self) -> None:
        """Carga los documentos actuales desde SQLite."""
        self._clear_documents()

        try:
            with SessionLocal() as session:
                documents = DocumentRepository(session).get_all()
        except Exception:
            error_label = QLabel(
                "No se han podido cargar los documentos."
            )
            error_label.setObjectName("pageDescription")
            self.documents_container.addWidget(error_label)
            return

        if not documents:
            empty_label = QLabel(
                "No hay documentos sincronizados todavía."
            )
            empty_label.setObjectName("pageDescription")
            self.documents_container.addWidget(empty_label)
            return

        for document in documents:
            document_label = self._create_document_label(document)
            self.documents_container.addWidget(document_label)

    def _create_document_label(self, document) -> QLabel:
        """Crea la representación visual de un documento."""
        text = document.title

        if document.file_name:
            text += f"\nArchivo: {document.file_name}"

        if document.mime_type:
            text += f"\nTipo: {document.mime_type}"

        if document.course_name:
            text += f"\nCurso: {document.course_name}"

        if document.path:
            text += f"\nRuta: {document.path}"

        if document.url:
            text += f"\n{document.url}"

        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.setObjectName("documentItem")

        return label

    def showEvent(self, event) -> None:
        """Refresca los documentos cada vez que se muestra la página."""
        super().showEvent(event)
        self._refresh_documents()