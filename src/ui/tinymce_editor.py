import os
import sys
import json
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import QUrl, Signal, QObject, Slot, QTimer, QEventLoop, Qt
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel


class PyBridge(QObject):
    contentChangedSignal = Signal(str)
    
    @Slot(str)
    def contentChanged(self, content):
        self.contentChangedSignal.emit(content)


class TinyMCEEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self._content = ""
        self._theme = "Light"
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create web view
        self.web_view = QWebEngineView()
        # Set height to 0.75x (reduced from previous 2x)
        self.web_view.setMinimumHeight(300)
        # Ensure web view can receive focus
        self.web_view.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout.addWidget(self.web_view)
        
        # Set up web channel for Python-JavaScript communication
        self.channel = QWebChannel()
        self.bridge = PyBridge()
        self.channel.registerObject("pybridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)
        
        # Connect signal
        self.bridge.contentChangedSignal.connect(self.on_content_changed)
        
        # Load TinyMCE HTML template
        self.load_editor()
        
        # Focus the editor after a delay to ensure it's loaded
        QTimer.singleShot(3000, self.focus_editor)
    
    def load_editor(self):
        # Get the path to the HTML template
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        html_path = os.path.join(project_root, "assets", "tinymce_like_editor.html")
        
        if os.path.exists(html_path):
            # Load the HTML file
            url = QUrl.fromLocalFile(html_path)
            self.web_view.load(url)
        else:
            print(f"Error: TinyMCE-like editor template not found at {html_path}")
    
    def on_content_changed(self, content):
        self._content = content
    
    def focus_editor(self):
        # Focus the web view first
        self.web_view.setFocus()
        # Use research-based focus method with mouseup event
        self.web_view.page().runJavaScript("focusEditor()")
    
    def mousePressEvent(self, event):
        # When the widget is clicked, focus the editor
        super().mousePressEvent(event)
        self.focus_editor()
    
    def focusInEvent(self, event):
        # When the widget receives focus, focus the editor
        super().focusInEvent(event)
        self.focus_editor()
    
    def setPlaceholderText(self, text):
        # This is handled in the HTML template
        pass
    
    def toHtml(self):
        # Get content synchronously using event loop
        loop = QEventLoop()
        result = {'content': ''}
        
        def callback(content):
            result['content'] = content if content else ''
            loop.quit()
        
        self.web_view.page().runJavaScript("getContent()", callback)
        
        # Set a timeout to prevent infinite waiting
        QTimer.singleShot(1000, loop.quit)
        loop.exec()
        
        return result['content']
    
    def toPlainText(self):
        # Get plain text synchronously using event loop
        loop = QEventLoop()
        result = {'text': ''}
        
        def callback(text):
            result['text'] = text if text else ''
            loop.quit()
        
        self.web_view.page().runJavaScript("getPlainText()", callback)
        
        # Set a timeout to prevent infinite waiting
        QTimer.singleShot(1000, loop.quit)
        loop.exec()
        
        return result['text']
    
    def clear(self):
        self.web_view.page().runJavaScript("clearContent()")
        self._content = ""
    
    def setHtml(self, html):
        # Escape quotes in HTML
        escaped_html = html.replace("'", "\\'").replace("\n", "\\n")
        self.web_view.page().runJavaScript(f"setContent('{escaped_html}')")
        self._content = html
    
    def setPlainText(self, text):
        # Convert plain text to HTML
        html = text.replace("\n", "<br>")
        self.setHtml(html)
    
    def insertPlainText(self, text):
        # Insert text at cursor position
        escaped_text = text.replace("'", "\\'").replace("\n", "\\n")
        self.web_view.page().runJavaScript(
            f"if (window.tinyEditor) {{ window.tinyEditor.insertContent('{escaped_text}'); }}"
        )
    
    def textCursor(self):
        # TinyMCE handles cursor internally
        return None
    
    def setTextCursor(self, cursor):
        # TinyMCE handles cursor internally
        pass
    
    def setTheme(self, theme):
        self._theme = theme
        theme_name = 'dark' if theme == 'Dark' else 'light'
        # Use a timer to ensure the page is loaded before calling setTheme
        QTimer.singleShot(1000, lambda: self.web_view.page().runJavaScript(f"if (typeof setTheme !== 'undefined') setTheme('{theme_name}')"))
    
    def get_content_async(self, callback):
        self.web_view.page().runJavaScript("getContent()", callback)
    
    def get_plain_text_async(self, callback):
        self.web_view.page().runJavaScript("getPlainText()", callback)
    
    def update_variable_dropdown(self, excel_columns=None):
        """Update the variable dropdown with Excel columns"""
        if excel_columns is None:
            excel_columns = []
        
        # Convert column list to JavaScript array string
        columns_js = str(excel_columns).replace("'", '"')
        
        script = f"if (typeof updateVariableDropdown === 'function') {{ updateVariableDropdown({columns_js}); }}"
        self.web_view.page().runJavaScript(script)
    
    def set_preview_data(self, preview_data):
        """Set the preview data for variable substitution"""
        if preview_data is None:
            preview_data = {}
        
        # Remove debug output to clean up console
        # print(f"[DEBUG] TinyMCE editor set_preview_data called with {len(preview_data)} variables")
        # print(f"[DEBUG] Preview data keys: {list(preview_data.keys())}")
        
        # Convert preview data to JavaScript object string
        # Ensure all values are strings and handle None values
        cleaned_data = {}
        for key, value in preview_data.items():
            if value is None:
                cleaned_data[key] = ""
            else:
                cleaned_data[key] = str(value)
        
        data_js = json.dumps(cleaned_data, ensure_ascii=False)
        
        # Create the script that will set the preview data
        script = f"""
        if (typeof setPreviewData === 'function') {{
            setPreviewData({data_js});
            console.log('Preview data updated with ' + Object.keys({data_js}).length + ' variables');
        }} else {{
            // If function doesn't exist yet, wait and retry
            setTimeout(function() {{
                if (typeof setPreviewData === 'function') {{
                    setPreviewData({data_js});
                    console.log('Preview data updated with ' + Object.keys({data_js}).length + ' variables (delayed)');
                }} else {{
                    console.warn('setPreviewData function still not available');
                }}
            }}, 500);
        }}
        """
        
        # Execute immediately - the script has its own retry logic
        self.web_view.page().runJavaScript(script)