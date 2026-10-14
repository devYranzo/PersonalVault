from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.core.config import APP_NAME, APP_VERSION, DATA_DIR

ABOUT_CARD_MAX_WIDTH = 520


class AboutPage(QWidget):
    """Sección con información sobre la aplicación y su versión."""

    def __init__(self) -> None:
        super().__init__()

        self._setup_ui()

    # ------------------------------------------------------------------ UI

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(8)

        description = QLabel(
            "Información sobre esta instalación de Personal Vault."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        card = QFrame()
        card.setObjectName("settingsCard")
        card.setMaximumWidth(ABOUT_CARD_MAX_WIDTH)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(14)

        self._add_row(card_layout, "Aplicación", APP_NAME)
        self._add_row(card_layout, "Versión", APP_VERSION)
        self._add_row(card_layout, "Carpeta de datos", str(DATA_DIR))

        root_layout.addWidget(description)
        root_layout.addSpacing(8)
        root_layout.addWidget(card)
        root_layout.addStretch(1)

    # ------------------------------------------------------------- filas

    @staticmethod
    def _add_row(
        layout: QVBoxLayout,
        label: str,
        value: str,
    ) -> None:
        key_label = QLabel(label)
        key_label.setObjectName("settingsRowLabel")

        value_label = QLabel(value)
        value_label.setObjectName("settingsRowValue")
        value_label.setWordWrap(True)
        value_label.setTextFormat(Qt.TextFormat.PlainText)
        value_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse,
        )

        row = QVBoxLayout()
        row.setSpacing(2)
        row.addWidget(key_label)
        row.addWidget(value_label)

        layout.addLayout(row)