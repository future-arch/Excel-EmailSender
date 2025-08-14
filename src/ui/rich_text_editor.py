from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, 
    QComboBox, QColorDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QFont, QTextCharFormat, QTextListFormat, QGuiApplication, 
    QFontDatabase
)


class RichTextEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.toolbar_layout = QHBoxLayout()
        self.build_toolbar()
        layout.addLayout(self.toolbar_layout)
        
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Arial", 12))
        layout.addWidget(self.text_edit)
    
    def build_toolbar(self):
        paste_text_btn = QPushButton("粘贴纯文本")
        paste_text_btn.setToolTip("从剪贴板粘贴纯文本，清除所有格式")
        paste_text_btn.clicked.connect(self.paste_as_plain_text)
        
        self.act_bold = QPushButton("B")
        self.act_bold.setCheckable(True)
        font = self.act_bold.font()
        font.setBold(True)
        self.act_bold.setFont(font)
        
        self.act_italic = QPushButton("I")
        self.act_italic.setCheckable(True)
        font = self.act_italic.font()
        font.setItalic(True)
        self.act_italic.setFont(font)
        
        self.act_under = QPushButton("U")
        self.act_under.setCheckable(True)
        font = self.act_under.font()
        font.setUnderline(True)
        self.act_under.setFont(font)
        
        self.act_bullet = QPushButton("•")
        self.act_bullet.setToolTip("项目符号列表")
        
        self.font_combo = QComboBox()
        self.font_combo.addItems(QFontDatabase.families())
        
        self.size_combo = QComboBox()
        self.size_combo.addItems([str(s) for s in [8, 9, 10, 11, 12, 14, 16, 18, 24, 36, 48]])
        self.size_combo.setCurrentText("12")
        
        color_btn = QPushButton("颜色")
        color_btn.clicked.connect(self.set_text_color)
        
        for btn in [paste_text_btn, self.act_bold, self.act_italic, self.act_under, self.act_bullet]:
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setFixedWidth(100)
            self.toolbar_layout.addWidget(btn)
        
        color_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        self.toolbar_layout.addSpacing(10)
        self.toolbar_layout.addWidget(self.font_combo, 1)
        self.toolbar_layout.addWidget(self.size_combo)
        self.toolbar_layout.addWidget(color_btn)
        self.toolbar_layout.addStretch()
    
    def setup_connections(self):
        self.font_combo.currentTextChanged.connect(self.set_selection_font_family)
        self.size_combo.currentTextChanged.connect(self.set_selection_font_size)
        
        self.act_bold.toggled.connect(self.toggle_bold)
        self.act_italic.toggled.connect(self.toggle_italic)
        self.act_under.toggled.connect(self.toggle_underline)
        self.act_bullet.clicked.connect(self.insert_bullet)
        
        self.text_edit.cursorPositionChanged.connect(self.sync_toolbar_state)
    
    def toggle_bold(self, checked):
        self.text_edit.setFocus()
        if self.text_edit.textCursor().hasSelection():
            char_format = QTextCharFormat()
            char_format.setFontWeight(QFont.Bold if checked else QFont.Normal)
            self.text_edit.textCursor().mergeCharFormat(char_format)
        else:
            self.text_edit.setFontWeight(QFont.Bold if checked else QFont.Normal)
    
    def toggle_italic(self, checked):
        self.text_edit.setFocus()
        if self.text_edit.textCursor().hasSelection():
            char_format = QTextCharFormat()
            char_format.setFontItalic(checked)
            self.text_edit.textCursor().mergeCharFormat(char_format)
        else:
            self.text_edit.setFontItalic(checked)
    
    def toggle_underline(self, checked):
        self.text_edit.setFocus()
        if self.text_edit.textCursor().hasSelection():
            char_format = QTextCharFormat()
            char_format.setFontUnderline(checked)
            self.text_edit.textCursor().mergeCharFormat(char_format)
        else:
            self.text_edit.setFontUnderline(checked)
    
    def set_selection_font_family(self, family):
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            char_format = QTextCharFormat()
            char_format.setFontFamilies([family])
            cursor.mergeCharFormat(char_format)
        self.text_edit.setFontFamily(family)
    
    def set_selection_font_size(self, size_str):
        if not size_str or not size_str.isdigit():
            return
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            char_format = QTextCharFormat()
            char_format.setFontPointSize(float(size_str))
            cursor.mergeCharFormat(char_format)
        self.text_edit.setFontPointSize(float(size_str))
    
    def set_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            cursor = self.text_edit.textCursor()
            if cursor.hasSelection():
                char_format = QTextCharFormat()
                char_format.setForeground(color)
                cursor.mergeCharFormat(char_format)
            else:
                self.text_edit.setTextColor(color)
    
    def paste_as_plain_text(self):
        self.text_edit.insertPlainText(QGuiApplication.clipboard().text())
    
    def sync_toolbar_state(self):
        self.act_bold.blockSignals(True)
        self.act_italic.blockSignals(True)
        self.act_under.blockSignals(True)
        self.font_combo.blockSignals(True)
        self.size_combo.blockSignals(True)
        
        self.act_bold.setChecked(self.text_edit.fontWeight() > QFont.Normal)
        self.act_italic.setChecked(self.text_edit.fontItalic())
        self.act_under.setChecked(self.text_edit.fontUnderline())
        self.font_combo.setCurrentText(self.text_edit.fontFamily())
        self.size_combo.setCurrentText(str(int(self.text_edit.fontPointSize())))
        
        self.act_bold.blockSignals(False)
        self.act_italic.blockSignals(False)
        self.act_under.blockSignals(False)
        self.font_combo.blockSignals(False)
        self.size_combo.blockSignals(False)
    
    def insert_bullet(self):
        self.text_edit.textCursor().insertList(QTextListFormat.ListDisc)
    
    def setPlaceholderText(self, text):
        self.text_edit.setPlaceholderText(text)
    
    def toHtml(self):
        return self.text_edit.toHtml()
    
    def toPlainText(self):
        return self.text_edit.toPlainText()
    
    def clear(self):
        self.text_edit.clear()
    
    def setHtml(self, html):
        self.text_edit.setHtml(html)
    
    def setPlainText(self, text):
        self.text_edit.setPlainText(text)
    
    def insertPlainText(self, text):
        self.text_edit.insertPlainText(text)
    
    def textCursor(self):
        return self.text_edit.textCursor()
    
    def setTextCursor(self, cursor):
        self.text_edit.setTextCursor(cursor)