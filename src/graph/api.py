import requests
from PySide6.QtWidgets import QMessageBox

GRAPH_ROOT = "https://graph.microsoft.com/v1.0"

def fetch_user_groups(app_instance):
    """获取用户所属的Microsoft 365群组"""
    if not app_instance.access_token:
        return False
    
    try:
        headers = {"Authorization": f"Bearer {app_instance.access_token}"}
        endpoint = f"{GRAPH_ROOT}/me/memberOf/microsoft.graph.group?$select=id,displayName,mail,mailNickname"
        response = requests.get(endpoint, headers=headers)
        
        if response.status_code == 200:
            groups_data = response.json()
            app_instance.user_groups = []
            for group in groups_data.get('value', []):
                if group.get('mail'):
                    app_instance.user_groups.append({
                        'id': group['id'],
                        'displayName': group['displayName'],
                        'mail': group['mail'],
                        'mailNickname': group.get('mailNickname', '')
                    })
            return True
        else:
            QMessageBox.critical(app_instance, "获取群组失败", f"无法获取群组信息: {response.status_code}\n{response.text}")
            return False
    except Exception as e:
        QMessageBox.critical(app_instance, "错误", f"获取群组时发生错误:\n{e}")
        return False

def fetch_group_members(app_instance, group_id):
    """获取指定群组的成员列表"""
    if not app_instance.access_token:
        return []
    
    try:
        headers = {"Authorization": f"Bearer {app_instance.access_token}"}
        endpoint = f"{GRAPH_ROOT}/groups/{group_id}/members"
        response = requests.get(endpoint, headers=headers)
        
        if response.status_code == 200:
            members_data = response.json()
            members = []
            
            for member in members_data.get('value', []):
                member_id = member['id']
                display_name = member.get('displayName')
                email = member.get('mail') or member.get('userPrincipalName')

                if not display_name or not email:
                    user_details = fetch_user_details(app_instance, member_id)
                    if user_details:
                        display_name = user_details.get('displayName') or f"User-{member_id[:8]}"
                        email = user_details.get('mail') or user_details.get('userPrincipalName')

                if email:
                    members.append({
                        'id': member_id,
                        'displayName': display_name,
                        'email': email
                    })
            
            return members
        else:
            error_text = response.text
            QMessageBox.warning(app_instance, "获取成员失败", f"无法获取群组成员: {response.status_code}\n{error_text}")
            return []
    except Exception as e:
        QMessageBox.critical(app_instance, "错误", f"获取群组成员时发生错误:\n{e}")
        return []

def fetch_user_details(app_instance, user_id):
    """获取单个用户的详细信息"""
    try:
        headers = {"Authorization": f"Bearer {app_instance.access_token}"}
        endpoint = f"{GRAPH_ROOT}/users/{user_id}?$select=id,displayName,mail,userPrincipalName"
        response = requests.get(endpoint, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Debug: Error getting user details for {user_id}: {e}")
        return None
