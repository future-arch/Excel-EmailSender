# SmartEmailSender 自动更新系统指南

本指南详细说明如何使用SmartEmailSender的自动更新系统，让用户无需重新下载完整安装包即可更新到最新版本。

## 🎯 系统特点

### 📦 两种更新方式
1. **增量更新** - 只下载修改的文件（通常5-20MB）
2. **完整更新** - 下载完整更新包（通常50-100MB）

### 🛡️ 安全机制
- 文件完整性校验（SHA256）
- 自动备份当前版本
- 更新失败时自动回滚
- 支持跳过特定版本

### 🌐 多镜像支持
- 自动选择最快的下载源
- 国内外CDN智能切换
- 下载失败时自动重试

## 📋 使用方法

### 用户端使用

#### 1. 自动检查更新
应用启动时会自动检查更新（可在设置中关闭）

#### 2. 手动检查更新
```python
# 在主应用中集成
from update_dialog import check_for_updates_with_ui

# 在菜单中添加"检查更新"选项
def check_updates_manually():
    check_for_updates_with_ui(self, silent=False)
```

#### 3. 更新流程
1. 检测到新版本时显示更新对话框
2. 用户选择"立即更新"
3. 自动下载增量更新包（如果可用）
4. 应用更新并自动重启

### 开发者端管理

#### 1. 准备新版本
```bash
# 修改代码后，更新版本号
vim version.json
# 更改版本为 1.1.0

# 测试新版本
python src/SmartEmailSender.py
```

#### 2. 生成更新包
```bash
# 生成从1.0.0到1.1.0的更新包
python create_update_package.py \
  --old-version 1.0.0 \
  --new-version 1.1.0 \
  --changelog "修复邮件发送bug，新增历史记录功能"

# 输出文件:
# updates/update_1.0.0_to_1.1.0_incremental.zip (5MB)
# updates/update_1.1.0_full.zip (50MB)
# updates/update_info.json (版本信息)
```

#### 3. 上传到CDN
```bash
# 上传到Gitee (示例)
gh release create v1.1.0 \
  --title "SmartEmailSender v1.1.0" \
  --notes-file CHANGELOG.md \
  updates/update_1.0.0_to_1.1.0_incremental.zip \
  updates/update_1.1.0_full.zip

# 上传版本信息到服务器
scp updates/update_info.json user@server:/path/to/cdn/
```

## 🔧 集成到主应用

### 1. 在主窗口中添加更新检查

```python
# 在主窗口类中添加
from update_dialog import check_for_updates_with_ui
from updater import UpdateManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        # 启动时检查更新
        QTimer.singleShot(3000, self.check_updates_on_startup)
        
    def setup_ui(self):
        # ... 其他UI设置 ...
        
        # 添加更新菜单
        help_menu = self.menuBar().addMenu("帮助")
        
        update_action = QAction("检查更新", self)
        update_action.triggered.connect(self.check_updates_manually)
        help_menu.addAction(update_action)
        
    def check_updates_on_startup(self):
        """启动时检查更新（静默）"""
        check_for_updates_with_ui(self, silent=True)
        
    def check_updates_manually(self):
        """手动检查更新"""
        check_for_updates_with_ui(self, silent=False)
```

### 2. 添加版本信息显示

```python
# 在关于对话框中显示版本信息
from updater import UpdateManager

def show_about_dialog(self):
    update_manager = UpdateManager()
    version = str(update_manager.current_version)
    
    QMessageBox.about(self, "关于", f"""
    SmartEmailSender v{version}
    
    智能邮件发送工具
    支持批量发送、模板编辑、群组管理
    
    © 2024 Your Company
    """)
```

## 📊 更新包结构

### 增量更新包结构
```
update_1.0.0_to_1.1.0_incremental.zip
├── update_manifest.json    # 更新清单
├── SmartEmailSender.py     # 修改的文件
├── src/
│   ├── new_feature.py      # 新增的文件
│   └── updater.py          # 修改的文件
└── templates/
    └── new_template.html   # 新增的模板
```

### 更新清单格式
```json
{
  "from_version": "1.0.0",
  "to_version": "1.1.0",
  "created_at": "2024-08-15T10:30:00Z",
  "type": "incremental",
  "updates": [
    {
      "action": "add",
      "path": "src/new_feature.py",
      "size": 5120,
      "hash": "sha256_hash_here"
    },
    {
      "action": "update",
      "path": "SmartEmailSender.py",
      "size": 15360,
      "hash": "sha256_hash_here"
    },
    {
      "action": "delete",
      "path": "src/deprecated.py"
    }
  ]
}
```

## 🚀 发布流程

### 开发阶段
1. 开发新功能或修复bug
2. 更新 `version.json` 中的版本号
3. 测试新版本功能
4. 编写更新日志

### 发布准备
```bash
# 1. 生成更新包
python create_update_package.py --old-version 1.0.0 --new-version 1.1.0 \
  --changelog "$(cat CHANGELOG_1.1.0.md)"

# 2. 验证更新包
unzip -l updates/update_1.1.0_full.zip
cat updates/update_info.json

# 3. 测试更新流程
python test_update.py
```

### CDN部署
```bash
# 上传到多个CDN确保可用性

# Gitee
gh release create v1.1.0 updates/*.zip

# 阿里云OSS
ossutil cp updates/update_info.json oss://smartemailsender/updates/
ossutil cp updates/*.zip oss://smartemailsender/updates/v1.1.0/

# 腾讯云COS
coscmd upload updates/update_info.json updates/info.json
coscmd upload updates/*.zip updates/v1.1.0/
```

### 发布验证
1. 测试国内外网络环境下的更新
2. 验证增量更新和完整更新都正常
3. 确认更新后应用正常运行
4. 检查回滚机制是否工作

## 🔍 故障排除

### 常见问题

#### 1. 更新下载失败
- **原因**: 网络问题或CDN不可用
- **解决**: 系统会自动尝试其他CDN源

#### 2. 更新应用失败
- **原因**: 文件权限不足或文件被占用
- **解决**: 系统会自动回滚到原版本

#### 3. 更新后无法启动
- **原因**: 更新包有问题或依赖缺失
- **解决**: 手动恢复备份或重新安装

### 日志位置
```bash
# 更新日志位置
~/.smartemailsender/logs/update.log

# 查看最新日志
tail -f ~/.smartemailsender/logs/update.log
```

### 手动回滚
```bash
# 如果自动回滚失败，可以手动恢复
ls ~/.smartemailsender/backups/
# backup_1.0.0_20240815_103000/

# 复制备份文件到应用目录
cp -r ~/.smartemailsender/backups/backup_1.0.0_20240815_103000/* /path/to/app/
```

## ⚙️ 配置选项

### 用户配置
```json
// ~/.smartemailsender/update_settings.json
{
  "auto_check": true,           // 自动检查更新
  "check_interval": 24,         // 检查间隔（小时）
  "preferred_cdn": "auto",      // 优选CDN: auto/gitee/github
  "download_incremental": true, // 优先下载增量更新
  "backup_count": 3            // 保留备份数量
}
```

### 开发者配置
```python
# 更新服务器配置
UPDATE_INFO_URLS = [
    "https://your-cdn.com/smartemailsender/update_info.json",
    "https://gitee.com/your-name/smartemailsender/raw/main/update_info.json",
    "https://github.com/your-name/smartemailsender/raw/main/update_info.json"
]
```

## 📈 监控和分析

### 更新成功率监控
```python
# 可以添加更新统计
def report_update_result(success: bool, from_version: str, to_version: str):
    analytics_data = {
        'event': 'update_completed',
        'success': success,
        'from_version': from_version,
        'to_version': to_version,
        'timestamp': datetime.now().isoformat()
    }
    # 发送到分析服务
```

### CDN性能监控
```python
# 监控各CDN的下载速度
def monitor_cdn_performance():
    from cdn_selector import CDNSelector
    selector = CDNSelector()
    
    for cdn in CDNS:
        latency, available = selector.test_cdn_speed(cdn)
        print(f"{cdn}: {latency}ms, available: {available}")
```

## 🎯 最佳实践

1. **版本策略**: 使用语义化版本号（major.minor.patch）
2. **测试充分**: 在发布前充分测试更新流程
3. **渐进发布**: 可以先发布给部分用户测试
4. **备份机制**: 始终确保用户可以回滚到稳定版本
5. **用户体验**: 提供清晰的更新说明和进度提示

这个自动更新系统确保用户始终能够以最小的代价获得最新的功能和修复！