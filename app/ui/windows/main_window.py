from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.config import APP_NAME
from app.core.plugin_system import create_plugin_manager
from app.core.plugins import PluginManager
from app.ui.pages.ai_page import AIPage
from app.ui.pages.calendar_page import CalendarPage
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.settings_page import SettingsPage
from app.ui.pages.tasks_page import TasksPage

ICONS_DIR = (
    Path(__file__).resolve().parents[1]
    / "resources"
    / "icons"
)

# Botones de la barra lateral: (icono, texto).
# El orden de `self.pages` debe coincidir con NAVIGATION seguido de
# SETTINGS_NAVIGATION: Ajustes es el último y va anclado abajo del todo.
NAVIGATION = [
    ("home.svg", "Dashboard"),
    ("tasks.svg", "Tareas"),
    ("calendar.svg", "Calendario"),
    ("ai.svg", "AI"),
]

SETTINGS_NAVIGATION = ("settings.svg", "Ajustes")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(APP_NAME)
        self.resize(1200, 600)
        self.setMinimumSize(900, 600)

        self.plugin_manager: PluginManager = create_plugin_manager()

        self._load_stylesheet()
        self._setup_ui()
        self._connect_navigation()
        self._select_page(0)

    def _load_stylesheet(self) -> None:
        stylesheet_path = (
            Path(__file__).resolve().parents[1]
            / "resources"
            / "style.qss"
        )

        if stylesheet_path.exists():
            stylesheet = stylesheet_path.read_text(encoding="utf-8")

            # Qt resuelve url() relativo al directorio de trabajo, no al
            # .qss, así que los iconos del QSS usan este marcador.
            stylesheet = stylesheet.replace(
                "{{ICONS}}",
                ICONS_DIR.as_posix(),
            )

            self.setStyleSheet(stylesheet)

    def _setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = self._create_sidebar()
        self.content = QStackedWidget()

        self.settings_page = SettingsPage(
            plugin_manager=self.plugin_manager,
        )

        # El orden debe coincidir con los botones de la barra lateral
        self.pages = [
            DashboardPage(),
            TasksPage(),
            CalendarPage(),
            AIPage(),
            self.settings_page,
        ]

        for page in self.pages:
            self.content.addWidget(page)

        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(self.content, 1)

    def _create_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(6)

        title = QLabel(APP_NAME)
        title.setObjectName("appTitle")
        layout.addWidget(title)

        subtitle = QLabel("Tu espacio personal")
        subtitle.setObjectName("appSubtitle")
        layout.addWidget(subtitle)

        layout.addSpacing(24)

        self.navigation_buttons: list[QPushButton] = []

        for icon, text in NAVIGATION:
            layout.addWidget(self._create_nav_button(icon, text))

        layout.addStretch()

        # Ajustes, separado de las páginas, abajo del todo
        layout.addWidget(self._create_nav_button(*SETTINGS_NAVIGATION))

        return sidebar

    def _create_nav_button(self, icon: str, text: str) -> QPushButton:
        button = QPushButton(text)
        button.setIcon(QIcon(str(ICONS_DIR / icon)))
        button.setIconSize(QSize(20, 20))

        button.setObjectName("navButton")
        button.setCheckable(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)

        button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        button.setMinimumHeight(42)

        self.navigation_buttons.append(button)

        return button

    def _connect_navigation(self) -> None:
        for index, button in enumerate(self.navigation_buttons):
            button.clicked.connect(
                lambda checked=False, i=index: self._select_page(i)
            )

    def _select_page(self, index: int) -> None:
        self.content.setCurrentIndex(index)

        for button_index, button in enumerate(self.navigation_buttons):
            button.setChecked(button_index == index)

    def closeEvent(self, event) -> None:
        self.plugin_manager.shutdown_all()
        event.accept()