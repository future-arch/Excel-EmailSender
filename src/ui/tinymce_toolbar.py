from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QComboBox, QLabel, 
    QToolButton, QButtonGroup, QFrame, QColorDialog, QSizePolicy, QListView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon, QColor, QPalette


class TinyMCEToolbar(QWidget):
    """External toolbar for TinyMCE editor"""
    
    # Signals for communicating with the editor
    commandExecuted = Signal(str, str)  # command, value
    formatChanged = Signal(str, str)    # format_type, value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.editor = None  # Will be set by parent
        self.setup_ui()
        
    def setup_ui(self):
        """Create the toolbar UI with two rows"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 4, 6, 4)
        main_layout.setSpacing(2)
        
        # First row
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(3)
        
        # Undo/Redo group
        undo_btn = self._create_button("↶", "撤销", lambda: self._exec_command("undo"))
        redo_btn = self._create_button("↷", "重做", lambda: self._exec_command("redo"))
        row1_layout.addWidget(undo_btn)
        row1_layout.addWidget(redo_btn)
        self._add_separator_to_layout(row1_layout)
        
        # Format dropdowns
        self.format_combo = self._configure_combo_box(QComboBox())
        self.format_combo.addItems(["格式", "段落", "标题 1", "标题 2", "标题 3", "标题 4", "标题 5", "标题 6", "引用", "代码块"])
        self.format_combo.currentTextChanged.connect(self._format_changed)
        row1_layout.addWidget(self.format_combo)
        
        self.font_size_combo = self._configure_combo_box(QComboBox())
        self.font_size_combo.addItems(["字号", "10px", "12px", "14px", "16px", "18px", "24px", "32px"])
        self.font_size_combo.currentTextChanged.connect(self._font_size_changed)
        row1_layout.addWidget(self.font_size_combo)
        
        self.font_family_combo = self._configure_combo_box(QComboBox())
        self.font_family_combo.addItems([
            "字体", "Arial", "Helvetica", "Times New Roman", "Georgia", "Verdana", 
            "Courier New", "微软雅黑", "苹方", "冬青黑体", "宋体", "黑体", "华文黑体", 
            "华文宋体", "华文楷体", "楷体", "仿宋"
        ])
        self.font_family_combo.currentTextChanged.connect(self._font_family_changed)
        row1_layout.addWidget(self.font_family_combo)
        self._add_separator_to_layout(row1_layout)
        
        # Text formatting buttons
        self.bold_btn = self._create_toggle_button("B", "粗体", lambda: self._toggle_format("bold"))
        self.italic_btn = self._create_toggle_button("I", "斜体", lambda: self._toggle_format("italic"))
        self.underline_btn = self._create_toggle_button("U", "下划线", lambda: self._toggle_format("underline"))
        self.strike_btn = self._create_toggle_button("S", "删除线", lambda: self._toggle_format("strikethrough"))
        
        row1_layout.addWidget(self.bold_btn)
        row1_layout.addWidget(self.italic_btn)
        row1_layout.addWidget(self.underline_btn)
        row1_layout.addWidget(self.strike_btn)
        self._add_separator_to_layout(row1_layout)
        
        # Alignment buttons
        left_btn = self._create_button("⫷", "左对齐", lambda: self._exec_command("justifyLeft"))
        center_btn = self._create_button("☰", "居中", lambda: self._exec_command("justifyCenter"))
        right_btn = self._create_button("⫸", "右对齐", lambda: self._exec_command("justifyRight"))
        row1_layout.addWidget(left_btn)
        row1_layout.addWidget(center_btn)
        row1_layout.addWidget(right_btn)
        self._add_separator_to_layout(row1_layout)
        
        # List buttons  
        bullet_btn = self._create_button("•", "无序列表", lambda: self._exec_command("insertUnorderedList"))
        numbered_btn = self._create_button("1.", "有序列表", lambda: self._exec_command("insertOrderedList"))
        outdent_btn = self._create_button("⇤", "减少缩进", lambda: self._exec_command("outdent"))
        indent_btn = self._create_button("⇥", "增加缩进", lambda: self._exec_command("indent"))
        row1_layout.addWidget(bullet_btn)
        row1_layout.addWidget(numbered_btn)
        row1_layout.addWidget(outdent_btn)
        row1_layout.addWidget(indent_btn)
        
        row1_layout.addStretch()
        
        # Second row
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(3)
        
        # Color buttons
        text_color_btn = self._create_button("A", "文字颜色", self._change_text_color)
        bg_color_btn = self._create_button("A", "背景颜色", self._change_bg_color)
        text_color_btn.setStyleSheet("color: black; font-weight: bold;")
        bg_color_btn.setStyleSheet("background-color: yellow; font-weight: bold;")
        row2_layout.addWidget(text_color_btn)
        row2_layout.addWidget(bg_color_btn)
        self._add_separator_to_layout(row2_layout)
        
        # Insert buttons
        link_btn = self._create_button("🔗", "插入链接", self._insert_link)
        table_btn = self._create_button("⊞", "插入表格", self._insert_table)
        hr_btn = self._create_button("—", "分隔线", lambda: self._exec_command("insertHorizontalRule"))
        row2_layout.addWidget(link_btn)
        row2_layout.addWidget(table_btn)
        row2_layout.addWidget(hr_btn)
        self._add_separator_to_layout(row2_layout)
        
        # Variable dropdown
        self.variable_combo = self._configure_combo_box(QComboBox())
        self.variable_combo.setMinimumWidth(120)
        self._setup_variable_combo()
        self.variable_combo.currentTextChanged.connect(self._insert_variable)
        row2_layout.addWidget(self.variable_combo)
        self._add_separator_to_layout(row2_layout)
        
        # Utility buttons
        preview_btn = self._create_button("👁", "预览邮件内容", self._toggle_preview)
        emoji_btn = self._create_button("😊", "表情", lambda: self._insert_emoji("😊"))
        clear_btn = self._create_button("Tx", "清除格式", lambda: self._exec_command("removeFormat"))
        source_btn = self._create_button("</>", "查看源码", self._toggle_source)
        row2_layout.addWidget(preview_btn)
        row2_layout.addWidget(emoji_btn)
        row2_layout.addWidget(clear_btn)
        row2_layout.addWidget(source_btn)
        
        row2_layout.addStretch()
        
        # Add rows to main layout
        main_layout.addLayout(row1_layout)
        main_layout.addLayout(row2_layout)
        
        # Set toolbar styling for two-row layout
        self.setStyleSheet("""
            TinyMCEToolbar {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f8f9fa, stop:1 #f1f3f4);
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 4px 6px;
                min-height: 60px;
                max-height: 80px;
            }
            QPushButton, QToolButton {
                border: 1px solid #d1d9e0;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ffffff, stop:1 #f6f8fa);
                border-radius: 3px;
                padding: 2px 4px;
                margin: 1px;
                min-width: 22px;
                min-height: 22px;
                max-height: 24px;
                font-size: 11px;
            }
            QPushButton:hover, QToolButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f6f8fa, stop:1 #eaeef2);
                border-color: #c7d2fe;
            }
            QPushButton:pressed, QToolButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #4f46e5, stop:1 #3730a3);
                color: white;
            }
            QComboBox {
                border: 1px solid #d1d9e0;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #ffffff, stop:1 #f6f8fa);
                border-radius: 3px;
                padding: 2px 6px;
                margin: 1px;
                min-height: 22px;
                max-height: 24px;
                font-size: 11px;
                color: #1f2937;
            }
            QComboBox:hover {
                border-color: #c7d2fe;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #f6f8fa, stop:1 #eaeef2);
            }
            QComboBox QAbstractItemView {
                border: 1px solid #d1d9e0;
                background-color: #ffffff;
                color: #1f2937;
                selection-background-color: #4f46e5;
                selection-color: #ffffff;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 4px 8px;
                border-bottom: 1px solid #f1f3f4;
                min-height: 20px;
                color: #1f2937;
                background-color: transparent;
            }
            QComboBox QAbstractItemView::item:hover {
                background: #e5e7eb !important;
                color: #1f2937 !important;
            }
            QComboBox QListView::item:hover {
                background: #e5e7eb !important;
                color: #1f2937 !important;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #4f46e5 !important;
                color: #ffffff !important;
                border: none !important;
            }
            QComboBox QAbstractItemView::item:focus {
                background-color: #4f46e5 !important;
                color: #ffffff !important;
                border: none !important;
            }
            QComboBox QAbstractItemView::item:selected:hover {
                background-color: #4338ca !important;
                color: #ffffff !important;
            }
            QFrame {
                color: #d0d7de;
                margin: 0px 2px;
            }
        """)
        
    def _create_button(self, text, tooltip, callback):
        """Create a standard button"""
        btn = QPushButton(text)
        btn.setToolTip(tooltip)
        btn.clicked.connect(callback)
        btn.setFixedSize(26, 24)
        return btn
        
    def _create_toggle_button(self, text, tooltip, callback):
        """Create a toggle button"""
        btn = QToolButton()
        btn.setText(text)
        btn.setToolTip(tooltip)
        btn.setCheckable(True)
        btn.clicked.connect(callback)
        btn.setFixedSize(26, 24)
        return btn
        
    def _add_separator_to_layout(self, layout):
        """Add a visual separator to a layout"""
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setMaximumHeight(20)
        separator.setMaximumWidth(1)
        layout.addWidget(separator)
    
    def _configure_combo_box(self, combo):
        """Configure combo box with custom styling to force hover colors"""
        combo.setAttribute(Qt.WidgetAttribute.WA_MacShowFocusRect, False)
        
        # Create custom list view for dropdown
        list_view = QListView()
        combo.setView(list_view)
        
        # Set custom palette for the list view
        palette = list_view.palette()
        
        # Light theme colors (will be updated in set_theme)
        palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))  # Background
        palette.setColor(QPalette.ColorRole.Text, QColor("#1f2937"))  # Text
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#e5e7eb"))  # Hover background
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#1f2937"))  # Hover text
        
        list_view.setPalette(palette)
        return combo
        
    def _setup_variable_combo(self):
        """Setup the variable dropdown"""
        self.variable_combo.addItem("插入变量")
        self.variable_combo.addItem("{{姓名}} - 收件人姓名")
        self.variable_combo.addItem("{{邮箱}} - 收件人邮箱")
        self.variable_combo.addItem("{{群组名称}} - 群组显示名称")
        self.variable_combo.addItem("{{群组描述}} - 群组描述信息")
        self.variable_combo.addItem("{{群组邮箱}} - 群组邮箱地址")
        self.variable_combo.addItem("{{成员类型}} - 成员类型")
        self.variable_combo.addItem("{{部门}} - 成员所属部门")
        self.variable_combo.addItem("{{职位}} - 成员职位")
        self.variable_combo.addItem("{{当前日期}} - 今天的日期")
        self.variable_combo.addItem("{{当前时间}} - 当前时间")
        self.variable_combo.addItem("{{年份}} - 当前年份")
        self.variable_combo.addItem("{{月份}} - 当前月份")
        
    def set_editor(self, editor):
        """Set the associated editor"""
        self.editor = editor
        
    def _exec_command(self, command, value=""):
        """Execute a command on the editor"""
        if self.editor:
            self.editor.web_view.page().runJavaScript(f"execCommand('{command}', '{value}')")
            
    def _toggle_format(self, format_type):
        """Toggle text formatting"""
        if self.editor:
            self.editor.web_view.page().runJavaScript(f"toggleFormat('{format_type}')")
            
    def _format_changed(self, text):
        """Handle format dropdown change"""
        format_map = {
            "段落": "p", "标题 1": "h1", "标题 2": "h2", "标题 3": "h3",
            "标题 4": "h4", "标题 5": "h5", "标题 6": "h6", 
            "引用": "blockquote", "代码块": "pre"
        }
        if text in format_map and self.editor:
            self.editor.web_view.page().runJavaScript(f"formatBlock('{format_map[text]}')")
            self.format_combo.setCurrentIndex(0)  # Reset to "格式"
            
    def _font_size_changed(self, text):
        """Handle font size change"""
        size_map = {
            "10px": "1", "12px": "2", "14px": "3", "16px": "4",
            "18px": "5", "24px": "6", "32px": "7"
        }
        if text in size_map and self.editor:
            self.editor.web_view.page().runJavaScript(f"changeFontSize('{size_map[text]}')")
            self.font_size_combo.setCurrentIndex(0)  # Reset
            
    def _font_family_changed(self, text):
        """Handle font family change"""
        font_map = {
            "Arial": "Arial, sans-serif",
            "Helvetica": "Helvetica, sans-serif", 
            "Times New Roman": "Times New Roman, serif",
            "Georgia": "Georgia, serif",
            "Verdana": "Verdana, sans-serif",
            "Courier New": "Courier New, monospace",
            "微软雅黑": "'Microsoft YaHei', '微软雅黑', sans-serif",
            "苹方": "'PingFang SC', '苹方', sans-serif",
            "冬青黑体": "'Hiragino Sans GB', '冬青黑体', sans-serif",
            "宋体": "SimSun, '宋体', serif",
            "黑体": "SimHei, '黑体', sans-serif",
            "华文黑体": "'STHeiti', '华文黑体', sans-serif",
            "华文宋体": "'STSong', '华文宋体', serif",
            "华文楷体": "'STKaiti', '华文楷体', serif",
            "楷体": "KaiTi, '楷体', serif",
            "仿宋": "FangSong, '仿宋', serif"
        }
        if text in font_map and self.editor:
            self.editor.web_view.page().runJavaScript(f"changeFontFamily('{font_map[text]}')")
            self.font_family_combo.setCurrentIndex(0)  # Reset
            
    def _change_text_color(self):
        """Change text color"""
        color = QColorDialog.getColor(QColor(0, 0, 0), self, "选择文字颜色")
        if color.isValid() and self.editor:
            self.editor.web_view.page().runJavaScript(f"changeForeColor('{color.name()}')")
            
    def _change_bg_color(self):
        """Change background color"""
        color = QColorDialog.getColor(QColor(255, 255, 255), self, "选择背景颜色")
        if color.isValid() and self.editor:
            self.editor.web_view.page().runJavaScript(f"changeBackColor('{color.name()}')")
            
    def _insert_link(self):
        """Insert a link"""
        if self.editor:
            self.editor.web_view.page().runJavaScript("insertLink()")
            
    def _insert_table(self):
        """Insert a table"""
        if self.editor:
            self.editor.web_view.page().runJavaScript("insertTable()")
            
    def _insert_variable(self, text):
        """Insert a variable"""
        if text.startswith("{{") and self.editor:
            variable = text.split(" - ")[0]  # Extract just the variable part
            self.editor.web_view.page().runJavaScript(f"insertVariable('{variable}')")
            self.variable_combo.setCurrentIndex(0)  # Reset
            
    def _insert_emoji(self, emoji):
        """Insert an emoji"""
        if self.editor:
            self.editor.web_view.page().runJavaScript(f"insertEmoji('{emoji}')")
            
    def _toggle_preview(self):
        """Toggle preview mode"""
        if self.editor:
            self.editor.web_view.page().runJavaScript("togglePreview()")
            
    def _toggle_source(self):
        """Toggle source view"""
        if self.editor:
            self.editor.web_view.page().runJavaScript("toggleSource()")
            
    def update_variable_dropdown(self, excel_columns=None):
        """Update variable dropdown with Excel columns"""
        # Clear existing Excel items
        for i in range(self.variable_combo.count() - 1, 12, -1):  # Remove items after the standard ones
            self.variable_combo.removeItem(i)
            
        # Add Excel columns if provided
        if excel_columns:
            for column in excel_columns:
                self.variable_combo.addItem(f"{{{{{column}}}}} - Excel列")
                
    def set_theme(self, theme):
        """Set the toolbar theme"""
        # Force refresh by clearing stylesheet first
        self.setStyleSheet("")
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()  # Force processing of events
        
        if theme == "Dark":
            self.setStyleSheet("""
                TinyMCEToolbar {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #1f2937, stop:1 #111827);
                    border: 1px solid #374151;
                    border-radius: 4px;
                    padding: 4px 6px;
                    min-height: 60px;
                    max-height: 80px;
                }
                QPushButton, QToolButton {
                    border: 1px solid #4b5563;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #374151, stop:1 #1f2937);
                    color: #f9fafb;
                    border-radius: 3px;
                    padding: 2px 4px;
                    margin: 1px;
                    min-width: 22px;
                    min-height: 22px;
                    max-height: 24px;
                    font-size: 11px;
                }
                QPushButton:hover, QToolButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #4b5563, stop:1 #374151);
                    border-color: #818cf8;
                }
                QPushButton:pressed, QToolButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #6366f1, stop:1 #4f46e5);
                    color: white;
                }
                QComboBox {
                    border: 1px solid #4b5563;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #374151, stop:1 #1f2937);
                    color: #f9fafb;
                    border-radius: 3px;
                    padding: 2px 6px;
                    margin: 1px;
                    min-height: 22px;
                    max-height: 24px;
                    font-size: 11px;
                }
                QComboBox:hover {
                    border-color: #818cf8;
                }
                QComboBox QAbstractItemView {
                    border: 1px solid #4b5563;
                    background-color: #1f2937;
                    color: #f9fafb;
                    selection-background-color: #6366f1;
                    selection-color: #ffffff;
                    outline: none;
                }
                QComboBox QAbstractItemView::item {
                    padding: 4px 8px;
                    border-bottom: 1px solid #374151;
                    min-height: 20px;
                    color: #f9fafb;
                    background-color: transparent;
                }
                QComboBox QAbstractItemView::item:hover {
                    background: #4b5563 !important;
                    color: #ffffff !important;
                }
                QComboBox QListView::item:hover {
                    background: #4b5563 !important;
                    color: #ffffff !important;
                }
                QComboBox QAbstractItemView::item:selected {
                    background-color: #6366f1 !important;
                    color: #ffffff !important;
                    border: none !important;
                }
                QComboBox QAbstractItemView::item:focus {
                    background-color: #6366f1 !important;
                    color: #ffffff !important;
                    border: none !important;
                }
                QComboBox QAbstractItemView::item:selected:hover {
                    background-color: #5b21b6 !important;
                    color: #ffffff !important;
                }
                QFrame {
                    color: #4b5563;
                    margin: 0px 2px;
                }
            """)
        else:
            self.setStyleSheet("""
                TinyMCEToolbar {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #f8f9fa, stop:1 #f1f3f4);
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 4px 6px;
                    min-height: 60px;
                    max-height: 80px;
                }
                QPushButton, QToolButton {
                    border: 1px solid #d1d9e0;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #ffffff, stop:1 #f6f8fa);
                    border-radius: 3px;
                    padding: 2px 4px;
                    margin: 1px;
                    min-width: 22px;
                    min-height: 22px;
                    max-height: 24px;
                    font-size: 11px;
                }
                QPushButton:hover, QToolButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #f6f8fa, stop:1 #eaeef2);
                    border-color: #c7d2fe;
                }
                QPushButton:pressed, QToolButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #4f46e5, stop:1 #3730a3);
                    color: white;
                }
                QComboBox {
                    border: 1px solid #d1d9e0;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #ffffff, stop:1 #f6f8fa);
                    border-radius: 3px;
                    padding: 2px 6px;
                    margin: 1px;
                    min-height: 22px;
                    max-height: 24px;
                    font-size: 11px;
                    color: #1f2937;
                }
                QComboBox:hover {
                    border-color: #c7d2fe;
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #f6f8fa, stop:1 #eaeef2);
                }
                QComboBox QAbstractItemView {
                    border: 1px solid #d1d9e0;
                    background-color: #ffffff;
                    color: #1f2937;
                    selection-background-color: #4f46e5;
                    selection-color: #ffffff;
                    outline: none;
                }
                QComboBox QAbstractItemView::item {
                    padding: 4px 8px;
                    border-bottom: 1px solid #f1f3f4;
                    min-height: 20px;
                    color: #1f2937;
                    background-color: transparent;
                }
                QComboBox QAbstractItemView::item:hover {
                    background: #e5e7eb !important;
                    color: #1f2937 !important;
                }
                QComboBox QListView::item:hover {
                    background: #e5e7eb !important;
                    color: #1f2937 !important;
                }
                QComboBox QAbstractItemView::item:selected {
                    background-color: #4f46e5 !important;
                    color: #ffffff !important;
                    border: none !important;
                }
                QComboBox QAbstractItemView::item:focus {
                    background-color: #4f46e5 !important;
                    color: #ffffff !important;
                    border: none !important;
                }
                QComboBox QAbstractItemView::item:selected:hover {
                    background-color: #4338ca !important;
                    color: #ffffff !important;
                }
                QFrame {
                    color: #d0d7de;
                    margin: 0px 2px;
                }
            """)
        
        # Update combo box palettes based on theme
        self._update_combo_box_palettes(theme)
        
        # Force widget to update its style
        self.style().unpolish(self)
        self.style().polish(self)
        QApplication.processEvents()
    
    def _update_combo_box_palettes(self, theme):
        """Update combo box dropdown palettes for the theme"""
        combos = [self.format_combo, self.font_size_combo, self.font_family_combo, self.variable_combo]
        
        for combo in combos:
            if combo.view():
                palette = combo.view().palette()
                
                if theme == "Dark":
                    # Dark theme colors
                    palette.setColor(QPalette.ColorRole.Base, QColor("#1f2937"))  # Background
                    palette.setColor(QPalette.ColorRole.Text, QColor("#f9fafb"))  # Text
                    palette.setColor(QPalette.ColorRole.Highlight, QColor("#4b5563"))  # Hover background
                    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))  # Hover text
                else:
                    # Light theme colors
                    palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))  # Background
                    palette.setColor(QPalette.ColorRole.Text, QColor("#1f2937"))  # Text
                    palette.setColor(QPalette.ColorRole.Highlight, QColor("#e5e7eb"))  # Hover background
                    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#1f2937"))  # Hover text
                
                combo.view().setPalette(palette)