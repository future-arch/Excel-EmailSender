# -*- coding: utf-8 -*-
"""
个性化邮件发送助手（Microsoft Graph + PySide6 + Jinja2）- Bug修复版 v9
Author: WEILAI & Gemini & Claude
"""
import sys, os, time, json, atexit, base64, mimetypes, webbrowser, re
import pandas as pd
import requests, msal
import jinja2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QLineEdit, QFileDialog, QComboBox, QMessageBox, QFrame,
    QDialog, QProgressBar, QListWidget, QListWidgetItem, QStyle, QColorDialog
)
from PySide6.QtCore import QObject, Signal, QThread, Qt
from PySide6.QtGui import (
    QFont, QAction, QTextListFormat, QGuiApplication, QPalette, QColor,
    QFontDatabase, QTextCharFormat, QTextCursor
)

# ------------------ 配置区 ------------------
CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
TENANT_ID = os.getenv('AZURE_TENANT_ID')
SCOPES = ["Mail.Send", "Mail.ReadWrite", "User.Read"]
TOKEN_CACHE_FILE = "token_cache.json"
TEST_SELF_EMAIL = os.getenv('TEST_SELF_EMAIL')
GRAPH_ROOT = "https://graph.microsoft.com/v1.0"

# Validate required environment variables
if not all([CLIENT_ID, TENANT_ID, TEST_SELF_EMAIL]):
    missing_vars = []
    if not CLIENT_ID: missing_vars.append('AZURE_CLIENT_ID')
    if not TENANT_ID: missing_vars.append('AZURE_TENANT_ID')
    if not TEST_SELF_EMAIL: missing_vars.append('TEST_SELF_EMAIL')
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
# -------------------------------------------

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
            endpoint = f"{GRAPH_ROOT}/me/sendMail"
            payload = {"message": message, "saveToSentItems": True}
            r = requests.post(endpoint, headers=headers, json=payload)
        else:
            endpoint = f"{GRAPH_ROOT}/me/messages"
            r = requests.post(endpoint, headers=headers, json=message)
        if r.status_code in (200, 201, 202): return True, "Success"
        return False, f"{r.status_code}: {r.text}"

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

class MailerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.df, self.access_token, self.thread, self.worker = None, None, None, None
        self.is_formal_send = False
        self.personalized_attachment_folder = None
        self.personalized_attachments_map = {}
        self.token_cache = msal.SerializableTokenCache()
        if os.path.exists(TOKEN_CACHE_FILE):
            try:
                with open(TOKEN_CACHE_FILE, "r", encoding="utf-8") as f: self.token_cache.deserialize(f.read())
            except Exception as e: print("加载 token 缓存失败:", e)
        atexit.register(self._save_token_cache)
        self.msal_app = msal.PublicClientApplication(
            CLIENT_ID, authority=f"https://login.microsoftonline.com/{TENANT_ID}",
            token_cache=self.token_cache
        )
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle('个性化邮件发送助手')
        self.setGeometry(100, 100, 800, 950)
        main = QVBoxLayout(self)

        self.progress = QProgressBar(); self.progress.setVisible(False); self.progress.setTextVisible(False)
        main.addWidget(self.progress)

        top = QHBoxLayout(); self.excel_label = QLabel("尚未加载Excel文件")
        load_btn = QPushButton("1. 加载Excel..."); load_btn.clicked.connect(self.load_excel)
        top.addWidget(load_btn); top.addWidget(self.excel_label, 1)
        main.addLayout(top); main.addWidget(self._sep())

        form = QVBoxLayout(); form.setSpacing(10)
        
        form.addWidget(QLabel("<b>2. 核心信息列</b>"))
        name_email_layout = QHBoxLayout()
        self.name_combo = QComboBox(); self.email_combo = QComboBox()
        name_email_layout.addWidget(QLabel("姓名列:"))
        name_email_layout.addWidget(self.name_combo, 1)
        name_email_layout.addWidget(QLabel("邮箱列:"))
        name_email_layout.addWidget(self.email_combo, 1)
        form.addLayout(name_email_layout)

        form.addWidget(self._sep())
        form.addWidget(QLabel("<b>3. 筛选收件人 (选填)</b>"))
        self.filters = []
        for i in range(3):
            filter_layout = QHBoxLayout()
            col_combo = QComboBox(); col_combo.addItem("【不筛选】")
            val_input = QLineEdit(); val_input.setPlaceholderText("在此输入筛选值")
            filter_layout.addWidget(QLabel(f"筛选条件 {i+1}:"))
            filter_layout.addWidget(col_combo, 1)
            filter_layout.addWidget(QLabel("值为"))
            filter_layout.addWidget(val_input, 1)
            form.addLayout(filter_layout)
            self.filters.append((col_combo, val_input))
            col_combo.currentIndexChanged.connect(self.update_filtered_count)
            val_input.textChanged.connect(self.update_filtered_count)
        self.filtered_count_label = QLabel("筛选后将发送给: <b>...</b> 人")
        form.addWidget(self.filtered_count_label, 0, Qt.AlignmentFlag.AlignRight)

        form.addWidget(self._sep())
        form.addWidget(QLabel("<b>4. 邮件内容</b>"))
        form.addWidget(QLabel("邮件主题:"))
        self.subject_input = QLineEdit(); self.subject_input.setFont(QFont("Arial", 12))
        form.addWidget(self.subject_input)
        form.addWidget(QLabel("邮件正文:"))
        
        self.body_editor = QTextEdit(); self.body_editor.setFont(QFont("Arial", 12))
        self.body_editor.setPlaceholderText("例如：尊敬的 {{姓名}} 专家，您好！")
        self.body_editor.cursorPositionChanged.connect(self._sync_toolbar_state)
        
        self.toolbar_layout = QHBoxLayout()
        self._build_toolbar()
        form.addLayout(self.toolbar_layout)
        
        form.addWidget(self.body_editor)

        main.addLayout(form); main.addWidget(self._sep())
        attachments_layout = QHBoxLayout()
        pa_vbox = QVBoxLayout(); pa_vbox.addWidget(QLabel("<b>5. 个性化附件 (按姓名匹配)</b>")); self.pa_folder_label = QLabel("<i>尚未选择文件夹</i>"); pa_vbox.addWidget(self.pa_folder_label); pa_btn_layout = QHBoxLayout(); select_pa_folder_btn = QPushButton("选择文件夹..."); preview_pa_btn = QPushButton("预览匹配结果"); select_pa_folder_btn.clicked.connect(self.select_personalized_folder); preview_pa_btn.clicked.connect(self.preview_matches); pa_btn_layout.addWidget(select_pa_folder_btn); pa_btn_layout.addWidget(preview_pa_btn); pa_btn_layout.addStretch(); pa_vbox.addLayout(pa_btn_layout); attachments_layout.addLayout(pa_vbox)
        attachments_layout.addWidget(self._vert_sep()); ca_vbox = QVBoxLayout(); ca_vbox.addWidget(QLabel("<b>6. 通用附件 (发送给所有人)</b>")); self.att_list = QListWidget(); self.att_list.setFixedHeight(60); ca_vbox.addWidget(self.att_list); ca_btn_layout = QHBoxLayout(); add_att_btn = QPushButton("添加..."); rm_att_btn = QPushButton("移除"); add_att_btn.clicked.connect(self.add_common_attachment); rm_att_btn.clicked.connect(self.remove_common_attachment); ca_btn_layout.addWidget(add_att_btn); ca_btn_layout.addWidget(rm_att_btn); ca_btn_layout.addStretch(); ca_vbox.addLayout(ca_btn_layout); attachments_layout.addLayout(ca_vbox)
        main.addLayout(attachments_layout); main.addWidget(self._sep())
        btn_bar = QHBoxLayout(); self.draft_btn = QPushButton("内部测试(草稿)"); self.test_btn = QPushButton("内部测试(发给自己)"); self.send_btn = QPushButton("!!! 正式发送 !!!"); self.draft_btn.setStyleSheet("background:#DAA520;color:white;border-radius:5px;padding:5px;"); self.test_btn.setStyleSheet("background:#4682B4;color:white;border-radius:5px;padding:5px;"); self.send_btn.setStyleSheet("background:#B22222;color:white;font-weight:bold;border-radius:5px;padding:5px;"); self.draft_btn.clicked.connect(lambda: self.run_process('SAVE_DRAFT', True)); self.test_btn.clicked.connect(lambda: self.run_process('SEND', True)); self.send_btn.clicked.connect(lambda: self.run_process('SEND', False)); btn_bar.addStretch(); btn_bar.addWidget(self.draft_btn); btn_bar.addWidget(self.test_btn); btn_bar.addWidget(self.send_btn); btn_bar.addStretch(); main.addLayout(btn_bar)

    def _build_toolbar(self):
        paste_text_btn = QPushButton("粘贴纯文本"); paste_text_btn.setToolTip("从剪贴板粘贴纯文本，清除所有格式"); paste_text_btn.clicked.connect(self.paste_as_plain_text)
        self.act_bold = QPushButton("B"); self.act_bold.setCheckable(True); font=self.act_bold.font();font.setBold(True);self.act_bold.setFont(font)
        self.act_italic = QPushButton("I"); self.act_italic.setCheckable(True); font=self.act_italic.font();font.setItalic(True);self.act_italic.setFont(font)
        self.act_under = QPushButton("U"); self.act_under.setCheckable(True); font=self.act_under.font();font.setUnderline(True);self.act_under.setFont(font)
        self.act_bullet = QPushButton("•"); self.act_bullet.setToolTip("项目符号列表")
        self.font_combo = QComboBox(); self.font_combo.addItems(QFontDatabase.families())
        self.size_combo = QComboBox(); self.size_combo.addItems([str(s) for s in [8, 9, 10, 11, 12, 14, 16, 18, 24, 36, 48]]); self.size_combo.setCurrentText("12")
        color_btn = QPushButton("颜色"); color_btn.clicked.connect(self.set_text_color)
        
        # Bug修复1: 让所有按钮在点击后保持焦点在编辑器
        paste_text_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.act_bold.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.act_italic.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.act_under.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.act_bullet.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        color_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        # Bug修复2: 改变字体和字号的连接方式，只在有选中文本时才应用
        self.font_combo.currentTextChanged.connect(self.set_selection_font_family)
        self.size_combo.currentTextChanged.connect(self.set_selection_font_size)
        
        # Bug修复3: 修正加粗、斜体、下划线的行为
        self.act_bold.toggled.connect(self.toggle_bold)
        self.act_italic.toggled.connect(self.toggle_italic)
        self.act_under.toggled.connect(self.toggle_underline)

        self.act_bullet.clicked.connect(self._insert_bullet)
        
        for btn in [paste_text_btn, self.act_bold, self.act_italic, self.act_under, self.act_bullet]:
            btn.setFixedWidth(100); self.toolbar_layout.addWidget(btn)
        self.toolbar_layout.addSpacing(10)
        self.toolbar_layout.addWidget(self.font_combo, 1); self.toolbar_layout.addWidget(self.size_combo); self.toolbar_layout.addWidget(color_btn)
        self.toolbar_layout.addStretch()

    # Bug修复：新增三个方法处理格式切换，确保焦点不丢失
    def toggle_bold(self, checked):
        self.body_editor.setFocus()  # 确保焦点回到编辑器
        if self.body_editor.textCursor().hasSelection():
            # 如果有选中文本，应用到选中部分
            char_format = QTextCharFormat()
            char_format.setFontWeight(QFont.Bold if checked else QFont.Normal)
            self.body_editor.textCursor().mergeCharFormat(char_format)
        else:
            # 如果没有选中文本，只影响后续输入
            self.body_editor.setFontWeight(QFont.Bold if checked else QFont.Normal)
    
    def toggle_italic(self, checked):
        self.body_editor.setFocus()
        if self.body_editor.textCursor().hasSelection():
            char_format = QTextCharFormat()
            char_format.setFontItalic(checked)
            self.body_editor.textCursor().mergeCharFormat(char_format)
        else:
            self.body_editor.setFontItalic(checked)
    
    def toggle_underline(self, checked):
        self.body_editor.setFocus()
        if self.body_editor.textCursor().hasSelection():
            char_format = QTextCharFormat()
            char_format.setFontUnderline(checked)
            self.body_editor.textCursor().mergeCharFormat(char_format)
        else:
            self.body_editor.setFontUnderline(checked)

    # Bug修复：修改字体和字号方法，只在有选中文本时才应用
    def set_selection_font_family(self, family):
        cursor = self.body_editor.textCursor()
        if cursor.hasSelection():
            # 只有选中文本时才应用到选中部分
            char_format = QTextCharFormat()
            char_format.setFontFamilies([family])
            cursor.mergeCharFormat(char_format)
        # 无论如何都设置当前字体，影响后续输入
        self.body_editor.setFontFamily(family)

    def set_selection_font_size(self, size_str):
        if not size_str or not size_str.isdigit(): return
        cursor = self.body_editor.textCursor()
        if cursor.hasSelection():
            # 只有选中文本时才应用到选中部分
            char_format = QTextCharFormat()
            char_format.setFontPointSize(float(size_str))
            cursor.mergeCharFormat(char_format)
        # 无论如何都设置当前字号，影响后续输入
        self.body_editor.setFontPointSize(float(size_str))

    def set_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            cursor = self.body_editor.textCursor()
            if cursor.hasSelection():
                char_format = QTextCharFormat()
                char_format.setForeground(color)
                cursor.mergeCharFormat(char_format)
            else:
                # 设置后续输入的颜色
                self.body_editor.setTextColor(color)
    
    def paste_as_plain_text(self):
        self.body_editor.insertPlainText(QGuiApplication.clipboard().text())

    def _sync_toolbar_state(self):
        # 同步工具栏状态，但要避免触发信号
        self.act_bold.blockSignals(True)
        self.act_italic.blockSignals(True)
        self.act_under.blockSignals(True)
        self.font_combo.blockSignals(True)
        self.size_combo.blockSignals(True)
        
        self.act_bold.setChecked(self.body_editor.fontWeight() > QFont.Normal)
        self.act_italic.setChecked(self.body_editor.fontItalic())
        self.act_under.setChecked(self.body_editor.fontUnderline())
        self.font_combo.setCurrentText(self.body_editor.fontFamily())
        self.size_combo.setCurrentText(str(int(self.body_editor.fontPointSize())))
        
        self.act_bold.blockSignals(False)
        self.act_italic.blockSignals(False)
        self.act_under.blockSignals(False)
        self.font_combo.blockSignals(False)
        self.size_combo.blockSignals(False)
    
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
        if df is not None: self.filtered_count_label.setText(f"筛选后将发送给: <b>{len(df)}</b> 人")

    def run_process(self, action: str, test_mode: bool):
        if self.df is None: QMessageBox.warning(self, "提示", "请先加载Excel文件。"); return
        filtered_df = self.get_filtered_df()
        if filtered_df is None: return
        if filtered_df.empty: QMessageBox.warning(self, "提示", "筛选后没有符合条件的收件人。"); return
        if not self._ensure_token(): return
        email_col = self.email_combo.currentText(); name_col = self.name_combo.currentText(); subj_tpl = self.subject_input.text(); body_tpl = self.body_editor.toHtml()
        if not all([email_col, name_col, subj_tpl, self.body_editor.toPlainText().strip()]): QMessageBox.warning(self, "提示", "请完善所有必填项（邮箱列、姓名列、主题、正文）。"); return
        if (test_mode and action == "SEND"):
            if QMessageBox.question(self, "测试确认", f"全部发送到测试邮箱 {TEST_SELF_EMAIL}？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.No: return
        if not test_mode:
            if QMessageBox.question(self, "正式群发确认", f"将向筛选后的 {len(filtered_df)} 位联系人正式发送邮件，确定继续？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.No: return
        self.is_formal_send = not test_mode
        if self.personalized_attachment_folder: self.match_and_verify_attachments(show_dialog=False)
        common_attachments = [self.att_list.item(i).text() for i in range(self.att_list.count())]
        self._lock_ui(True); self.progress.setMaximum(len(filtered_df)); self.progress.setValue(0); self.progress.setVisible(True)
        self.thread = QThread()
        self.worker = MailWorker(self.access_token, filtered_df, email_col, name_col, subj_tpl, body_tpl, common_attachments, self.personalized_attachments_map, action, test_mode)
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
        """任务结束后，彻底重置界面状态和内部数据"""
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
        print("界面已彻底重置，准备下一个任务。")
        
    def _end_thread(self):
        if self.thread: self.thread.quit(); self.thread.wait()
        if self.worker: self.worker.deleteLater()
        self.thread=self.worker=None; self
        
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

    def _save_token_cache(self):
        if self.token_cache.has_state_changed:
            with open(TOKEN_CACHE_FILE, "w", encoding="utf-8") as f: f.write(self.token_cache.serialize())

    def _ensure_token(self):
        if self.access_token: return True
        acct = self.msal_app.get_accounts()
        result = self.msal_app.acquire_token_silent(SCOPES, account=acct[0]) if acct else None
        if not result:
            flow = self.msal_app.initiate_device_flow(scopes=SCOPES)
            if "user_code" not in flow: QMessageBox.critical(self, "认证错误", flow.get('error_description', '未知错误')); return False
            AuthDialog(flow["user_code"], flow["verification_uri"], self).exec()
            result = self.msal_app.acquire_token_by_device_flow(flow)
        if "access_token" in result: self.access_token = result["access_token"]; return True
        QMessageBox.critical(self, "认证失败", json.dumps(result, ensure_ascii=False, indent=2)); return False

    def _insert_bullet(self):
        self.body_editor.textCursor().insertList(QTextListFormat.ListDisc)

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
        if self.df is None:
            if show_dialog: QMessageBox.warning(self, "提示", "请先加载Excel文件。"); return
            return
        name_col = self.name_combo.currentText()
        if not name_col:
            if show_dialog: QMessageBox.warning(self, "提示", "请先选择包含“专家姓名”的列。"); return
            return
        self.personalized_attachments_map = {}; expert_names = self.df[name_col].unique()
        for name in expert_names:
            if not name: continue
            self.personalized_attachments_map[name] = [os.path.join(self.personalized_attachment_folder, f) for f in os.listdir(self.personalized_attachment_folder) if name in f]
        if show_dialog:
            dialog = VerificationDialog(self.personalized_attachments_map, self); dialog.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    app.setStyle("Fusion")
    dark_palette = QPalette(); dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53)); dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white); dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25)); dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53)); dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white); dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white); dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white); dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53)); dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white); dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red); dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218)); dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218)); dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black); app.setPalette(dark_palette); app.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; } QWidget { font-size: 13px; }")
    
    gui = MailerApp()
    gui.show()
    sys.exit(app.exec())