# SmartEmailSender Windows版本构建指南

## 📋 准备工作

### 1. 环境要求
- Windows 10 或更高版本
- Python 3.9+ (推荐3.11)
- PyInstaller 5.0+
- Git for Windows
- PowerShell 5.0+

### 2. 可选工具
- **NSIS 3.08+** - 创建专业安装程序
- **Inno Setup 6.0+** - 创建高级安装程序
- **Visual Studio Build Tools** - 编译某些依赖

## 🔧 依赖安装

```bash
# 安装Python依赖
pip install -r requirements.txt
pip install pyinstaller
pip install pillow  # 用于图标处理

# 如果需要处理Windows特定功能
pip install pywin32
```

## 🖼️ 图标文件准备

由于我们只有macOS的.icns文件，需要创建Windows的.ico文件：

### 方法1: 在线转换
1. 访问 https://www.icoconverter.com/
2. 上传 `assets/SmartEmailSender.icns`
3. 转换为 `SmartEmailSender.ico`
4. 保存到 `assets/` 目录

### 方法2: 使用Pillow转换 (在有图标的情况下)
```python
from PIL import Image
import os

# 转换icns到ico (如果系统支持)
if os.path.exists('assets/SmartEmailSender.icns'):
    try:
        img = Image.open('assets/SmartEmailSender.icns')
        img.save('assets/SmartEmailSender.ico', format='ICO', sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
        print("✅ 图标转换成功")
    except Exception as e:
        print(f"❌ 图标转换失败: {e}")
```

## 🏗️ 构建步骤

### 1. 使用批处理脚本构建 (推荐)
```cmd
# 在Windows命令提示符中运行
build_windows.bat
```

### 2. 手动构建
```cmd
# 清理旧构建
rmdir /s /q build dist releases 2>nul
mkdir releases

# 构建应用
pyinstaller SmartEmailSender_windows.spec --clean --noconfirm

# 创建ZIP包
powershell "Compress-Archive -Path 'dist\SmartEmailSender' -DestinationPath 'releases\SmartEmailSender-Windows.zip'"
```

### 3. 在macOS/Linux上交叉构建 (实验性)
```bash
# 使用Wine环境 (需要配置)
wine python -m PyInstaller SmartEmailSender_windows.spec --clean --noconfirm
```

## 📦 创建安装程序

### 使用NSIS
```cmd
# 如果安装了NSIS
"C:\Program Files (x86)\NSIS\makensis.exe" SmartEmailSender_advanced.nsi
```

### 使用Inno Setup
```cmd
# 如果安装了Inno Setup
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" SmartEmailSender.iss
```

## 🧪 测试

### 基本功能测试
1. 运行 `dist\SmartEmailSender\SmartEmailSender.exe`
2. 检查界面是否正常显示
3. 测试Microsoft 365登录
4. 验证Excel文件导入
5. 测试邮件发送功能

### 兼容性测试
- Windows 10 (多个版本)
- Windows 11
- 不同的屏幕分辨率
- 有/无网络连接的情况

## 🔐 安全检查

运行安全检查脚本：
```bash
# 在Git Bash中运行
./security_check.sh
```

确保没有以下敏感文件：
- `token_cache.json`
- `.env`
- `credentials`
- `secrets`
- 任何包含密钥的文件

## 📊 预期结果

### 构建输出
```
releases/
├── SmartEmailSender-Windows.zip          # 绿色版 (~400-600MB)
├── SmartEmailSender-Setup.exe            # NSIS安装程序 (~400-600MB)
├── SmartEmailSender-Setup-InnoSetup.exe  # Inno Setup安装程序 (~400-600MB)
└── README.txt                            # 用户说明
```

### 应用结构
```
SmartEmailSender/
├── SmartEmailSender.exe                  # 主程序
├── _internal/                            # PyInstaller内部文件
│   ├── PySide6/                         # Qt框架
│   ├── pandas/                          # 数据处理库
│   ├── msal/                            # 认证库
│   └── ...
├── assets/                              # 资源文件
└── field_mapping_config.json           # 配置文件
```

## 🚨 常见问题

### 1. 构建失败
- 检查Python版本和依赖
- 确保有足够磁盘空间 (至少2GB)
- 临时禁用杀毒软件

### 2. 应用启动失败
- 检查是否缺少Microsoft Visual C++ Redistributable
- 确保Windows版本兼容
- 查看Windows事件查看器中的错误信息

### 3. WebEngine问题
- 确保系统已安装Microsoft Edge
- 检查WebView2运行时是否安装

### 4. 文件大小过大
- 检查是否包含了不必要的文件
- 考虑使用UPX压缩 (可能导致杀毒软件误报)

## 🎯 优化建议

### 减少文件大小
1. 排除不必要的Qt模块
2. 移除调试信息
3. 使用UPX压缩 (谨慎使用)

### 提升性能
1. 启用Windows-specific优化
2. 使用windowed模式而非console模式
3. 预编译Python字节码

### 用户体验
1. 添加启动画面
2. 创建卸载程序
3. 支持文件关联
4. 添加到Windows防火墙例外

## 📱 分发建议

### 发布渠道
- GitHub Releases
- 官方网站下载
- 企业内部分发

### 文件命名
- `SmartEmailSender-v1.0.0-Windows-x64.zip`
- `SmartEmailSender-Setup-v1.0.0.exe`

### 签名证书
建议购买代码签名证书，避免Windows Defender警告。

---

## 💡 提示

在没有Windows环境的情况下，建议：
1. 使用虚拟机安装Windows
2. 使用云端Windows实例
3. 找Windows用户协助构建
4. 考虑GitHub Actions自动化构建

完成构建后，请进行充分测试确保功能完整性！