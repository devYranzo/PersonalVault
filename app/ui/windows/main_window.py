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

from app.ui.pages.ai_page import AIPage
from app.ui.pages.connections_page import ConnectionsPage
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.documents_page import DocumentsPage
from app.ui.pages.knowledge_page import KnowledgePage
from app.ui.pages.settings_page import SettingsPage
from app.ui.pages.tasks_page import TasksPage

ICONS_DIR = (
    Path(__file__).resolve().parents[1]
    / "resources"
    / "icons"
)

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Personal Vault")
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)

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
            self.setStyleSheet(
                stylesheet_path.read_text(encoding="utf-8")
            )

    def _setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = self._create_sidebar()
        self.content = QStackedWidget()

        self.pages = [
            DashboardPage(),
            TasksPage(),
            DocumentsPage(),
            KnowledgePage(),
            AIPage(),
            ConnectionsPage(),
            SettingsPage(),
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

        title = QLabel("Personal Vault")
        title.setObjectName("appTitle")
        layout.addWidget(title)

        subtitle = QLabel("Tu espacio personal")
        subtitle.setObjectName("appSubtitle")
        layout.addWidget(subtitle)

        layout.addSpacing(24)

        self.navigation_buttons: list[QPushButton] = []

        navigation = [
            ("home.svg", "Dashboard"),
            ("tasks.svg", "Tareas"),
            ("documents.svg", "Documentos"),
            ("knowledge.svg", "Knowledge"),
            ("ai.svg", "AI"),
            ("connections.svg", "Conexiones"),
            ("settings.svg", "Ajustes"),
        ]

        for icon, text in navigation:
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
            layout.addWidget(button)

        layout.addStretch()

        status = QLabel("Personal Vault v0.1.0")
        status.setObjectName("sidebarStatus")
        layout.addWidget(status)

        return sidebar

    def _connect_navigation(self) -> None:
        for index, button in enumerate(self.navigation_buttons):
            button.clicked.connect(
                lambda checked=False, i=index: self._select_page(i)
            )

    def _select_page(self, index: int) -> None:
        self.content.setCurrentIndex(index)

        for button_index, button in enumerate(self.navigation_buttons):
            button.setChecked(button_index == index)
