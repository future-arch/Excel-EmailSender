import sys
import os
import subprocess
import site

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Auto-activate virtual environment if not already activated
def ensure_venv():
    """Ensure virtual environment is activated or dependencies are available"""
    venv_path = os.path.join(project_root, 'venv')
    
    # Check if we're already in the virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return True  # Already in a virtual environment
    
    # Check if venv exists and try to use its packages
    if os.path.exists(venv_path):
        # Add venv site-packages to path
        if sys.platform == "win32":
            site_packages = os.path.join(venv_path, 'Lib', 'site-packages')
        else:
            python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
            site_packages = os.path.join(venv_path, 'lib', python_version, 'site-packages')
        
        if os.path.exists(site_packages):
            sys.path.insert(0, site_packages)
            site.addsitedir(site_packages)
            
            # Also add the venv's bin/Scripts to PATH for any executables
            if sys.platform == "win32":
                bin_path = os.path.join(venv_path, 'Scripts')
            else:
                bin_path = os.path.join(venv_path, 'bin')
            os.environ['PATH'] = bin_path + os.pathsep + os.environ.get('PATH', '')
            return True
    
    return False

# Try to ensure venv before importing PySide6
venv_activated = ensure_venv()

try:
    from PySide6.QtWidgets import QApplication
except ImportError as e:
    print("\n" + "="*60)
    print("ERROR: Required dependencies not found!")
    print("="*60)
    if not venv_activated:
        print("\nThe virtual environment is not set up properly.")
        print("Please run the following commands to set up the environment:\n")
        print(f"  cd {project_root}")
        print("  python3 -m venv venv")
        print("  source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        print("  pip install -r requirements.txt")
    else:
        print("\nDependencies are missing from the virtual environment.")
        print("Please run:\n")
        print(f"  cd {project_root}")
        print("  source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
        print("  pip install -r requirements.txt")
    print("\nOr simply use the provided run script:")
    print(f"  {project_root}/run.sh")
    print("="*60)
    sys.exit(1)

from src.ui.main_window import MailerApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application attributes for macOS
    from PySide6.QtCore import Qt, QTimer
    app.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeMenuBar, True)  # Prevent menubar issues
    
    gui = MailerApp()
    
    # Show the window first for better perceived performance
    gui.show()
    
    # Fix window position and flags after showing
    def fix_window():
        # Move window away from menubar area
        gui.move(gui.x(), max(50, gui.y()))  # Ensure at least 50px from top
        # Normalize flags
        if hasattr(gui, '_normalize_window_flags_and_geometry'):
            gui._normalize_window_flags_and_geometry()
    
    # Initialize heavy components after UI is visible
    def initialize_components():
        # Initialize TinyMCE editor
        if hasattr(gui, '_initialize_editor'):
            gui._initialize_editor()
        # Set theme (reduced delay)
        gui.set_theme(gui.settings.get("theme", "Light"))
    
    QTimer.singleShot(50, fix_window)  # Reduced delay
    QTimer.singleShot(100, initialize_components)  # Much shorter delay
    
    sys.exit(app.exec())