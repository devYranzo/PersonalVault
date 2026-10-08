from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.infrastructure.database.database import SessionLocal
from app.infrastructure.database.repositories import (
    AssignmentRepository,
    EventRepository,
)
from app.ui.resources.icons import IconButton, svg_pixmap

MONTHS = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]
WEEKDAYS_SHORT = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
WEEKDAYS_LONG = [
    "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo",
]

MAX_DOTS = 4
PANEL_WIDTH = 320

# kind -> (icono del panel, color del icono)
KIND_ICONS = {
    "task": ("assignment", "#3a414c"),
    "done": ("check_circle", "#22a559"),
    "overdue": ("error", "#d92d20"),
    "event": ("event", "#0e8a9a"),
}


@dataclass
class CalendarItem:
    kind: str          # task | done | overdue | event
    title: str
    when: datetime
    subtitle: str = ""


# ---------------------------------------------------------------------------
# Adaptadores: único sitio donde se leen los campos de los modelos.
# Si tu modelo Event usa otros nombres de atributo, cámbialos aquí.
# ---------------------------------------------------------------------------

def _first_attr(obj, names):
    for name in names:
        value = getattr(obj, name, None)
        if value:
            return value
    return None


def _as_local_datetime(value) -> datetime | None:
    if isinstance(value, datetime):
        return value.astimezone().replace(tzinfo=None) if value.tzinfo else value

    if isinstance(value, date):
        return datetime.combine(value, time.min)

    return None


def _task_to_item(task) -> CalendarItem | None:
    when = _as_local_datetime(task.due_date)

    if when is None:
        return None

    status = task.status.value
    kind = {"completed": "done", "overdue": "overdue"}.get(status, "task")

    return CalendarItem(
        kind=kind,
        title=task.title,
        when=when,
        subtitle=task.course_name or "",
    )


def _event_to_item(event) -> CalendarItem | None:
    when = _as_local_datetime(
        _first_attr(
            event,
            ("start_date", "start", "start_time", "starts_at", "date", "begin"),
        )
    )

    if when is None:
        return None

    return CalendarItem(
        kind="event",
        title=str(_first_attr(event, ("title", "name", "summary")) or "Evento"),
        when=when,
        subtitle=str(_first_attr(event, ("location", "course_name")) or ""),
    )


# ---------------------------------------------------------------------------
# Celda de día
# ---------------------------------------------------------------------------

class DayCell(QFrame):
    clicked = Signal(date)

    def __init__(
        self,
        day: date,
        in_month: bool,
        is_today: bool,
        is_selected: bool,
        items: list[CalendarItem],
    ) -> None:
        super().__init__()

        self.day = day

        self.setObjectName("dayCell")
        self.setProperty("outside", "false" if in_month else "true")
        self.setProperty("selected", "true" if is_selected else "false")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumSize(70, 58)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        number = QLabel(str(day.day))
        number.setObjectName("dayNumber")
        number.setProperty("outside", "false" if in_month else "true")
        number.setProperty("today", "true" if is_today else "false")
        number.setAlignment(Qt.AlignmentFlag.AlignCenter)
        number.setMinimumSize(22, 22)
        layout.addWidget(number, 0, Qt.AlignmentFlag.AlignLeft)

        if items:
            dots = QHBoxLayout()
            dots.setSpacing(4)

            for item in sorted(items, key=lambda i: i.when)[:MAX_DOTS]:
                dots.addWidget(make_dot(item.kind))

            extra = len(items) - MAX_DOTS
            if extra > 0:
                more = QLabel(f"+{extra}")
                more.setObjectName("calendarMore")
                dots.addWidget(more)

            dots.addStretch()
            layout.addLayout(dots)

        layout.addStretch(1)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.day)

        super().mousePressEvent(event)


def make_dot(kind: str) -> QLabel:
    dot = QLabel()
    dot.setObjectName("calendarDot")
    dot.setProperty("kind", kind)
    dot.setFixedSize(7, 7)
    return dot


# ---------------------------------------------------------------------------
# Página
# ---------------------------------------------------------------------------

class CalendarPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        today = date.today()

        self._selected: date = today
        self._month: date = today.replace(day=1)
        self._items: dict[date, list[CalendarItem]] = {}
        self._load_failed = False

        self._setup_ui()
        self._reload()

    # ------------------------------------------------------------------ UI

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(40, 40, 40, 30)
        root_layout.setSpacing(8)

        body = QHBoxLayout()
        body.setSpacing(24)

        body.addLayout(self._create_calendar_column(), 1)
        body.addWidget(self._create_side_panel())

        root_layout.addLayout(body, 1)

    def _create_calendar_column(self) -> QVBoxLayout:
        column = QVBoxLayout()
        column.setSpacing(12)

        # Barra: mes + navegación
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        self.month_label = QLabel()
        self.month_label.setObjectName("calendarMonth")

        previous_button = IconButton("", "chevron_left", icon_size=20)
        previous_button.setToolTip("Mes anterior")
        previous_button.clicked.connect(lambda: self._change_month(-1))

        next_button = IconButton("", "chevron_right", icon_size=20)
        next_button.setToolTip("Mes siguiente")
        next_button.clicked.connect(lambda: self._change_month(1))

        for button in (previous_button, next_button):
            button.setProperty("iconOnly", "true")
            button.setFixedSize(34, 34)

        today_button = QPushButton("Hoy")
        today_button.setProperty("variant", "secondary")
        today_button.setCursor(Qt.CursorShape.PointingHandCursor)
        today_button.clicked.connect(self._go_today)

        toolbar.addWidget(self.month_label)
        toolbar.addStretch()
        toolbar.addWidget(today_button)
        toolbar.addSpacing(6)
        toolbar.addWidget(previous_button)
        toolbar.addWidget(next_button)

        column.addLayout(toolbar)

        # Cabecera de días + cuadrícula en el mismo grid (columnas alineadas)
        self.grid_container = QWidget()
        self.grid = QGridLayout(self.grid_container)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(6)

        for col in range(7):
            self.grid.setColumnStretch(col, 1)

        for row in range(1, 7):
            self.grid.setRowStretch(row, 1)

        column.addWidget(self.grid_container, 1)

        column.addLayout(self._create_legend())

        return column

    def _create_legend(self) -> QHBoxLayout:
        legend = QHBoxLayout()
        legend.setSpacing(6)

        for kind, text in (
            ("task", "Tarea"),
            ("done", "Completada"),
            ("overdue", "Atrasada"),
            ("event", "Evento"),
        ):
            legend.addWidget(make_dot(kind))

            label = QLabel(text)
            label.setObjectName("calendarLegend")
            legend.addWidget(label)
            legend.addSpacing(10)

        legend.addStretch()

        return legend

    def _create_side_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("calendarPanel")
        panel.setFixedWidth(PANEL_WIDTH)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(2)

        self.panel_title = QLabel()
        self.panel_title.setObjectName("panelTitle")

        self.panel_subtitle = QLabel()
        self.panel_subtitle.setObjectName("panelSubtitle")

        layout.addWidget(self.panel_title)
        layout.addWidget(self.panel_subtitle)
        layout.addSpacing(12)

        container = QWidget()
        container.setObjectName("pageContainer")

        self.panel_list = QVBoxLayout(container)
        self.panel_list.setContentsMargins(0, 0, 6, 0)
        self.panel_list.setSpacing(8)

        scroll = QScrollArea()
        scroll.setObjectName("pageScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(container)

        layout.addWidget(scroll, 1)

        return panel

    # --------------------------------------------------------------- datos

    def _reload(self) -> None:
        """Carga tareas y eventos desde SQLite y repinta."""
        items: dict[date, list[CalendarItem]] = {}

        try:
            with SessionLocal() as session:
                tasks = AssignmentRepository(session).get_all()
                events = EventRepository(session).get_all()

            candidates = [_task_to_item(t) for t in tasks]
            candidates += [_event_to_item(e) for e in events]

            for item in candidates:
                if item is not None:
                    items.setdefault(item.when.date(), []).append(item)

            self._load_failed = False
        except Exception:
            self._load_failed = True

        self._items = items
        self._render()

    # ---------------------------------------------------------- navegación

    def _change_month(self, delta: int) -> None:
        month_index = self._month.year * 12 + (self._month.month - 1) + delta
        self._month = date(month_index // 12, month_index % 12 + 1, 1)
        self._render_grid()

    def _go_today(self) -> None:
        today = date.today()
        self._selected = today
        self._month = today.replace(day=1)
        self._render()

    def _select_day(self, day: date) -> None:
        self._selected = day

        if (day.year, day.month) != (self._month.year, self._month.month):
            self._month = day.replace(day=1)

        self._render()

    # --------------------------------------------------------------- render

    def _render(self) -> None:
        self._render_grid()
        self._render_panel()

    def _render_grid(self) -> None:
        # Vacía el grid
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        self.month_label.setText(
            f"{MONTHS[self._month.month - 1]} {self._month.year}"
        )

        for col, name in enumerate(WEEKDAYS_SHORT):
            label = QLabel(name)
            label.setObjectName("calendarWeekday")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(label, 0, col)

        today = date.today()
        start = self._month - timedelta(days=self._month.weekday())

        for index in range(42):
            day = start + timedelta(days=index)

            cell = DayCell(
                day=day,
                in_month=day.month == self._month.month,
                is_today=day == today,
                is_selected=day == self._selected,
                items=self._items.get(day, []),
            )
            cell.clicked.connect(self._select_day)

            self.grid.addWidget(cell, 1 + index // 7, index % 7)

    def _render_panel(self) -> None:
        while self.panel_list.count():
            item = self.panel_list.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        day = self._selected

        self.panel_title.setText(
            f"{WEEKDAYS_LONG[day.weekday()]}, {day.day} de "
            f"{MONTHS[day.month - 1].lower()}"
        )

        if self._load_failed:
            self.panel_subtitle.setText("No se han podido cargar los datos.")
            self.panel_list.addStretch(1)
            return

        items = sorted(self._items.get(day, []), key=lambda i: i.when)

        if not items:
            self.panel_subtitle.setText("Nada programado")
        else:
            self.panel_subtitle.setText(
                "1 elemento" if len(items) == 1 else f"{len(items)} elementos"
            )

        for item in items:
            self.panel_list.addWidget(self._create_item_row(item))

        self.panel_list.addStretch(1)

    def _create_item_row(self, item: CalendarItem) -> QFrame:
        row = QFrame()
        row.setObjectName("calendarItem")
        row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        icon_name, color = KIND_ICONS[item.kind]

        icon = QLabel()
        icon.setPixmap(svg_pixmap(icon_name, color, 18))
        icon.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(icon)

        text = QVBoxLayout()
        text.setSpacing(2)

        title = QLabel(item.title)
        title.setObjectName("calendarItemTitle")
        title.setTextFormat(Qt.TextFormat.PlainText)
        title.setWordWrap(True)
        text.addWidget(title)

        meta_parts = []

        if item.when.time() != time.min:
            meta_parts.append(item.when.strftime("%H:%M"))

        if item.subtitle:
            meta_parts.append(item.subtitle)

        if meta_parts:
            meta = QLabel("  ·  ".join(meta_parts))
            meta.setObjectName("calendarItemMeta")
            meta.setTextFormat(Qt.TextFormat.PlainText)
            meta.setWordWrap(True)
            text.addWidget(meta)

        layout.addLayout(text, 1)

        return row

    def showEvent(self, event) -> None:
        """Recarga los datos cada vez que se muestra la página."""
        super().showEvent(event)
        self._reload()
