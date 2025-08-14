import os
import json
import time
import msal
from PySide6.QtWidgets import QMessageBox
from src.ui.dialogs import AuthDialog

TOKEN_CACHE_FILE = "token_cache.json"
SCOPES = ["Mail.Send", "Mail.ReadWrite", "User.Read", "User.Read.All", "GroupMember.Read.All", "Group.Read.All"]

def _save_token_cache(cache):
    if cache.has_state_changed:
        with open(TOKEN_CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(cache.serialize())

def ensure_token(app_instance):
    if app_instance.access_token:
        return True
    
    accounts = app_instance.msal_app.get_accounts()
    result = app_instance.msal_app.acquire_token_silent(SCOPES, account=accounts[0]) if accounts else None
    
    if not result:
        flow = app_instance.msal_app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            QMessageBox.critical(app_instance, "认证错误", flow.get('error_description', '未知错误'))
            return False
        
        dialog = AuthDialog(flow["user_code"], flow["verification_uri"], app_instance)
        dialog.exec()
        
        result = app_instance.msal_app.acquire_token_by_device_flow(flow)
        
    if "access_token" in result:
        app_instance.access_token = result["access_token"]
        return True
        
    QMessageBox.critical(app_instance, "认证失败", json.dumps(result, ensure_ascii=False, indent=2))
    return False