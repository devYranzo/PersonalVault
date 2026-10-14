from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.core.plugins import PluginManager
from app.ui.pages.settings.about_page import AboutPage
from app.ui.pages.settings.connections_page import ConnectionsPage


class SettingsPage(QWidget):
    def __init__(self, plugin_manager: PluginManager) -> None:
        super().__init__()

        self.plugin_manager = plugin_manager
        self.section_buttons: list[QPushButton] = []

        self._setup_ui()
        self._select_section(0)

    # ------------------------------------------------------------------ UI

    def _create_sections(self) -> list[tuple[str, QWidget]]:
        """Secciones de Ajustes: (texto de la pestaña, widget)."""
        return [
            ("Conexiones", ConnectionsPage(self.plugin_manager)),
            ("Acerca de", AboutPage()),
        ]

    def _setup_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(40, 40, 40, 30)
        root_layout.setSpacing(8)

        title = QLabel("Ajustes")
        title.setObjectName("pageTitle")

        # Contenido de la sección activa
        self.stack = QStackedWidget()

        root_layout.addWidget(title)
        root_layout.addSpacing(12)
        root_layout.addWidget(self._create_tab_bar())
        root_layout.addSpacing(16)
        root_layout.addWidget(self.stack, 1)

    def _create_tab_bar(self) -> QFrame:
        """Barra con una pestaña por sección. También rellena `self.stack`."""
        tab_bar = QFrame()
        tab_bar.setObjectName("settingsTabBar")
        tab_bar.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Maximum,
        )

        layout = QHBoxLayout(tab_bar)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        group = QButtonGroup(self)
        group.setExclusive(True)

        for index, (label, widget) in enumerate(self._create_sections()):
            button = QPushButton(label)
            button.setObjectName("settingsTab")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(
                lambda checked=False, i=index: self._select_section(i),
            )

            group.addButton(button)
            layout.addWidget(button)

            self.section_buttons.append(button)
            self.stack.addWidget(widget)

        layout.addStretch()

        return tab_bar

    # ----------------------------------------------------------- navegación

    def _select_section(self, index: int) -> None:
        self.stack.setCurrentIndex(index)

        for button_index, button in enumerate(self.section_buttons):
            button.setChecked(button_index == index)