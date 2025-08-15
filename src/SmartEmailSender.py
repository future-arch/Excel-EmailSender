import sys
import os
from PySide6.QtWidgets import QApplication

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.ui.main_window import MailerApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application attributes for macOS
    from PySide6.QtCore import Qt, QTimer
    app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, True)  # Prevent menubar issues
    
    gui = MailerApp()
    
    # Show the window
    gui.show()
    
    # Fix window position and flags after showing
    def fix_window():
        # Move window away from menubar area
        gui.move(gui.x(), max(50, gui.y()))  # Ensure at least 50px from top
        # Normalize flags
        if hasattr(gui, '_normalize_window_flags_and_geometry'):
            gui._normalize_window_flags_and_geometry()
    
    QTimer.singleShot(100, fix_window)
    
    # Set theme after a delay to ensure TinyMCE is loaded
    QTimer.singleShot(2000, lambda: gui.set_theme(gui.settings.get("theme", "Light")))
    
    sys.exit(app.exec())