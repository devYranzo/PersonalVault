from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class DashboardPage(QWidget):

    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        self.title = QLabel()
        self.title.setObjectName("pageTitle")

        description = QLabel(
            "Aquí tendrás una visión general de tus estudios, tareas y eventos."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        layout.addWidget(self.title)
        layout.addWidget(description)
        layout.addStretch()

        self._update_greeting()

        # Configurar el QTimer para actualizar cada minuto (60,000 ms)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_greeting)
        self.timer.start(60000)

    def _get_greeting(self) -> str:
        hour = datetime.now().hour

        if 6 <= hour < 12:
            return "¡Buenos días, usuario!"
        elif 12 <= hour < 20:
            return "¡Buenas tardes, usuario!"
        else:
            return "¡Buenas noches, usuario!"

    def _update_greeting(self) -> str:
        """Actualiza el texto de la etiqueta si cambia la hora."""
        new_greeting = self._get_greeting()

        if self.title.text() != new_greeting:
            self.title.setText(new_greeting)