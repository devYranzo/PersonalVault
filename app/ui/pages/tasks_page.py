from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.infrastructure.database.database import SessionLocal
from app.infrastructure.database.repositories import AssignmentRepository
from app.ui.resources.icons import IconButton, svg_pixmap  # ajusta la ruta

LIST_MAX_WIDTH = 920
DESCRIPTION_MAX_CHARS = 180

# status -> (texto, icono, color del icono)
STATUS_INFO = {
    "pending": ("Pendiente", "radio_button_unchecked", "#9ca3af"),
    "in_progress": ("En progreso", "schedule", "#d49a00"),
    "completed": ("Completada", "check_circle", "#22a559"),
    "overdue": ("Atrasada", "error", "#d92d20"),
}

FILTERS = {
    "all": "Todas",
    "pending": "Pendientes",
    "completed": "Completadas",
}


class TasksPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self._filter = "all"
        self._tasks: list = []
        self._load_failed = False
        self.filter_buttons: dict[str, QPushButton] = {}

        self._setup_ui()
        self._refresh_tasks()

    # ------------------------------------------------------------------ UI

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(40, 40, 40, 30)
        root_layout.setSpacing(8)

        title = QLabel("Tareas")
        title.setObjectName("pageTitle")

        description = QLabel(
            "Aquí aparecerán tus tareas de Google Classroom, Moodle y otras fuentes."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        root_layout.addWidget(title)
        root_layout.addWidget(description)
        root_layout.addSpacing(12)

        # Filtros
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(4)

        group = QButtonGroup(self)
        group.setExclusive(True)

        for key, label in FILTERS.items():
            button = QPushButton(label)
            button.setProperty("variant", "segment")
            button.setCheckable(True)
            button.setChecked(key == self._filter)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda checked=False, k=key: self._set_filter(k),
            )

            group.addButton(button)
            filters_layout.addWidget(button)
            self.filter_buttons[key] = button

        filters_layout.addStretch()
        root_layout.addLayout(filters_layout)
        root_layout.addSpacing(4)

        # Lista con scroll
        self.list_container = QWidget()
        self.list_container.setObjectName("pageContainer")
        self.list_container.setMaximumWidth(LIST_MAX_WIDTH)

        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 8, 8)
        self.list_layout.setSpacing(10)

        scroll = QScrollArea()
        scroll.setObjectName("pageScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self.list_container)

        root_layout.addWidget(scroll, 1)

    # --------------------------------------------------------------- datos

    def _set_filter(self, key: str) -> None:
        self._filter = key
        self._render()

    def _refresh_tasks(self) -> None:
        """Carga las tareas actuales desde SQLite."""
        try:
            with SessionLocal() as session:
                self._tasks = list(AssignmentRepository(session).get_all())
            self._load_failed = False
        except Exception:
            self._tasks = []
            self._load_failed = True

        self._render()

    @staticmethod
    def _sort_key(task):
        completed = task.status.value == "completed"
        due = task.due_date
        return (completed, due is None, due.timestamp() if due else 0)

    def _visible_tasks(self) -> list:
        if self._filter == "pending":
            tasks = [t for t in self._tasks if t.status.value != "completed"]
        elif self._filter == "completed":
            tasks = [t for t in self._tasks if t.status.value == "completed"]
        else:
            tasks = list(self._tasks)

        return sorted(tasks, key=self._sort_key)

    # --------------------------------------------------------------- render

    def _render(self) -> None:
        self._clear_list()
        self._update_filter_counts()

        if self._load_failed:
            error = QLabel("No se han podido cargar las tareas.")
            error.setObjectName("dashboardError")
            self.list_layout.addWidget(error)
            self.list_layout.addStretch(1)
            return

        tasks = self._visible_tasks()

        if not tasks:
            self.list_layout.addWidget(self._create_empty_state())
        else:
            for task in tasks:
                self.list_layout.addWidget(self._create_task_row(task))

        self.list_layout.addStretch(1)

    def _clear_list(self) -> None:
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

    def _update_filter_counts(self) -> None:
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks if t.status.value == "completed")

        counts = {
            "all": total,
            "pending": total - completed,
            "completed": completed,
        }

        for key, button in self.filter_buttons.items():
            button.setText(f"{FILTERS[key]}  {counts[key]}")

    def _create_empty_state(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("emptyState")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(30, 36, 30, 36)
        layout.setSpacing(8)

        icon = QLabel()
        icon.setPixmap(svg_pixmap("assignment", "#9ca3af", 40))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if not self._tasks:
            title_text = "No hay tareas sincronizadas todavía"
            hint_text = "Conecta un plugin en Conexiones y sincroniza para verlas aquí."
        else:
            title_text = "No hay tareas en esta vista"
            hint_text = "Prueba con otro filtro."

        title = QLabel(title_text)
        title.setObjectName("emptyTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        hint = QLabel(hint_text)
        hint.setObjectName("emptyHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setWordWrap(True)

        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(hint)

        return frame

    def _create_task_row(self, task) -> QFrame:
        """Crea la representación visual de una tarea."""
        status = task.status.value
        status_text, status_icon, status_color = STATUS_INFO.get(
            status, (status, "radio_button_unchecked", "#9ca3af"),
        )

        row = QFrame()
        row.setObjectName("taskRow")
        # Altura = la que pide su contenido; nunca se estira con la ventana
        row.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        layout = QHBoxLayout(row)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)

        # Icono de estado
        icon = QLabel()
        icon.setPixmap(svg_pixmap(status_icon, status_color, 22))
        icon.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(icon)

        # Contenido
        content = QVBoxLayout()
        content.setSpacing(4)

        title = QLabel(task.title)
        title.setObjectName("taskTitle")
        title.setProperty("state", status)
        title.setTextFormat(Qt.TextFormat.PlainText)
        title.setWordWrap(True)

        if status == "completed":
            font = QFont(title.font())
            font.setStrikeOut(True)
            title.setFont(font)

        content.addWidget(title)

        meta = QHBoxLayout()
        meta.setSpacing(16)

        if task.course_name:
            meta.addLayout(self._create_meta("school", task.course_name))

        if task.due_date:
            due = task.due_date.strftime("%d/%m/%Y %H:%M")
            meta.addLayout(
                self._create_meta(
                    "event",
                    f"Entrega: {due}",
                    state="overdue" if status == "overdue" else None,
                )
            )

        meta.addStretch()
        content.addLayout(meta)

        if task.description:
            text = " ".join(task.description.split())

            if len(text) > DESCRIPTION_MAX_CHARS:
                text = text[:DESCRIPTION_MAX_CHARS].rstrip() + "…"

            description = QLabel(text)
            description.setObjectName("taskDescription")
            description.setTextFormat(Qt.TextFormat.PlainText)
            description.setWordWrap(True)
            content.addWidget(description)

        content.addStretch(1)
        layout.addLayout(content, 1)

        # Estado + acción
        side = QVBoxLayout()
        side.setSpacing(8)
        side.setAlignment(Qt.AlignmentFlag.AlignTop)

        status_label = QLabel(status_text)
        status_label.setObjectName("taskStatus")
        status_label.setProperty("state", status)
        status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        side.addWidget(status_label)

        if task.url:
            open_button = IconButton("Abrir", "open_in_new")
            open_button.setToolTip(task.url)
            open_button.clicked.connect(
                lambda checked=False, url=task.url: QDesktopServices.openUrl(QUrl(url)),
            )
            side.addWidget(open_button)

        side.addStretch()
        layout.addLayout(side)

        return row

    def _create_meta(self, icon_name: str, text: str, state: str | None = None) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(5)

        color = "#d92d20" if state == "overdue" else "#7b8390"

        icon = QLabel()
        icon.setPixmap(svg_pixmap(icon_name, color, 15))

        label = QLabel(text)
        label.setObjectName("taskMeta")
        label.setTextFormat(Qt.TextFormat.PlainText)

        if state:
            label.setProperty("state", state)

        layout.addWidget(icon)
        layout.addWidget(label)

        return layout

    def showEvent(self, event) -> None:
        """Refresca las tareas cada vez que se muestra la página."""
        super().showEvent(event)
        self._refresh_tasks()