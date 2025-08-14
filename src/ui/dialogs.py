import os
import webbrowser
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QRadioButton,
    QButtonGroup, QCheckBox, QWidget, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QGuiApplication
from src.graph.api import fetch_group_members

class AuthDialog(QDialog):
    def __init__(self, user_code, verify_uri, parent=None):
        super().__init__(parent)
        self.setWindowTitle("账户授权")
        lay = QVBoxLayout()
        lay.addWidget(QLabel("1. 已在浏览器打开授权页面。\n2. 输入以下一次性代码："))
        self.code = QLineEdit(user_code); self.code.setReadOnly(True)
        self.code.setFont(QFont("Courier", 18, QFont.Bold))
        lay.addWidget(self.code)
        copy_btn = QPushButton("复制代码"); copy_btn.clicked.connect(self.copy_code)
        lay.addWidget(copy_btn)
        self.setLayout(lay)
        webbrowser.open(verify_uri)
    def copy_code(self):
        QGuiApplication.clipboard().setText(self.code.text())
        QMessageBox.information(self, "已复制", "代码已复制到剪贴板！")

class VerificationDialog(QDialog):
    def __init__(self, match_results, parent=None):
        super().__init__(parent)
        self.setWindowTitle("个性化附件匹配结果预览")
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)
        text_area = QTextEdit(); text_area.setReadOnly(True)
        report_text = ""
        found_count = 0
        for name, files in match_results.items():
            if files:
                found_count += 1
                report_text += f"<b>{name}:</b><br>"
                for file in files:
                    report_text += f"&nbsp;&nbsp;&nbsp;&nbsp;- {os.path.basename(file)}<br>"
                report_text += "<br>"
        if found_count == 0:
            report_text = "在指定文件夹中，未找到任何与Excel中姓名匹配的文件。"
        text_area.setHtml(report_text)
        ok_button = QPushButton("关闭"); ok_button.clicked.connect(self.accept)
        layout.addWidget(text_area)
        layout.addWidget(ok_button)

class GroupSelectionDialog(QDialog):
    def __init__(self, groups, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择Microsoft 365群组")
        self.setMinimumSize(700, 500)
        self.groups = groups
        self.selected_recipients = []
        self.sending_mode = "group"  # "group" or "members"
        
        layout = QVBoxLayout(self)
        
        # 说明文字
        info_label = QLabel(
            "请选择要发送邮件的Microsoft 365群组，然后选择发送方式："
        )
        layout.addWidget(info_label)
        
        # 群组列表
        self.group_table = QTableWidget()
        self.group_table.setColumnCount(4)
        self.group_table.setHorizontalHeaderLabels(["选择", "群组名称", "群组邮箱", "成员数"])
        self.group_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.group_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.group_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.group_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.group_table.setShowGrid(False)
        
        # 填充群组数据
        self.group_table.setRowCount(len(groups))
        self.group_checkboxes = []
        
        for i, group in enumerate(groups):
            # 选择框
            checkbox = QCheckBox()
            self.group_checkboxes.append(checkbox)
            
            # Center the checkbox in the cell
            cell_widget = QWidget()
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.addWidget(checkbox)
            cell_layout.setAlignment(Qt.AlignCenter)
            cell_layout.setContentsMargins(0,0,0,0)
            cell_widget.setLayout(cell_layout)
            self.group_table.setCellWidget(i, 0, cell_widget)
            
            # 群组名称
            name_item = QTableWidgetItem(group['displayName'])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.group_table.setItem(i, 1, name_item)
            
            # 群组邮箱
            email_item = QTableWidgetItem(group['mail'])
            email_item.setFlags(email_item.flags() & ~Qt.ItemIsEditable)
            self.group_table.setItem(i, 2, email_item)
            
            # 成员数量（暂不获取，等用户选择时再获取）
            member_count_item = QTableWidgetItem("点击预览查看")
            member_count_item.setFlags(member_count_item.flags() & ~Qt.ItemIsEditable)
            self.group_table.setItem(i, 3, member_count_item)
        
        layout.addWidget(self.group_table)
        
        # 发送方式选择
        mode_group = QVBoxLayout()
        mode_label = QLabel("<b>邮件发送方式:</b>")
        mode_group.addWidget(mode_label)
        
        self.mode_button_group = QButtonGroup()
        self.group_radio = QRadioButton("发送到群组邮箱地址（群组成员都会收到）")
        self.members_radio = QRadioButton("发送到群组成员的个人邮箱（每个成员收到个人邮件）")
        
        self.group_radio.setChecked(True)  # 默认选择群组邮箱
        self.mode_button_group.addButton(self.group_radio, 0)
        self.mode_button_group.addButton(self.members_radio, 1)
        
        mode_group.addWidget(self.group_radio)
        mode_group.addWidget(self.members_radio)
        layout.addLayout(mode_group)
        
        # 预览区域
        preview_label = QLabel("<b>预览收件人:</b>")
        layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        preview_btn = QPushButton("预览收件人")
        preview_btn.clicked.connect(self.preview_recipients)
        
        ok_btn = QPushButton("确认选择")
        ok_btn.clicked.connect(self.accept_selection)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(preview_btn)
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def preview_recipients(self):
        """预览将要发送邮件的收件人"""
        selected_groups = []
        
        for i, checkbox in enumerate(self.group_checkboxes):
            if checkbox.isChecked():
                if i < len(self.groups):
                    selected_groups.append(self.groups[i])
        
        if not selected_groups:
            self.preview_text.setPlainText("请先选择至少一个群组")
            return
        
        if self.group_radio.isChecked():
            # 发送到群组邮箱
            preview_text = "发送方式: 群组邮箱地址\n\n收件人:\n"
            for group in selected_groups:
                preview_text += f"• {group['displayName']} ({group['mail']})\n"
        else:
            # 发送到成员个人邮箱 - 现在才获取成员列表
            preview_text = "发送方式: 群组成员个人邮箱\n\n正在获取成员列表..."
            self.preview_text.setPlainText(preview_text)
            
            all_members = []
            parent_app = self.parent()
            
            for group in selected_groups:
                print(f"Debug: Fetching members for group: {group['displayName']}")
                members = fetch_group_members(parent_app, group['id'])
                
                # 更新表格中的成员数量显示
                for i, table_group in enumerate(self.groups):
                    if table_group['id'] == group['id']:
                        count_text = f"{len(members)} 人" if members else "无成员"
                        member_count_item = QTableWidgetItem(count_text)
                        member_count_item.setFlags(member_count_item.flags() & ~Qt.ItemIsEditable)
                        self.group_table.setItem(i, 3, member_count_item)
                        break
                
                for member in members:
                    member_copy = member.copy()
                    member_copy['group_name'] = group['displayName']
                    # 避免重复成员
                    if not any(m['id'] == member_copy['id'] for m in all_members):
                        all_members.append(member_copy)
            
            if all_members:
                preview_text = f"发送方式: 群组成员个人邮箱\n\n总共 {len(all_members)} 位收件人:\n\n"
                for member in all_members[:10]:  # 只显示前10个成员
                    preview_text += f"• {member['displayName']} ({member['email']}) - 来自 {member['group_name']}\n"
                if len(all_members) > 10:
                    preview_text += f"... 还有 {len(all_members) - 10} 位成员\n"
            else:
                preview_text = "发送方式: 群组成员个人邮箱\n\n未找到群组成员，请检查权限设置。"
        
        self.preview_text.setPlainText(preview_text)
    
    def accept_selection(self):
        """确认选择并准备收件人数据"""
        selected_groups = []
        for i, checkbox in enumerate(self.group_checkboxes):
            if checkbox.isChecked():
                selected_groups.append(self.groups[i])
        
        if not selected_groups:
            QMessageBox.warning(self, "提示", "请至少选择一个群组")
            return
        
        self.selected_recipients = []
        self.sending_mode = "group" if self.group_radio.isChecked() else "members"
        
        if self.sending_mode == "group":
            # 使用群组邮箱地址
            for group in selected_groups:
                self.selected_recipients.append({
                    'name': group['displayName'],
                    'email': group['mail'] or group.get('mailNickname', '') + '@' + group.get('mail', '').split('@')[-1] if group.get('mail') else '',
                    'type': 'group',
                    'group_name': group['displayName'],
                    'group_description': group.get('description', ''),
                    'group_email': group['mail'] or '',
                    'group_id': group['id']
                })
        else:
            # 使用群组成员的个人邮箱
            parent_app = self.parent()
            for group in selected_groups:
                members = fetch_group_members(parent_app, group['id'])
                for member in members:
                    self.selected_recipients.append({
                        'name': member['displayName'],
                        'email': member['email'],
                        'type': 'member',
                        'group_name': group['displayName'],
                        'group_description': group.get('description', ''),
                        'group_email': group['mail'] or '',
                        'job_title': member.get('jobTitle', ''),
                        'department': member.get('department', ''),
                        'member_type': '成员' if not member.get('isOwner') else '所有者'
                    })
        
        self.accept()