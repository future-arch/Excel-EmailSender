import json
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, 
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, 
    QComboBox, QMessageBox, QGroupBox, QScrollArea,
    QHeaderView, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal

class FieldConfigDialog(QDialog):
    """Dialog for configuring field mappings between data sources and template variables"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.config_file = "field_mapping_config.json"
        self.config = self.load_config()
        self.setup_ui()
        
    def load_config(self):
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # Default configuration
        return {
            "version": "1.0",
            "mappings": {
                "excel": {
                    "enabled": True,
                    "auto_detect": True,
                    "column_mappings": {}
                },
                "group": {
                    "enabled": True,
                    "available_fields": {
                        "id": "群组 ID",
                        "displayName": "群组名称", 
                        "description": "群组描述",
                        "mail": "群组邮箱",
                        "mailNickname": "群组邮箱别名",
                        "createdDateTime": "创建日期",
                        "visibility": "可见性"
                    },
                    "field_mappings": {
                        "群组名称": "displayName",
                        "群组描述": "description", 
                        "群组邮箱": "mail"
                    }
                },
                "members": {
                    "enabled": True,
                    "available_fields": {
                        "id": "用户 ID",
                        "displayName": "显示名称",
                        "givenName": "名字",
                        "surname": "姓氏", 
                        "mail": "邮箱地址",
                        "jobTitle": "职位",
                        "department": "部门",
                        "companyName": "公司",
                        "businessPhones": "办公电话",
                        "mobilePhone": "手机",
                        "officeLocation": "办公地点",
                        "employeeId": "员工 ID",
                        "employeeType": "员工类型",
                        "userPrincipalName": "用户主体名称"
                    },
                    "field_mappings": {
                        "姓名": "displayName",
                        "邮箱": "mail",
                        "职位": "jobTitle",
                        "部门": "department",
                        "成员类型": "_memberType"
                    }
                }
            },
            "template_variables": [
                "姓名", "邮箱", "群组名称", "群组描述", "群组邮箱", 
                "成员类型", "部门", "职位", "当前日期", "当前时间", "年份", "月份"
            ]
        }
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败: {e}")
            return False
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("字段映射配置")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Description
        desc_label = QLabel(
            "配置数据源字段与邮件模板变量之间的映射关系。\n"
            "Excel 标签页会自动检测列名，群组标签页使用 Microsoft Graph API 字段。"
        )
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Tab widget for different data sources
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_excel_tab()
        self._create_group_tab()
        self._create_members_tab()
        self._create_variables_tab()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_and_close)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _create_excel_tab(self):
        """Create Excel configuration tab"""
        excel_widget = QWidget()
        layout = QVBoxLayout(excel_widget)
        
        # Description
        desc = QLabel(
            "Excel 文件的列名会自动检测。当您加载 Excel 文件时，\n"
            "所有列名都会自动添加为可用的模板变量。"
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Current Excel columns (if loaded)
        if hasattr(self.parent_window, 'df') and self.parent_window.df is not None:
            columns_group = QGroupBox("当前 Excel 文件的列")
            columns_layout = QVBoxLayout(columns_group)
            
            columns_list = QListWidget()
            for col in self.parent_window.df.columns:
                columns_list.addItem(f"{{{{{col}}}}}")
            columns_layout.addWidget(columns_list)
            
            layout.addWidget(columns_group)
        else:
            info_label = QLabel("请先加载 Excel 文件以查看可用列。")
            info_label.setStyleSheet("color: gray; font-style: italic;")
            layout.addWidget(info_label)
        
        layout.addStretch()
        self.tab_widget.addTab(excel_widget, "Excel 数据源")
    
    def _create_group_tab(self):
        """Create group configuration tab"""
        group_widget = QWidget()
        layout = QVBoxLayout(group_widget)
        
        desc = QLabel("配置 Microsoft 365 群组字段与模板变量的映射关系。")
        layout.addWidget(desc)
        
        # Mapping table
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["API 字段", "→", "模板变量"])
        table.horizontalHeader().setStretchLastSection(True)
        
        # Add current mappings
        mappings = self.config["mappings"]["group"]["field_mappings"]
        available_fields = self.config["mappings"]["group"]["available_fields"]
        template_variables = self.config["template_variables"]
        
        # Create reverse mapping for display (API field -> template variable)
        reverse_mappings = {}
        for template_var, api_field in mappings.items():
            reverse_mappings[api_field] = template_var
        
        table.setRowCount(len(available_fields))
        row = 0
        for api_field, description in available_fields.items():
            # API field (fixed)
            api_item = QTableWidgetItem(f"{api_field}\n({description})")
            api_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Read-only
            table.setItem(row, 0, api_item)
            
            # Arrow
            arrow_item = QTableWidgetItem("→")
            arrow_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            arrow_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            table.setItem(row, 1, arrow_item)
            
            # Template variable combo box (selectable)
            combo = QComboBox()
            combo.addItem("【不映射】")  # Option to not map
            combo.addItems(template_variables)
            
            # Set current selection
            current_template_var = reverse_mappings.get(api_field, "")
            if current_template_var:
                combo.setCurrentText(current_template_var)
            else:
                combo.setCurrentText("【不映射】")
                
            combo.currentTextChanged.connect(
                lambda text, field=api_field: self.update_group_mapping_reverse(field, text)
            )
            table.setCellWidget(row, 2, combo)
            
            row += 1
        
        layout.addWidget(table)
        
        # Note about API fields
        note_label = QLabel("注意：API 字段由 Microsoft 定义，无法修改。您只能选择映射到哪个模板变量。")
        note_label.setStyleSheet("color: #666; font-style: italic; font-size: 12px;")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)
        
        self.group_table = table
        self.tab_widget.addTab(group_widget, "群组字段")
    
    def _create_members_tab(self):
        """Create members configuration tab"""
        members_widget = QWidget()
        layout = QVBoxLayout(members_widget)
        
        desc = QLabel("配置 Microsoft 365 群组成员字段与模板变量的映射关系。")
        layout.addWidget(desc)
        
        # Mapping table
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["API 字段", "→", "模板变量"])
        table.horizontalHeader().setStretchLastSection(True)
        
        # Add current mappings
        mappings = self.config["mappings"]["members"]["field_mappings"]
        available_fields = self.config["mappings"]["members"]["available_fields"]
        template_variables = self.config["template_variables"]
        
        # Create reverse mapping for display (API field -> template variable)
        reverse_mappings = {}
        for template_var, api_field in mappings.items():
            reverse_mappings[api_field] = template_var
        
        table.setRowCount(len(available_fields))
        row = 0
        for api_field, description in available_fields.items():
            # API field (fixed)
            api_item = QTableWidgetItem(f"{api_field}\n({description})")
            api_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Read-only
            table.setItem(row, 0, api_item)
            
            # Arrow
            arrow_item = QTableWidgetItem("→")
            arrow_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            arrow_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            table.setItem(row, 1, arrow_item)
            
            # Template variable combo box (selectable)
            combo = QComboBox()
            combo.addItem("【不映射】")  # Option to not map
            combo.addItems(template_variables)
            
            # Set current selection
            current_template_var = reverse_mappings.get(api_field, "")
            if current_template_var:
                combo.setCurrentText(current_template_var)
            else:
                combo.setCurrentText("【不映射】")
                
            combo.currentTextChanged.connect(
                lambda text, field=api_field: self.update_member_mapping_reverse(field, text)
            )
            table.setCellWidget(row, 2, combo)
            
            row += 1
        
        layout.addWidget(table)
        
        # Note about API fields
        note_label = QLabel("注意：API 字段由 Microsoft 定义，无法修改。您只能选择映射到哪个模板变量。")
        note_label.setStyleSheet("color: #666; font-style: italic; font-size: 12px;")
        note_label.setWordWrap(True)
        layout.addWidget(note_label)
        
        self.members_table = table
        self.tab_widget.addTab(members_widget, "成员字段")
    
    def _create_variables_tab(self):
        """Create template variables overview tab"""
        variables_widget = QWidget()
        layout = QVBoxLayout(variables_widget)
        
        desc = QLabel(
            "这些是您可以在邮件模板中使用的所有变量。\n"
            "在邮件内容中使用 {{变量名}} 格式来插入变量。"
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Variables list
        variables_group = QGroupBox("可用的模板变量")
        variables_layout = QVBoxLayout(variables_group)
        
        variables_list = QListWidget()
        for var in self.config["template_variables"]:
            variables_list.addItem(f"{{{{{var}}}}}")
        
        variables_layout.addWidget(variables_list)
        layout.addWidget(variables_group)
        
        # Add new variable
        add_layout = QHBoxLayout()
        add_layout.addWidget(QLabel("添加新变量:"))
        self.new_var_input = QLineEdit()
        add_layout.addWidget(self.new_var_input)
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(lambda: self.add_template_variable(variables_list))
        add_layout.addWidget(add_btn)
        
        layout.addLayout(add_layout)
        
        self.tab_widget.addTab(variables_widget, "模板变量")
    
    def update_group_mapping_reverse(self, api_field, template_var):
        """Update group field mapping (API field -> template variable)"""
        # Remove old mapping for this API field
        mappings = self.config["mappings"]["group"]["field_mappings"]
        old_template_var = None
        for tvar, afield in list(mappings.items()):
            if afield == api_field:
                old_template_var = tvar
                del mappings[tvar]
                break
        
        # Add new mapping if not "不映射"
        if template_var != "【不映射】":
            mappings[template_var] = api_field
    
    def update_member_mapping_reverse(self, api_field, template_var):
        """Update member field mapping (API field -> template variable)"""
        # Remove old mapping for this API field
        mappings = self.config["mappings"]["members"]["field_mappings"]
        old_template_var = None
        for tvar, afield in list(mappings.items()):
            if afield == api_field:
                old_template_var = tvar
                del mappings[tvar]
                break
        
        # Add new mapping if not "不映射"
        if template_var != "【不映射】":
            mappings[template_var] = api_field
    
    
    def add_template_variable(self, list_widget):
        """Add new template variable"""
        var_name = self.new_var_input.text().strip()
        if var_name and var_name not in self.config["template_variables"]:
            self.config["template_variables"].append(var_name)
            list_widget.addItem(f"{{{{{var_name}}}}}")
            self.new_var_input.clear()
    
    def save_and_close(self):
        """Save configuration and close dialog"""
        if self.save_config():
            QMessageBox.information(self, "成功", "配置已保存。")
            self.accept()

# Import QLineEdit if not already imported
from PySide6.QtWidgets import QLineEdit