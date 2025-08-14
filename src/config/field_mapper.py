import json
import os
from typing import Dict, List, Any

class FieldMapper:
    """Manages field mapping configuration between data sources and template variables"""
    
    def __init__(self, config_file="field_mapping_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return self.get_default_config()
    
    def get_default_config(self) -> Dict:
        """Get default configuration"""
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
    
    def save_config(self) -> bool:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except:
            return False
    
    def map_group_field(self, api_field: str, group_data: Dict) -> Any:
        """Map a group API field to template variable value"""
        mappings = self.config["mappings"]["group"]["field_mappings"]
        
        # Find template variable for this API field
        for template_var, field in mappings.items():
            if field == api_field:
                return group_data.get(api_field, f"[{template_var}]")
        
        return group_data.get(api_field, "")
    
    def map_member_field(self, api_field: str, member_data: Dict) -> Any:
        """Map a member API field to template variable value"""
        mappings = self.config["mappings"]["members"]["field_mappings"]
        
        # Find template variable for this API field
        for template_var, field in mappings.items():
            if field == api_field:
                return member_data.get(api_field, f"[{template_var}]")
        
        return member_data.get(api_field, "")
    
    def get_template_variables_for_source(self, source: str) -> List[str]:
        """Get template variables available for a specific data source"""
        if source == "excel":
            # Excel columns are auto-detected
            return self.config["template_variables"]
        elif source == "group":
            return list(self.config["mappings"]["group"]["field_mappings"].keys())
        elif source == "members":
            return list(self.config["mappings"]["members"]["field_mappings"].keys())
        else:
            return self.config["template_variables"]
    
    def map_data_to_template_vars(self, data: Dict, source: str) -> Dict:
        """Map raw data to template variables based on source type"""
        result = {}
        
        if source == "group":
            mappings = self.config["mappings"]["group"]["field_mappings"]
            for template_var, api_field in mappings.items():
                result[template_var] = data.get(api_field, f"[{template_var}]")
                
        elif source == "members":
            mappings = self.config["mappings"]["members"]["field_mappings"]
            for template_var, api_field in mappings.items():
                if api_field == "_memberType":
                    # Special handling for member type
                    result[template_var] = data.get('member_type', '成员')
                else:
                    result[template_var] = data.get(api_field, f"[{template_var}]")
                    
        elif source == "excel":
            # For Excel, columns map directly
            result = data.copy()
        
        return result