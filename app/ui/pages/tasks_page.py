from collections.abc import Callable

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.core.models import Assignment, AssignmentStatus
from app.infrastructure.database.database import SessionLocal
from app.services import TaskService
from app.ui.dialogs.task_dialog import TaskDialog
from app.ui.resources.icons import IconButton, svg_pixmap

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
    "local": "Locales",
    "external": "Externas",
}

EXTERNAL_TOOLTIP = (
    "Tarea externa: solo lectura. Se completará cuando la complete "
    "el servicio externo."
)


class TasksPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self._filter = "all"
        self._tasks: list[Assignment] = []
        self._load_failed = False
        self.filter_buttons: dict[str, QPushButton] = {}

        self._setup_ui()
        self._refresh_tasks()

    # ------------------------------------------------------------------ UI

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(40, 40, 40, 30)
        root_layout.setSpacing(8)

        # Cabecera: título + botón de nueva tarea
        header = QHBoxLayout()

        title = QLabel("Tareas")
        title.setObjectName("pageTitle")

        new_button = IconButton("Nueva tarea", "add", variant="primary")
        new_button.clicked.connect(self._create_task)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(new_button, 0, Qt.AlignmentFlag.AlignVCenter)

        description = QLabel(
            "Crea tus propias tareas y consulta las de Google Classroom, "
            "Moodle y otras fuentes. Las externas son de solo lectura."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        root_layout.addLayout(header)
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
                self._tasks = TaskService(session).list_tasks()
            self._load_failed = False
        except Exception:
            self._tasks = []
            self._load_failed = True

        self._render()

    @staticmethod
    def _sort_key(task: Assignment):
        completed = task.status.value == "completed"
        due = task.due_date
        return (completed, due is None, due.timestamp() if due else 0)

    def _visible_tasks(self) -> list[Assignment]:
        if self._filter == "pending":
            tasks = [t for t in self._tasks if t.status.value != "completed"]
        elif self._filter == "completed":
            tasks = [t for t in self._tasks if t.status.value == "completed"]
        elif self._filter == "local":
            tasks = [t for t in self._tasks if t.is_local]
        elif self._filter == "external":
            tasks = [t for t in self._tasks if not t.is_local]
        else:
            tasks = list(self._tasks)

        return sorted(tasks, key=self._sort_key)

    # ------------------------------------------------------------- acciones

    def _run(
        self,
        operation: Callable[[TaskService], object],
        error_title: str,
    ) -> bool:
        """Ejecuta una operación del servicio y refresca la lista."""
        try:
            with SessionLocal() as session:
                operation(TaskService(session))
        except Exception as exc:
            QMessageBox.critical(self, error_title, str(exc))
            return False

        self._refresh_tasks()
        return True

    def _create_task(self) -> None:
        dialog = TaskDialog(self)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()

        self._run(
            lambda service: service.create(
                title=data.title,
                description=data.description,
                course_name=data.course_name,
                due_date=data.due_date,
                status=data.status,
            ),
            "No se pudo crear la tarea.",
        )

    def _edit_task(self, task: Assignment) -> None:
        dialog = TaskDialog(self, task=task)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_data()

        self._run(
            lambda service: service.update(
                task.id,
                title=data.title,
                description=data.description,
                course_name=data.course_name,
                due_date=data.due_date,
                status=data.status,
            ),
            "No se pudo guardar la tarea.",
        )

    def _toggle_task(self, task: Assignment) -> None:
        if task.status == AssignmentStatus.COMPLETED:
            new_status = AssignmentStatus.PENDING
        else:
            new_status = AssignmentStatus.COMPLETED

        self._run(
            lambda service: service.set_status(task.id, new_status),
            "No se pudo cambiar el estado de la tarea.",
        )

    def _delete_task(self, task: Assignment) -> None:
        answer = QMessageBox.question(
            self,
            "Eliminar tarea",
            f"¿Eliminar la tarea «{task.title}»?\n\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self._run(
            lambda service: service.delete(task.id),
            "No se pudo eliminar la tarea.",
        )

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
        local = sum(1 for t in self._tasks if t.is_local)

        counts = {
            "all": total,
            "pending": total - completed,
            "completed": completed,
            "local": local,
            "external": total - local,
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
            title_text = "Todavía no tienes tareas"
            hint_text = (
                "Crea una con «Nueva tarea» o conecta un plugin en "
                "Conexiones y sincroniza."
            )
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

    def _create_task_row(self, task: Assignment) -> QFrame:
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

        title_row = QHBoxLayout()
        title_row.setSpacing(10)

        title = QLabel(task.title)
        title.setObjectName("taskTitle")
        title.setProperty("state", status)
        title.setTextFormat(Qt.TextFormat.PlainText)
        title.setWordWrap(True)

        if status == "completed":
            font = QFont(title.font())
            font.setStrikeOut(True)
            title.setFont(font)

        title_row.addWidget(title, 1)
        title_row.addWidget(
            self._create_origin_badge(task),
            0,
            Qt.AlignmentFlag.AlignTop,
        )

        content.addLayout(title_row)

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

        # Estado + acciones
        side = QVBoxLayout()
        side.setSpacing(8)
        side.setAlignment(Qt.AlignmentFlag.AlignTop)

        status_label = QLabel(status_text)
        status_label.setObjectName("taskStatus")
        status_label.setProperty("state", status)
        status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        side.addWidget(status_label)

        if task.is_local:
            side.addLayout(self._create_local_actions(task))

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

    def _create_origin_badge(self, task: Assignment) -> QLabel:
        badge = QLabel("Local" if task.is_local else "Externa")
        badge.setObjectName("taskBadge")
        badge.setProperty("origin", "local" if task.is_local else "external")

        if not task.is_local:
            badge.setToolTip(EXTERNAL_TOOLTIP)

        return badge

    def _create_local_actions(self, task: Assignment) -> QHBoxLayout:
        completed = task.status == AssignmentStatus.COMPLETED

        actions = QHBoxLayout()
        actions.setSpacing(6)
        actions.addStretch()

        actions.addWidget(
            self._create_icon_action(
                "undo" if completed else "check_circle",
                "Marcar como pendiente" if completed else "Marcar como completada",
                "secondary",
                lambda checked=False, t=task: self._toggle_task(t),
            )
        )
        actions.addWidget(
            self._create_icon_action(
                "edit",
                "Editar tarea",
                "secondary",
                lambda checked=False, t=task: self._edit_task(t),
            )
        )
        actions.addWidget(
            self._create_icon_action(
                "delete",
                "Eliminar tarea",
                "danger",
                lambda checked=False, t=task: self._delete_task(t),
            )
        )

        return actions

    @staticmethod
    def _create_icon_action(
        icon_name: str,
        tooltip: str,
        variant: str,
        slot: Callable[..., None],
    ) -> IconButton:
        button = IconButton("", icon_name, variant=variant)
        button.setProperty("iconOnly", "true")
        button.setFixedSize(32, 32)
        button.setToolTip(tooltip)
        button.clicked.connect(slot)
        return button

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