import sys, os, time, json, atexit, base64, mimetypes, webbrowser, re
from datetime import datetime
import pandas as pd
import requests, msal
import jinja2
from dotenv import load_dotenv
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QLineEdit, QFileDialog, QComboBox, QMessageBox, QFrame,
    QDialog, QProgressBar, QListWidget, QListWidgetItem, QStyle,
    QTableWidget, QTableWidgetItem, QHeaderView, QRadioButton, QButtonGroup, QCheckBox,
    QScrollArea, QGroupBox, QTabWidget
)
from PySide6.QtCore import QObject, Signal, QThread, Qt
from PySide6.QtGui import (
    QFont, QGuiApplication, QPalette, QColor
)
from src.ui.dialogs import AuthDialog, VerificationDialog, GroupSelectionDialog
from src.ui.tinymce_editor import TinyMCEEditor
from src.graph.auth import ensure_token, _save_token_cache
from src.graph.api import fetch_user_groups, fetch_group_members
from src.config.field_mapper import FieldMapper

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
TENANT_ID = os.getenv('AZURE_TENANT_ID')
TOKEN_CACHE_FILE = "token_cache.json"
TEST_SELF_EMAIL = os.getenv('TEST_SELF_EMAIL')
SETTINGS_FILE = "settings.json"

class MailWorker(QObject):
    progress = Signal(int, int)
    finished = Signal()
    error = Signal(str)

    def __init__(self, token, df, email_col, name_col, subj_tpl, body_tpl_html, 
                 common_attachments, personalized_attachments_map, 
                 action, test_mode):
        super().__init__()
        self.access_token, self.df, self.email_col, self.name_col = token, df, email_col, name_col
        self.subj_tpl, self.body_tpl_html = subj_tpl, body_tpl_html
        self.common_attachments, self.personalized_attachments_map = common_attachments, personalized_attachments_map
        self.action, self.test_mode = action, test_mode
        self.jinja_env = jinja2.Environment(autoescape=True, trim_blocks=True, lstrip_blocks=True)

    def run(self):
        try:
            subject_template = self.jinja_env.from_string(self.subj_tpl)
            body_template = self.jinja_env.from_string(self.body_tpl_html)
            total = len(self.df)
            for idx, row in self.df.iterrows():
                to_addr = TEST_SELF_EMAIL if self.test_mode else row[self.email_col]
                expert_name = row.get(self.name_col, '')
                context = row.to_dict()
                
                # Add datetime variables
                now = datetime.now()
                context.update({
                    '当前日期': now.strftime('%Y年%m月%d日'),
                    '当前时间': now.strftime('%H:%M:%S'),
                    '年份': now.strftime('%Y'),
                    '月份': now.strftime('%m')
                })
                
                # Add group variables if available (they're already in context from row.to_dict())
                # Just ensure they have default values if not present
                context.setdefault('群组名称', '')
                context.setdefault('群组描述', '')
                context.setdefault('群组邮箱', '')
                context.setdefault('成员类型', '成员')
                context.setdefault('部门', '')
                context.setdefault('职位', '')
                
                final_subject, final_body = subject_template.render(context), body_template.render(context)
                personalized_files = self.personalized_attachments_map.get(expert_name, [])
                all_attachments = self.common_attachments + personalized_files
                ok, msg = self._send_graph(to_addr, final_subject, final_body, all_attachments, self.action)
                if not ok:
                    self.error.emit(f"第 {idx+1} 行 ({expert_name}) 发送失败：\n{msg}")
                    return
                self.progress.emit(idx + 1, total)
                time.sleep(0.5)
        except Exception as e:
            self.error.emit(f"处理邮件模板时发生错误：\n{e}\n\n请检查占位符格式是否为 {{列名}}。")
            return
        self.finished.emit()

    def _send_graph(self, to_addr, subject, body_html, attachments, action):
        headers = { "Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json" }
        att_payload = []
        for fp in attachments:
            try:
                with open(fp, "rb") as f: content_b64 = base64.b64encode(f.read()).decode()
                mime, _ = mimetypes.guess_type(fp)
                att_payload.append({"@odata.type": "#microsoft.graph.fileAttachment", "name": os.path.basename(fp), "contentType": mime or "application/octet-stream", "contentBytes": content_b64})
            except Exception as e:
                return False, f"附件 {os.path.basename(fp)} 处理失败: {e}"
        message = {"subject": subject, "body": {"contentType": "HTML", "content": body_html}, "toRecipients": [{"emailAddress": {"address": to_addr}}], "attachments": att_payload}
        if action == "SEND":
            endpoint = f"https://graph.microsoft.com/v1.0/me/sendMail"
            payload = {"message": message, "saveToSentItems": True}
            r = requests.post(endpoint, headers=headers, json=payload)
        else:
            endpoint = f"https://graph.microsoft.com/v1.0/me/messages"
            r = requests.post(endpoint, headers=headers, json=message)
        if r.status_code in (200, 201, 202): return True, "Success"
        return False, f"{r.status_code}: {r.text}"

class MailerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.df, self.access_token, self.thread, self.worker = None, None, None, None
        self.is_formal_send = False
        self.personalized_attachment_folder = None
        self.personalized_attachments_map = {}
        self.user_groups = []
        self.selected_group_recipients = []
        self.field_mapper = FieldMapper()  # Initialize field mapper
        self.token_cache = msal.SerializableTokenCache()
        if os.path.exists(TOKEN_CACHE_FILE):
            try:
                with open(TOKEN_CACHE_FILE, "r", encoding="utf-8") as f: self.token_cache.deserialize(f.read())
            except Exception as e: print("加载 token 缓存失败:", e)
        atexit.register(lambda: _save_token_cache(self.token_cache))
        self.msal_app = msal.PublicClientApplication(
            CLIENT_ID, authority=f"https://login.microsoftonline.com/{TENANT_ID}",
            token_cache=self.token_cache
        )
        self._load_settings()
        self._build_ui()

    def _load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading settings: {e}")
                self.settings = {"theme": "Light"}
        else:
            self.settings = {"theme": "Light"}

    def _save_settings(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)
        except IOError as e:
            print(f"Error saving settings: {e}")

    def set_theme(self, theme):
        if theme == "Dark":
            self.settings["theme"] = "Dark"
            QApplication.instance().setStyle("Fusion")
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
            dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
            dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
            QApplication.instance().setPalette(dark_palette)
            QApplication.instance().setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; } QWidget { font-size: 13px; }")
        else:
            self.settings["theme"] = "Light"
            QApplication.instance().setStyle("Fusion")
            QApplication.instance().setPalette(QApplication.style().standardPalette())
            QApplication.instance().setStyleSheet("")
        
        # Update TinyMCE editor theme if it exists
        if hasattr(self, 'body_editor'):
            self.body_editor.setTheme(theme)
        
        self._save_settings()


    def _build_ui(self):
        self.setWindowTitle('个性化邮件发送助手')
        # Center window on screen instead of sticking to top
        self.resize(900, 850)
        screen = QGuiApplication.primaryScreen().geometry()
        x = (screen.width() - 900) // 2
        y = (screen.height() - 850) // 2
        self.move(x, y)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Add progress bar at top
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setTextVisible(False)
        main_layout.addWidget(self.progress)
        
        # Add toolbar with field config and theme selector at top
        toolbar_layout = QHBoxLayout()
        
        # Field configuration button
        config_btn = QPushButton("⚙️ 字段配置")
        config_btn.setToolTip("配置字段映射关系")
        config_btn.clicked.connect(self.open_field_config)
        toolbar_layout.addWidget(config_btn)
        
        toolbar_layout.addStretch()
        
        # Theme selector
        toolbar_layout.addWidget(QLabel("Theme:"))
        theme_combo = QComboBox()
        theme_combo.addItems(["Light", "Dark"])
        theme_combo.setCurrentText(self.settings.get("theme", "Light"))
        theme_combo.currentTextChanged.connect(self.set_theme)
        toolbar_layout.addWidget(theme_combo)
        
        main_layout.addLayout(toolbar_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_excel_tab()
        self._create_group_tab()
        
        # Add shared email composition area at bottom
        self._create_email_composition_area(main_layout)
        
        # Connect tab change event to update variables
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # Don't initialize preview data at startup - wait for user action

    def _create_excel_tab(self):
        """Create the Excel file tab content"""
        excel_widget = QWidget()
        excel_layout = QVBoxLayout(excel_widget)
        excel_layout.setSpacing(15)
        excel_layout.setContentsMargins(10, 10, 10, 10)
        
        # Section 1: Excel File Loading
        file_section = QGroupBox("Excel 文件")
        file_layout = QVBoxLayout(file_section)
        
        file_load_layout = QHBoxLayout()
        load_btn = QPushButton("加载 Excel 文件...")
        load_btn.clicked.connect(self.load_excel)
        self.excel_label = QLabel("尚未加载Excel文件")
        file_load_layout.addWidget(load_btn)
        file_load_layout.addWidget(self.excel_label, 1)
        file_layout.addLayout(file_load_layout)
        
        # Column selection
        column_layout = QHBoxLayout()
        column_layout.addWidget(QLabel("姓名列:"))
        self.name_combo = QComboBox()
        column_layout.addWidget(self.name_combo, 1)
        column_layout.addWidget(QLabel("邮箱列:"))
        self.email_combo = QComboBox()
        column_layout.addWidget(self.email_combo, 1)
        file_layout.addLayout(column_layout)
        
        excel_layout.addWidget(file_section)
        
        # Section 2: Filtering
        filter_section = QGroupBox("筛选收件人 (选填)")
        filter_layout = QVBoxLayout(filter_section)
        
        self.filters = []
        for i in range(3):
            filter_row_layout = QHBoxLayout()
            col_combo = QComboBox()
            col_combo.addItem("【不筛选】")
            val_input = QLineEdit()
            val_input.setPlaceholderText("在此输入筛选值")
            
            filter_row_layout.addWidget(QLabel(f"筛选条件 {i+1}:"))
            filter_row_layout.addWidget(col_combo, 1)
            filter_row_layout.addWidget(QLabel("值为"))
            filter_row_layout.addWidget(val_input, 1)
            filter_layout.addLayout(filter_row_layout)
            
            self.filters.append((col_combo, val_input))
            col_combo.currentIndexChanged.connect(self.update_filtered_count)
            val_input.textChanged.connect(self.update_filtered_count)
        
        self.filtered_count_label = QLabel("筛选后将发送给: <b>...</b> 人")
        filter_layout.addWidget(self.filtered_count_label, 0, Qt.AlignmentFlag.AlignRight)
        
        excel_layout.addWidget(filter_section)
        excel_layout.addStretch()
        
        self.tab_widget.addTab(excel_widget, "从 Excel 文件")

    def _create_group_tab(self):
        """Create the Microsoft 365 Groups tab content"""
        group_widget = QWidget()
        group_layout = QVBoxLayout(group_widget)
        group_layout.setSpacing(15)
        group_layout.setContentsMargins(10, 10, 10, 10)
        
        # Section 1: Group Selection
        group_section = QGroupBox("Microsoft 365 群组")
        group_section_layout = QVBoxLayout(group_section)
        
        group_btn_layout = QHBoxLayout()
        group_btn = QPushButton("选择 Microsoft 365 群组...")
        group_btn.clicked.connect(self.select_groups)
        self.group_label = QLabel("未选择群组收件人")
        group_btn_layout.addWidget(group_btn)
        group_btn_layout.addWidget(self.group_label, 1)
        group_section_layout.addLayout(group_btn_layout)
        
        group_layout.addWidget(group_section)
        group_layout.addStretch()
        
        self.tab_widget.addTab(group_widget, "从 Microsoft 365 群组")

    def _create_email_composition_area(self, main_layout):
        """Create the shared email composition area"""
        composition_frame = QFrame()
        composition_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        composition_layout = QVBoxLayout(composition_frame)
        composition_layout.setSpacing(10)
        composition_layout.setContentsMargins(10, 10, 10, 10)
        
        # Email subject
        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("邮件主题:"))
        self.subject_input = QLineEdit()
        self.subject_input.setFont(QFont("Arial", 12))
        subject_layout.addWidget(self.subject_input)
        composition_layout.addLayout(subject_layout)
        
        # Email body
        composition_layout.addWidget(QLabel("邮件正文:"))
        self.body_editor = TinyMCEEditor()
        self.body_editor.setPlaceholderText("例如：尊敬的 {{姓名}} 专家，您好！")
        composition_layout.addWidget(self.body_editor)
        
        # Attachments
        attachments_layout = QHBoxLayout()
        
        # Personalized attachments
        pa_group = QGroupBox("个性化附件 (按姓名匹配)")
        pa_layout = QVBoxLayout(pa_group)
        self.pa_folder_label = QLabel("<i>尚未选择文件夹</i>")
        pa_layout.addWidget(self.pa_folder_label)
        
        pa_btn_layout = QHBoxLayout()
        select_pa_folder_btn = QPushButton("选择文件夹...")
        preview_pa_btn = QPushButton("预览匹配结果")
        select_pa_folder_btn.clicked.connect(self.select_personalized_folder)
        preview_pa_btn.clicked.connect(self.preview_matches)
        pa_btn_layout.addWidget(select_pa_folder_btn)
        pa_btn_layout.addWidget(preview_pa_btn)
        pa_btn_layout.addStretch()
        pa_layout.addLayout(pa_btn_layout)
        
        # Common attachments
        ca_group = QGroupBox("通用附件 (发送给所有人)")
        ca_layout = QVBoxLayout(ca_group)
        self.att_list = QListWidget()
        self.att_list.setFixedHeight(60)
        ca_layout.addWidget(self.att_list)
        
        ca_btn_layout = QHBoxLayout()
        add_att_btn = QPushButton("添加...")
        rm_att_btn = QPushButton("移除")
        add_att_btn.clicked.connect(self.add_common_attachment)
        rm_att_btn.clicked.connect(self.remove_common_attachment)
        ca_btn_layout.addWidget(add_att_btn)
        ca_btn_layout.addWidget(rm_att_btn)
        ca_btn_layout.addStretch()
        ca_layout.addLayout(ca_btn_layout)
        
        attachments_layout.addWidget(pa_group)
        attachments_layout.addWidget(ca_group)
        composition_layout.addLayout(attachments_layout)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.draft_btn = QPushButton("内部测试(草稿)")
        self.test_btn = QPushButton("内部测试(发给自己)")
        self.send_btn = QPushButton("!!! 正式发送 !!!")
        
        self.draft_btn.setStyleSheet("background:#DAA520;color:white;border-radius:5px;padding:8px;")
        self.test_btn.setStyleSheet("background:#4682B4;color:white;border-radius:5px;padding:8px;")
        self.send_btn.setStyleSheet("background:#B22222;color:white;font-weight:bold;border-radius:5px;padding:8px;")
        
        self.draft_btn.clicked.connect(lambda: self.run_process('SAVE_DRAFT', True))
        self.test_btn.clicked.connect(lambda: self.run_process('SEND', True))
        self.send_btn.clicked.connect(lambda: self.run_process('SEND', False))
        
        btn_layout.addWidget(self.draft_btn)
        btn_layout.addWidget(self.test_btn)
        btn_layout.addWidget(self.send_btn)
        btn_layout.addStretch()
        
        composition_layout.addLayout(btn_layout)
        main_layout.addWidget(composition_frame)

    def _on_tab_changed(self, index):
        """Handle tab change to update variable dropdown"""
        # Update preview data when tab changes
        self._update_preview_data()
    
    def open_field_config(self):
        """Open field configuration dialog"""
        try:
            from src.ui.field_config_dialog import FieldConfigDialog
            dialog = FieldConfigDialog(self)
            if dialog.exec() == QDialog.Accepted:
                # Reload configuration and update UI
                self.field_mapper = FieldMapper()  # Reload mapper with new config
                self._update_preview_data()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开字段配置对话框:\n{str(e)}")
    
    def load_excel(self):
        fp, _=QFileDialog.getOpenFileName(self, "选择Excel文件", "", "Excel Files (*.xlsx *.xls)")
        if not fp: return
        try:
            self.df = pd.read_excel(fp, dtype=str).fillna('')
            self.excel_label.setText(f"已加载: {os.path.basename(fp)} (共 {len(self.df)} 条)")
            columns = ["【不筛选】"] + list(self.df.columns)
            self.email_combo.clear(); self.email_combo.addItems(self.df.columns)
            self.name_combo.clear(); self.name_combo.addItems(self.df.columns)
            for col_combo, _ in self.filters:
                col_combo.clear(); col_combo.addItems(columns)
            self.update_filtered_count()
            # Update variable dropdown with Excel columns
            self.body_editor.update_variable_dropdown(list(self.df.columns))
            # Update preview data with first row
            self._update_preview_data()
        except Exception as e: QMessageBox.critical(self, "错误", f"读取 Excel 失败：\n{e}")

    def get_filtered_df(self):
        if self.df is None: return None
        filtered_df = self.df.copy()
        try:
            for col_combo, val_input in self.filters:
                col_name = col_combo.currentText()
                filter_val = val_input.text().strip()
                if col_name and col_name != "【不筛选】" and filter_val:
                    filtered_df = filtered_df[filtered_df[col_name].str.contains(filter_val, case=False, na=False)]
            return filtered_df
        except Exception as e:
            QMessageBox.critical(self, "筛选错误", f"应用筛选时出错:\n{e}"); return self.df

    def update_filtered_count(self):
        df = self.get_filtered_df()
        if df is not None: 
            self.filtered_count_label.setText(f"筛选后将发送给: <b>{len(df)}</b> 人")
            # Update preview data when filters change
            self._update_preview_data()

    def run_process(self, action: str, test_mode: bool):
        if not ensure_token(self): return
        
        recipients_df = None
        recipient_source = None
        
        # Determine data source based on active tab
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 0:  # Excel tab
            if self.df is not None:
                filtered_df = self.get_filtered_df()
                if filtered_df is not None and not filtered_df.empty:
                    recipients_df = filtered_df
                    recipient_source = "excel"
                else:
                    QMessageBox.warning(self, "提示", "Excel 文件未加载或筛选后无收件人。")
                    return
            else:
                QMessageBox.warning(self, "提示", "请先在 Excel 标签页中加载 Excel 文件。")
                return
                
        elif current_tab == 1:  # Group tab
            if hasattr(self, 'selected_group_recipients') and self.selected_group_recipients:
                import pandas as pd
                group_data = []
                for recipient in self.selected_group_recipients:
                    group_data.append({
                        '姓名': recipient['name'],
                        '邮箱': recipient['email'],
                        'type': recipient.get('type', 'group'),
                        '群组名称': recipient.get('group_name', ''),
                        '群组描述': recipient.get('group_description', ''),
                        '群组邮箱': recipient.get('group_email', ''),
                        '成员类型': recipient.get('member_type', '成员'),
                        '部门': recipient.get('department', ''),
                        '职位': recipient.get('job_title', '')
                    })
                recipients_df = pd.DataFrame(group_data)
                recipient_source = "group"
            else:
                QMessageBox.warning(self, "提示", "请先在群组标签页中选择 Microsoft 365 群组收件人。")
                return
        
        subj_tpl = self.subject_input.text()
        body_tpl = self.body_editor.toHtml()
        if not all([subj_tpl, self.body_editor.toPlainText().strip()]):
            QMessageBox.warning(self, "提示", "请完善邮件主题和正文。")
            return
        
        if recipient_source == "excel":
            email_col = self.email_combo.currentText()
            name_col = self.name_combo.currentText()
            if not all([email_col, name_col]):
                QMessageBox.warning(self, "提示", "请选择姓名列和邮箱列。")
                return
        else:
            email_col = "邮箱"
            name_col = "姓名"
        
        if (test_mode and action == "SEND"):
            if QMessageBox.question(self, "测试确认", f"全部发送到测试邮箱 {TEST_SELF_EMAIL}？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.No: return
        if not test_mode:
            source_text = "Excel" if recipient_source == "excel" else "群组"
            if QMessageBox.question(self, "正式群发确认", f"将向 {len(recipients_df)} 位{source_text}收件人正式发送邮件，确定继续？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.No: return
        
        self.is_formal_send = not test_mode
        if self.personalized_attachment_folder: self.match_and_verify_attachments(show_dialog=False)
        common_attachments = [self.att_list.item(i).text() for i in range(self.att_list.count())]
        self._lock_ui(True); self.progress.setMaximum(len(recipients_df)); self.progress.setValue(0); self.progress.setVisible(True)
        self.thread = QThread()
        self.worker = MailWorker(self.access_token, recipients_df, email_col, name_col, subj_tpl, body_tpl, common_attachments, self.personalized_attachments_map, action, test_mode)
        self.worker.moveToThread(self.thread); self.thread.started.connect(self.worker.run); self.worker.progress.connect(self._on_progress); self.worker.error.connect(self._on_error); self.worker.finished.connect(self._on_finished); self.thread.start()

    def _on_progress(self, cur, total):
        self.progress.setValue(cur)
        self.setWindowTitle(f'发送中 {cur}/{total}')

    def _on_error(self, msg):
        QMessageBox.critical(self, "错误", msg)
        self._end_thread()

    def _on_finished(self):
        QMessageBox.information(self, "完成", "所有邮件已处理完毕！")
        self._end_thread()
        if self.is_formal_send:
            self.reset_ui()

    def reset_ui(self):
        self.subject_input.clear()
        self.body_editor.clear()
        self.att_list.clear()
        self.pa_folder_label.setText("<i>尚未选择文件夹</i>")
        self.personalized_attachment_folder = None
        self.personalized_attachments_map = {}
        self.excel_label.setText("尚未加载Excel文件")
        self.email_combo.clear()
        self.name_combo.clear()
        for col_combo, val_input in self.filters:
            col_combo.clear()
            col_combo.addItem("【不筛选】")
            col_combo.setCurrentIndex(0)
            val_input.clear()
        self.filtered_count_label.setText("筛选后将发送给: <b>...</b> 人")
        self.df = None
        self.user_groups = []
        self.selected_group_recipients = []
        self.group_label.setText("未选择群组收件人")
        print("界面已彻底重置，准备下一个任务。")
        
    def _end_thread(self):
        if self.thread: self.thread.quit(); self.thread.wait()
        if self.worker: self.worker.deleteLater()
        self.thread=self.worker=None; self._lock_ui(False); self.progress.setVisible(False); self.setWindowTitle('个性化邮件发送助手')
        
    def _lock_ui(self, lock: bool):
        self.draft_btn.setEnabled(not lock); self.test_btn.setEnabled(not lock); self.send_btn.setEnabled(not lock)

    def _sep(self):
        l=QFrame(); l.setFrameShape(QFrame.HLine); l.setFrameShadow(QFrame.Sunken); return l

    def _vert_sep(self):
        l=QFrame(); l.setFrameShape(QFrame.VLine); l.setFrameShadow(QFrame.Sunken); return l

    def select_groups(self):
        if not ensure_token(self):
            return
        
        if not fetch_user_groups(self):
            return
        
        if not self.user_groups:
            QMessageBox.information(self, "提示", "未找到您有权访问的Microsoft 365群组")
            return
        
        dialog = GroupSelectionDialog(self.user_groups, self)
        if dialog.exec() == QDialog.Accepted:
            self.selected_group_recipients = dialog.selected_recipients
            
            if self.selected_group_recipients:
                recipient_count = len(self.selected_group_recipients)
                if dialog.sending_mode == "group":
                    self.group_label.setText(f"已选择 {recipient_count} 个群组邮箱")
                else:
                    self.group_label.setText(f"已选择 {recipient_count} 位群组成员")
                
                # Debug: Print selected recipients to verify data
                print(f"[DEBUG] Selected {recipient_count} recipients")
                if self.selected_group_recipients:
                    print(f"[DEBUG] First recipient: {self.selected_group_recipients[0]}")
            else:
                self.group_label.setText("未选择群组收件人")
            
            # Update preview data with group data - add a small delay to ensure data is ready
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, self._update_preview_data)

    def _update_preview_data(self):
        """Update preview data for the rich text editor with first instance data based on active tab"""
        preview_data = {}
        excel_columns = []
        
        # Add basic datetime variables
        now = datetime.now()
        preview_data.update({
            '当前日期': now.strftime('%Y年%m月%d日'),
            '当前时间': now.strftime('%H:%M:%S'),
            '年份': now.strftime('%Y'),
            '月份': now.strftime('%m')
        })
        
        # Check which tab is active
        current_tab = 0  # Default to Excel tab
        if hasattr(self, 'tab_widget'):
            current_tab = self.tab_widget.currentIndex()
            
            if current_tab == 0:  # Excel tab
                if self.df is not None and not self.df.empty:
                    filtered_df = self.get_filtered_df()
                    if filtered_df is not None and not filtered_df.empty:
                        # Use first row of filtered data
                        first_row = filtered_df.iloc[0]
                        for col in first_row.index:
                            # Handle different data types properly
                            val = first_row[col]
                            if pd.isna(val) or val is None or str(val).strip() == '':
                                preview_data[col] = f"[空-{col}]"
                            else:
                                preview_data[col] = str(val)
                        excel_columns = list(self.df.columns)
                    else:
                        # Default Excel placeholders with sample data
                        preview_data.update({
                            '姓名': '示例姓名',
                            '邮箱': 'example@email.com',
                            '部门': '示例部门',
                            '职位': '示例职位'
                        })
                        # Still add column names if available
                        if self.df is not None:
                            excel_columns = list(self.df.columns)
                else:
                    # No Excel data loaded, provide sample data
                    preview_data.update({
                        '姓名': '示例姓名',
                        '邮箱': 'example@email.com',
                        '部门': '示例部门',
                        '职位': '示例职位'
                    })
                    
            elif current_tab == 1:  # Group tab
                if hasattr(self, 'selected_group_recipients') and self.selected_group_recipients:
                    # Use first group recipient
                    first_recipient = self.selected_group_recipients[0]
                    
                    # Debug: Print the first recipient to see its structure
                    print(f"[DEBUG] First recipient data: {first_recipient}")
                    
                    # Directly map the fields without using field mapper for now
                    if first_recipient.get('type') == 'group':
                        # Group email address - use direct field names
                        preview_data.update({
                            '姓名': first_recipient.get('name', ''),
                            '邮箱': first_recipient.get('email', ''),
                            '群组名称': first_recipient.get('group_name', ''),
                            '群组描述': first_recipient.get('group_description', ''),
                            '群组邮箱': first_recipient.get('group_email', '')
                        })
                    else:
                        # Individual member - use direct field names
                        preview_data.update({
                            '姓名': first_recipient.get('name', ''),
                            '邮箱': first_recipient.get('email', ''),
                            '群组名称': first_recipient.get('group_name', ''),
                            '群组描述': first_recipient.get('group_description', ''),
                            '群组邮箱': first_recipient.get('group_email', ''),
                            '成员类型': first_recipient.get('member_type', '成员'),
                            '部门': first_recipient.get('department', ''),
                            '职位': first_recipient.get('job_title', '')
                        })
                else:
                    # No group data selected, provide sample defaults for testing
                    preview_data.update({
                        '姓名': '示例成员',
                        '邮箱': 'member@example.com',
                        '群组名称': '示例群组',
                        '群组描述': '示例群组描述',
                        '群组邮箱': 'group@example.com',
                        '成员类型': '成员',
                        '部门': '示例部门',
                        '职位': '示例职位'
                    })
        
        # Update the editor with preview data and variable dropdown
        if hasattr(self, 'body_editor') and self.body_editor:
            self.body_editor.set_preview_data(preview_data)
            
            # Update variable dropdown based on active tab
            if current_tab == 0:  # Excel tab
                # Show Excel columns
                # print(f"[DEBUG] Excel tab - updating dropdown with columns: {excel_columns}")
                self.body_editor.update_variable_dropdown(excel_columns)
            else:  # Group tab
                # Show common group and member variables
                group_vars = ['姓名', '邮箱', '群组名称', '群组描述', '群组邮箱', '成员类型', '部门', '职位']
                # print(f"[DEBUG] Group tab - updating dropdown with variables: {group_vars}")
                self.body_editor.update_variable_dropdown(group_vars)

    def add_common_attachment(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择通用附件"); [self.att_list.addItem(f) for f in files]

    def remove_common_attachment(self):
        [self.att_list.takeItem(self.att_list.row(item)) for item in self.att_list.selectedItems()]

    def select_personalized_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择包含个性化附件的文件夹")
        if folder: self.personalized_attachment_folder = folder; self.pa_folder_label.setText(f"文件夹: ...{folder[-30:]}"); self.match_and_verify_attachments(show_dialog=False)

    def preview_matches(self):
        if not self.personalized_attachment_folder: QMessageBox.warning(self, "提示", "请先选择一个附件文件夹。"); return
        self.match_and_verify_attachments(show_dialog=True)

    def match_and_verify_attachments(self, show_dialog=True):
        self.personalized_attachments_map = {}
        expert_names = []
        
        # Get names based on active tab
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 0:  # Excel tab
            if self.df is None:
                if show_dialog: QMessageBox.warning(self, "提示", "请先加载Excel文件。"); return
                return
            name_col = self.name_combo.currentText()
            if not name_col:
                if show_dialog: QMessageBox.warning(self, "提示", "请先选择包含'专家姓名'的列。"); return
                return
            expert_names = self.df[name_col].unique()
            
        elif current_tab == 1:  # Group tab
            if hasattr(self, 'selected_group_recipients') and self.selected_group_recipients:
                expert_names = [recipient['name'] for recipient in self.selected_group_recipients if recipient.get('name')]
            else:
                if show_dialog: QMessageBox.warning(self, "提示", "请先选择群组收件人。"); return
                return
        
        # Match names with files
        for name in expert_names:
            if not name: continue
            self.personalized_attachments_map[name] = [os.path.join(self.personalized_attachment_folder, f) for f in os.listdir(self.personalized_attachment_folder) if name in f]
        
        if show_dialog:
            dialog = VerificationDialog(self.personalized_attachments_map, self); dialog.exec()