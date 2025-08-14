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
    gui.show()
    # Set theme after a delay to ensure TinyMCE is loaded
    from PySide6.QtCore import QTimer
    QTimer.singleShot(2000, lambda: gui.set_theme(gui.settings.get("theme", "Light")))
    sys.exit(app.exec())