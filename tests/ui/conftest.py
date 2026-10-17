import os

# Debe fijarse antes de que pytest-qt cree la QApplication.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")