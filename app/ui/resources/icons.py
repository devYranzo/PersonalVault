"""Iconos SVG (Material Icons, Apache 2.0) teñidos con el color definido en el QSS."""

from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QEvent, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QPushButton

# Ajusta esta ruta a donde copies la carpeta assets/icons
ICONS_DIR = Path(__file__).resolve().parent / "icons"


@lru_cache(maxsize=256)
def svg_pixmap(name: str, color: str = "#1f2329", size: int = 18) -> QPixmap:
    """Devuelve el SVG `name` teñido con `color`, nítido en pantallas HiDPI."""
    screen = QGuiApplication.primaryScreen()
    dpr = screen.devicePixelRatio() if screen else 1.0

    pixmap = QPixmap(int(size * dpr), int(size * dpr))
    pixmap.fill(Qt.GlobalColor.transparent)

    renderer = QSvgRenderer(str(ICONS_DIR / f"{name}.svg"))

    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(0, 0, pixmap.width(), pixmap.height()))
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor(color))
    painter.end()

    pixmap.setDevicePixelRatio(dpr)
    return pixmap


class IconButton(QPushButton):
    """Botón con icono SVG.

    El aspecto (colores, bordes...) lo define el QSS según `variant`
    (primary / secondary / danger). El icono se tiñe automáticamente con el
    `color` que el QSS asigne al texto del botón, también al deshabilitarse.
    """

    def __init__(
        self,
        text: str,
        icon_name: str,
        variant: str = "secondary",
        icon_size: int = 16,
        parent=None,
    ) -> None:
        super().__init__(text, parent)

        self._icon_name = icon_name
        self._icon_px = icon_size
        self._last_color = ""

        self.setProperty("variant", variant)
        self.setIconSize(QSize(icon_size, icon_size))
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._refresh_icon()

    def changeEvent(self, event) -> None:
        super().changeEvent(event)

        if event.type() in (
            QEvent.Type.EnabledChange,
            QEvent.Type.StyleChange,
            QEvent.Type.PaletteChange,
        ):
            self._refresh_icon()

    def _refresh_icon(self) -> None:
        group = (
            QPalette.ColorGroup.Active
            if self.isEnabled()
            else QPalette.ColorGroup.Disabled
        )
        color = self.palette().color(group, QPalette.ColorRole.ButtonText).name()

        if color == self._last_color:
            return

        self._last_color = color
        self.setIcon(QIcon(svg_pixmap(self._icon_name, color, self._icon_px)))