from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import QDateTime, QLocale, QSize, Qt, QTime
from PySide6.QtGui import QColor, QFont, QIcon, QTextCharFormat
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QToolButton,
    QVBoxLayout,
)

from app.core.models import Assignment, AssignmentStatus
from app.ui.resources.icons import svg_pixmap

# «Atrasada» no es elegible: se calcula a partir de la fecha de entrega.
STATUS_LABELS = {
    AssignmentStatus.PENDING: "Pendiente",
    AssignmentStatus.IN_PROGRESS: "En progreso",
    AssignmentStatus.COMPLETED: "Completada",
}


@dataclass
class TaskFormData:
    title: str
    description: str | None
    course_name: str | None
    due_date: datetime | None
    status: AssignmentStatus


class TaskDialog(QDialog):
    """Diálogo para crear (task=None) o editar una tarea local."""

    def __init__(self, parent=None, task: Assignment | None = None) -> None:
        super().__init__(parent)

        self._task = task

        self.setWindowTitle("Editar tarea" if task else "Nueva tarea")
        self.setModal(True)
        self.setMinimumWidth(480)

        self._setup_ui()

        if task is not None:
            self._load(task)

    # ------------------------------------------------------------------ UI

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(12)

        self.title_input = QLineEdit()
        self.title_input.setMaxLength(500)
        self.title_input.setPlaceholderText("¿Qué hay que hacer?")

        self.description_input = QPlainTextEdit()
        self.description_input.setFixedHeight(90)
        self.description_input.setPlaceholderText("Descripción (opcional)")

        self.course_input = QLineEdit()
        self.course_input.setMaxLength(500)
        self.course_input.setPlaceholderText("Curso o categoría (opcional)")

        self.due_check = QCheckBox("Con fecha de entrega")

        self.due_input = QDateTimeEdit()
        self.due_input.setObjectName("dueInput")
        self.due_input.setCalendarPopup(True)
        self.due_input.setDisplayFormat("dd/MM/yyyy HH:mm")
        self._style_calendar()

        default_due = QDateTime.currentDateTime().addDays(1)
        default_due.setTime(QTime(23, 59))
        self.due_input.setDateTime(default_due)
        self.due_input.setEnabled(False)

        self.due_check.toggled.connect(self.due_input.setEnabled)

        self.status_combo = QComboBox()
        for status, label in STATUS_LABELS.items():
            self.status_combo.addItem(label, status.value)

        form.addRow("Título", self.title_input)
        form.addRow("Descripción", self.description_input)
        form.addRow("Curso", self.course_input)
        form.addRow(self.due_check, self.due_input)

        # El estado solo se elige al editar; una tarea nueva empieza pendiente.
        if self._task is not None:
            form.addRow("Estado", self.status_combo)

        layout.addLayout(form)

        self.error_label = QLabel()
        self.error_label.setObjectName("dashboardError")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        save_button = buttons.button(QDialogButtonBox.StandardButton.Save)
        save_button.setText("Guardar")
        save_button.setProperty("variant", "primary")

        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setText("Cancelar")
        cancel_button.setProperty("variant", "secondary")

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def _style_calendar(self) -> None:
        """
        Aspecto claro y legible del calendario desplegable.

        Se hace en código además de en el QSS porque la cabecera, los fines
        de semana y las flechas de mes no se pueden controlar solo con QSS.
        """
        calendar = self.due_input.calendarWidget()

        calendar.setLocale(
            QLocale(QLocale.Language.Spanish, QLocale.Country.Spain)
        )
        calendar.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        calendar.setGridVisible(False)
        calendar.setVerticalHeaderFormat(
            calendar.VerticalHeaderFormat.NoVerticalHeader
        )

        header = QTextCharFormat()
        header.setForeground(QColor("#8a919c"))
        header.setBackground(QColor("#ffffff"))
        header.setFontWeight(QFont.Weight.DemiBold)
        calendar.setHeaderTextFormat(header)

        # Por defecto Qt pinta sábado y domingo en rojo
        weekend = QTextCharFormat()
        weekend.setForeground(QColor("#1f2329"))
        calendar.setWeekdayTextFormat(Qt.DayOfWeek.Saturday, weekend)
        calendar.setWeekdayTextFormat(Qt.DayOfWeek.Sunday, weekend)

        for name, icon_name in (
            ("qt_calendar_prevmonth", "chevron_left"),
            ("qt_calendar_nextmonth", "chevron_right"),
        ):
            button = calendar.findChild(QToolButton, name)

            if button is not None:
                button.setIcon(QIcon(svg_pixmap(icon_name, "#1f2329", 18)))
                button.setIconSize(QSize(18, 18))

    def _load(self, task: Assignment) -> None:
        self.title_input.setText(task.title)
        self.description_input.setPlainText(task.description or "")
        self.course_input.setText(task.course_name or "")

        if task.due_date is not None:
            due = task.due_date

            if due.tzinfo is not None:
                due = due.astimezone().replace(tzinfo=None)

            self.due_check.setChecked(True)
            self.due_input.setDateTime(QDateTime(due))

        index = self.status_combo.findData(task.status.value)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)

    # --------------------------------------------------------------- datos

    def accept(self) -> None:
        if not self.title_input.text().strip():
            self.error_label.setText("El título no puede estar vacío.")
            self.error_label.show()
            self.title_input.setFocus()
            return

        super().accept()

    def get_data(self) -> TaskFormData:
        due_date = None

        if self.due_check.isChecked():
            due_date = self.due_input.dateTime().toPython().replace(
                second=0,
                microsecond=0,
            )

        if self._task is not None:
            status = AssignmentStatus(self.status_combo.currentData())
        else:
            status = AssignmentStatus.PENDING

        return TaskFormData(
            title=self.title_input.text().strip(),
            description=self.description_input.toPlainText().strip() or None,
            course_name=self.course_input.text().strip() or None,
            due_date=due_date,
            status=status,
        )