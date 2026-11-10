"""
PyQt6 Desktop Application Entry Point for Gestor Presupuestario.
"""
import sys
import os
from pathlib import Path

# Fix path resolution for frozen exe and local execution
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

# Make sure project directory is in python path
sys.path.insert(0, str(BASE_DIR))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont

# Initialize DB tables
from db.database import create_tables, engine, Base
import models.models
Base.metadata.create_all(bind=engine)

from ui.main_window import MainWindow
from ui.login_dialog import LoginDialog


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Gestor Presupuestario")
    app.setStyle("Fusion")

    # Set modern default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Authentication flow
    login_dialog = LoginDialog()
    if login_dialog.exec() == LoginDialog.DialogCode.Accepted:
        current_user = login_dialog.authenticated_user
        window = MainWindow(current_user=current_user)
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
