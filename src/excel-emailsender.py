import sys
import os
from PySide6.QtWidgets import QApplication

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.ui.main_window import MailerApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = MailerApp()
    gui.set_theme(gui.settings.get("theme", "Light"))
    gui.show()
    sys.exit(app.exec())