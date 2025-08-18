#!/usr/bin/env python3
"""
简化的富文本编辑器 - 不依赖WebEngine
使用原生Qt组件，更稳定且易于打包
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QToolBar, QPushButton, QFontComboBox, QSpinBox,
    QColorDialog, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QTextCursor, QAction, QIcon
import re

class SimpleRichTextEditor(QWidget):
    """简化的富文本编辑器"""
    
    content_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        
        # 工具栏
        self.toolbar = self.create_toolbar()
        layout.addWidget(self.toolbar)
        
        # 文本编辑器
        self.text_edit = QTextEdit()
        self.text_edit.setAcceptRichText(True)
        self.text_edit.textChanged.connect(self.content_changed.emit)
        layout.addWidget(self.text_edit)
        
        # 设置样式
        self.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                line-height: 1.4;
            }
            QToolBar {
                border: none;
                spacing: 2px;
                background: #f8f9fa;
                padding: 4px;
            }
            QPushButton {
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 4px 8px;
                background: white;
                min-width: 30px;
                min-height: 25px;
            }
            QPushButton:hover {
                background: #e9ecef;
            }
            QPushButton:pressed {
                background: #dee2e6;
            }
            QPushButton:checked {
                background: #007bff;
                color: white;
                border-color: #0056b3;
            }
        """)
    
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        
        # 字体选择
        self.font_combo = QFontComboBox()
        self.font_combo.setMaximumWidth(150)
        self.font_combo.currentFontChanged.connect(self.change_font_family)
        toolbar.addWidget(self.font_combo)
        
        toolbar.addSeparator()
        
        # 字体大小
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 72)
        self.font_size.setValue(12)
        self.font_size.setSuffix("pt")
        self.font_size.valueChanged.connect(self.change_font_size)
        toolbar.addWidget(self.font_size)
        
        toolbar.addSeparator()
        
        # 粗体
        self.bold_btn = QPushButton("B")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.bold_btn.clicked.connect(self.toggle_bold)
        toolbar.addWidget(self.bold_btn)
        
        # 斜体
        self.italic_btn = QPushButton("I")
        self.italic_btn.setCheckable(True)
        italic_font = QFont("Arial", 10)
        italic_font.setItalic(True)
        self.italic_btn.setFont(italic_font)
        self.italic_btn.clicked.connect(self.toggle_italic)
        toolbar.addWidget(self.italic_btn)
        
        # 下划线
        self.underline_btn = QPushButton("U")
        self.underline_btn.setCheckable(True)
        underline_font = QFont("Arial", 10)
        underline_font.setUnderline(True)
        self.underline_btn.setFont(underline_font)
        self.underline_btn.clicked.connect(self.toggle_underline)
        toolbar.addWidget(self.underline_btn)
        
        toolbar.addSeparator()
        
        # 文字颜色
        self.color_btn = QPushButton("A")
        self.color_btn.setStyleSheet("QPushButton { color: black; font-weight: bold; }")
        self.color_btn.clicked.connect(self.change_text_color)
        toolbar.addWidget(self.color_btn)
        
        toolbar.addSeparator()
        
        # 对齐方式
        self.align_combo = QComboBox()
        self.align_combo.addItems(["左对齐", "居中", "右对齐", "两端对齐"])
        self.align_combo.currentTextChanged.connect(self.change_alignment)
        toolbar.addWidget(self.align_combo)
        
        toolbar.addSeparator()
        
        # 列表
        self.bullet_btn = QPushButton("• 列表")
        self.bullet_btn.clicked.connect(self.insert_bullet_list)
        toolbar.addWidget(self.bullet_btn)
        
        self.number_btn = QPushButton("1. 编号")
        self.number_btn.clicked.connect(self.insert_number_list)
        toolbar.addWidget(self.number_btn)
        
        toolbar.addSeparator()
        
        # 插入变量
        self.variable_combo = QComboBox()
        self.variable_combo.addItems([
            "选择变量...", "{{姓名}}", "{{名字}}", "{{邮箱}}", 
            "{{公司}}", "{{部门}}", "{{职位}}"
        ])
        self.variable_combo.currentTextChanged.connect(self.insert_variable)
        toolbar.addWidget(self.variable_combo)
        
        return toolbar
    
    def change_font_family(self, font):
        """改变字体"""
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            format = cursor.charFormat()
            format.setFontFamily(font.family())
            cursor.mergeCharFormat(format)
    
    def change_font_size(self, size):
        """改变字体大小"""
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            format = cursor.charFormat()
            format.setFontPointSize(size)
            cursor.mergeCharFormat(format)
    
    def toggle_bold(self):
        """切换粗体"""
        cursor = self.text_edit.textCursor()
        format = cursor.charFormat()
        
        if self.bold_btn.isChecked():
            format.setFontWeight(QFont.Weight.Bold)
        else:
            format.setFontWeight(QFont.Weight.Normal)
        
        cursor.mergeCharFormat(format)
        self.text_edit.setTextCursor(cursor)
    
    def toggle_italic(self):
        """切换斜体"""
        cursor = self.text_edit.textCursor()
        format = cursor.charFormat()
        format.setFontItalic(self.italic_btn.isChecked())
        cursor.mergeCharFormat(format)
        self.text_edit.setTextCursor(cursor)
    
    def toggle_underline(self):
        """切换下划线"""
        cursor = self.text_edit.textCursor()
        format = cursor.charFormat()
        format.setFontUnderline(self.underline_btn.isChecked())
        cursor.mergeCharFormat(format)
        self.text_edit.setTextCursor(cursor)
    
    def change_text_color(self):
        """改变文字颜色"""
        color = QColorDialog.getColor(Qt.GlobalColor.black, self)
        if color.isValid():
            cursor = self.text_edit.textCursor()
            format = cursor.charFormat()
            format.setForeground(color)
            cursor.mergeCharFormat(format)
            self.text_edit.setTextCursor(cursor)
            
            # 更新按钮颜色
            self.color_btn.setStyleSheet(f"""
                QPushButton {{ 
                    color: {color.name()}; 
                    font-weight: bold; 
                }}
            """)
    
    def change_alignment(self, alignment_text):
        """改变对齐方式"""
        cursor = self.text_edit.textCursor()
        
        alignment_map = {
            "左对齐": Qt.AlignmentFlag.AlignLeft,
            "居中": Qt.AlignmentFlag.AlignCenter,
            "右对齐": Qt.AlignmentFlag.AlignRight,
            "两端对齐": Qt.AlignmentFlag.AlignJustify
        }
        
        alignment = alignment_map.get(alignment_text, Qt.AlignmentFlag.AlignLeft)
        
        block_format = cursor.blockFormat()
        block_format.setAlignment(alignment)
        cursor.setBlockFormat(block_format)
        self.text_edit.setTextCursor(cursor)
    
    def insert_bullet_list(self):
        """插入项目符号列表"""
        cursor = self.text_edit.textCursor()
        cursor.insertText("• ")
        self.text_edit.setTextCursor(cursor)
    
    def insert_number_list(self):
        """插入编号列表"""
        cursor = self.text_edit.textCursor()
        cursor.insertText("1. ")
        self.text_edit.setTextCursor(cursor)
    
    def insert_variable(self, variable):
        """插入变量"""
        if variable and variable != "选择变量...":
            cursor = self.text_edit.textCursor()
            cursor.insertText(variable)
            self.text_edit.setTextCursor(cursor)
            
            # 重置选择
            self.variable_combo.setCurrentIndex(0)
    
    def get_content(self):
        """获取内容"""
        return self.text_edit.toHtml()
    
    def set_content(self, content):
        """设置内容"""
        # 如果是纯文本，直接设置
        if not content.startswith('<'):
            self.text_edit.setPlainText(content)
        else:
            self.text_edit.setHtml(content)
    
    def get_plain_text(self):
        """获取纯文本"""
        return self.text_edit.toPlainText()
    
    def set_plain_text(self, text):
        """设置纯文本"""
        self.text_edit.setPlainText(text)
    
    def clear(self):
        """清空内容"""
        self.text_edit.clear()


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication, QMainWindow
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    editor = SimpleRichTextEditor()
    window.setCentralWidget(editor)
    window.setWindowTitle("简化富文本编辑器测试")
    window.resize(800, 600)
    window.show()
    
    sys.exit(app.exec())