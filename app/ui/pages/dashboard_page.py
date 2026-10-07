from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from app.infrastructure.database.database import SessionLocal
from app.infrastructure.database.repositories import (
    AssignmentRepository,
    EventRepository,
)
from app.ui.layouts.flow_layout import FlowLayout, FlowScrollArea
from app.ui.resources.icons import svg_pixmap

CARD_WIDTH = 180

# clave -> (icono, etiqueta)
STAT_CARDS = {
    "pending": ("pending_actions", "Tareas pendientes"),
    "events": ("event", "Eventos"),
}


class DashboardPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.stat_numbers: dict[str, QLabel] = {}
        self.stat_hints: dict[str, QLabel] = {}

        self._setup_ui()

        self._update_greeting()
        self._refresh_data()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_greeting)
        self.timer.start(60000)

    # ------------------------------------------------------------------ UI

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(40, 40, 40, 30)
        root_layout.setSpacing(8)

        self.title = QLabel()
        self.title.setObjectName("pageTitle")

        description = QLabel(
            "Aquí tendrás una visión general de tus tareas y eventos."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        section = QLabel("Resumen del Vault")
        section.setObjectName("sectionTitle")

        self.error_label = QLabel(
            "No se han podido cargar las estadísticas del Vault."
        )
        self.error_label.setObjectName("dashboardError")
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        root_layout.addWidget(self.title)
        root_layout.addWidget(description)
        root_layout.addSpacing(20)
        root_layout.addWidget(section)
        root_layout.addSpacing(4)
        root_layout.addWidget(self.error_label)

        container = QWidget()
        container.setObjectName("pageContainer")

        grid = FlowLayout(container, h_spacing=16, v_spacing=16)
        grid.setContentsMargins(0, 0, 8, 8)

        for key, (icon_name, label) in STAT_CARDS.items():
            grid.addWidget(self._create_stat_card(key, icon_name, label))

        self.scroll = FlowScrollArea()
        self.scroll.setObjectName("pageScroll")
        self.scroll.setWidget(container)

        root_layout.addWidget(self.scroll, 1)

    def _create_stat_card(self, key: str, icon_name: str, label: str) -> QFrame:
        card = QFrame()
        card.setObjectName("statCard")
        card.setFixedWidth(CARD_WIDTH)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(2)

        icon = QLabel()
        icon.setObjectName("statIcon")
        icon.setFixedSize(36, 36)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setPixmap(svg_pixmap(icon_name, "#3a414c", 20))

        number = QLabel("–")
        number.setObjectName("statNumber")

        text = QLabel(label)
        text.setObjectName("statLabel")

        hint = QLabel()
        hint.setObjectName("statHint")
        hint.hide()

        layout.addWidget(icon)
        layout.addSpacing(10)
        layout.addWidget(number)
        layout.addWidget(text)
        layout.addWidget(hint)

        self.stat_numbers[key] = number
        self.stat_hints[key] = hint

        return card

    # ------------------------------------------------------------- saludo

    def _get_greeting(self) -> str:
        hour = datetime.now().hour

        if 6 <= hour < 12:
            return "¡Buenos días, usuario!"
        elif 12 <= hour < 20:
            return "¡Buenas tardes, usuario!"
        else:
            return "¡Buenas noches, usuario!"

    def _update_greeting(self) -> None:
        """Actualiza el saludo según la hora actual."""
        new_greeting = self._get_greeting()

        if self.title.text() != new_greeting:
            self.title.setText(new_greeting)

    # -------------------------------------------------------------- datos

    def _refresh_data(self) -> None:
        """Carga las estadísticas actuales desde SQLite."""
        try:
            with SessionLocal() as session:
                assignments = AssignmentRepository(session).get_all()
                events = EventRepository(session).get_all()
        except Exception:
            self.error_label.show()
            self.scroll.hide()
            return

        self.error_label.hide()
        self.scroll.show()

        pending_assignments = [
            assignment
            for assignment in assignments
            if assignment.status.value != "completed"
        ]

        self._set_stat(
            "pending",
            len(pending_assignments),
        )
        self._set_stat("events", len(events))

    def _set_stat(self, key: str, value: int, hint: str | None = None) -> None:
        self.stat_numbers[key].setText(str(value))

        hint_label = self.stat_hints[key]
        hint_label.setVisible(bool(hint))
        hint_label.setText(hint or "")

    def showEvent(self, event) -> None:
        """Refresca los datos cada vez que se muestra el Dashboard."""
        super().showEvent(event)
        self._refresh_data()