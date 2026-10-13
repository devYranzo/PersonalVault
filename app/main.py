import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.ui.windows.main_window import MainWindow

APP_NAME = "Personal Vault"

# Identificador propio para Windows: sin él, la barra de tareas agrupa la
# ventana bajo python.exe y muestra su icono en lugar del de la app.
WINDOWS_APP_ID = "devyranzo.personalvault"

ICON_PATH = (
    Path(__file__).resolve().parent
    / "ui"
    / "resources"
    / "app_icon.ico"
)


def _set_windows_app_id() -> None:
    if sys.platform != "win32":
        return

    import ctypes

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        WINDOWS_APP_ID
    )


def main() -> int:
    _set_windows_app_id()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setWindowIcon(QIcon(str(ICON_PATH)))

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())