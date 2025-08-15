# SmartEmailSender 依赖包CDN部署指南

本指南帮助您配置不同的CDN服务来托管QtWebEngine依赖包，确保中国内地和海外用户都能快速下载。

## 📦 准备依赖包

首先构建并准备依赖包：

```bash
# 1. 构建完整版
pyinstaller SmartEmailSender.spec

# 2. 提取依赖包
./prepare_deps.sh

# 3. 查看生成的文件
ls -lh dependency_packages/
# qtwebengine-6.5-macos.tar.gz (~580MB)
```

## 🇨🇳 国内CDN配置

### 1. Gitee (码云) - 免费方案

最简单的免费方案，适合小型项目：

```bash
# 1. 创建Gitee仓库
# 访问 https://gitee.com 创建账号
# 新建仓库: smartemailsender-deps

# 2. 上传依赖包到Release
# 在仓库页面点击"发行版" -> "创建发行版"
# 上传 qtwebengine-6.5-macos.tar.gz
# 记录下载链接: https://gitee.com/your-name/smartemailsender-deps/releases/download/v1.0/qtwebengine-6.5-macos.tar.gz

# 注意：Gitee单文件限制100MB，大文件需要分卷
# 分卷压缩示例：
split -b 95M qtwebengine-6.5-macos.tar.gz qtwebengine-part-
# 上传所有分卷文件
```

### 2. 阿里云OSS - 专业方案

适合商业项目，按流量计费：

```bash
# 1. 开通阿里云OSS服务
# 访问: https://www.aliyun.com/product/oss

# 2. 创建Bucket
# - Bucket名称: smartemailsender
# - 地域: 华北2(北京) 或就近选择
# - 读写权限: 公共读

# 3. 上传文件
ossutil cp dependency_packages/qtwebengine-6.5-macos.tar.gz \
  oss://smartemailsender/deps/v1.0/

# 4. 配置CDN加速（可选但推荐）
# - 添加CDN域名: deps.smartemailsender.cn
# - 源站类型: OSS域名
# - 回源配置: smartemailsender.oss-cn-beijing.aliyuncs.com

# 5. 获取下载地址
# https://smartemailsender.oss-cn-beijing.aliyuncs.com/deps/v1.0/qtwebengine-6.5-macos.tar.gz
# 或CDN地址: https://deps.smartemailsender.cn/v1.0/qtwebengine-6.5-macos.tar.gz
```

### 3. 腾讯云COS - 专业方案

另一个主流选择：

```bash
# 1. 开通腾讯云COS
# 访问: https://cloud.tencent.com/product/cos

# 2. 创建存储桶
# - 名称: smartemailsender-1234567890
# - 地域: 北京
# - 访问权限: 公有读私有写

# 3. 上传文件（使用COSBrowser或命令行）
coscmd upload dependency_packages/qtwebengine-6.5-macos.tar.gz \
  deps/v1.0/qtwebengine-6.5-macos.tar.gz

# 4. 获取地址
# https://smartemailsender-1234567890.cos.ap-beijing.myqcloud.com/deps/v1.0/qtwebengine-6.5-macos.tar.gz
```

### 4. 七牛云 - 备选方案

```bash
# 1. 注册七牛云账号
# 访问: https://www.qiniu.com

# 2. 创建存储空间
# - 空间名称: smartemailsender
# - 存储区域: 华北

# 3. 上传文件并获取外链
qshell put smartemailsender qtwebengine-6.5-macos.tar.gz \
  dependency_packages/qtwebengine-6.5-macos.tar.gz

# 获取地址: http://xxx.bkt.clouddn.com/qtwebengine-6.5-macos.tar.gz
```

## 🌍 国际CDN配置

### 1. GitHub Releases - 免费方案

最常用的国际方案：

```bash
# 1. 创建GitHub仓库
# https://github.com/new
# Repository name: smartemailsender-deps

# 2. 创建Release
gh release create v1.0 \
  --title "SmartEmailSender Dependencies v1.0" \
  --notes "QtWebEngine dependencies for lite version" \
  dependency_packages/qtwebengine-6.5-macos.tar.gz

# 3. 获取下载地址
# https://github.com/your-name/smartemailsender-deps/releases/download/v1.0/qtwebengine-6.5-macos.tar.gz
```

### 2. jsDelivr CDN - 免费加速

自动加速GitHub releases：

```bash
# 自动转换GitHub地址为CDN地址
# GitHub: https://github.com/user/repo/releases/download/v1.0/file.tar.gz
# jsDelivr: https://cdn.jsdelivr.net/gh/user/repo@v1.0/file.tar.gz

# 注意：jsDelivr对文件大小有限制（50MB），需要分卷
```

### 3. AWS S3 + CloudFront

专业的全球CDN方案：

```bash
# 1. 创建S3 Bucket
aws s3 mb s3://smartemailsender-deps --region us-east-1

# 2. 上传文件
aws s3 cp dependency_packages/qtwebengine-6.5-macos.tar.gz \
  s3://smartemailsender-deps/v1.0/ --acl public-read

# 3. 配置CloudFront分发
# 通过AWS Console配置CloudFront指向S3 bucket

# 获取地址: https://d1234567890.cloudfront.net/v1.0/qtwebengine-6.5-macos.tar.gz
```

## 📝 更新代码配置

配置好CDN后，更新 `src/dependency_manager.py`：

```python
CDN_URLS = [
    # 国内镜像源
    "https://gitee.com/your-name/smartemailsender-deps/releases/download/v1.0/",
    "https://smartemailsender.oss-cn-beijing.aliyuncs.com/deps/v1.0/",
    "https://smartemailsender-1234567890.cos.ap-beijing.myqcloud.com/deps/v1.0/",
    
    # 国际镜像源
    "https://github.com/your-name/smartemailsender-deps/releases/download/v1.0/",
    "https://cdn.jsdelivr.net/gh/your-name/smartemailsender-deps@v1.0/",
]

# 更新SHA256值
DEPENDENCIES = {
    "qtwebengine": {
        "darwin": {
            "url": "qtwebengine-6.5-macos.tar.gz",
            "size": 608174080,  # 实际文件大小
            "sha256": "实际计算的SHA256值",  # 使用 shasum -a 256 文件名
            ...
        }
    }
}
```

## 🔧 分卷处理（大文件）

如果CDN有文件大小限制：

```bash
# 1. 分卷压缩（每卷95MB）
split -b 95M qtwebengine-6.5-macos.tar.gz qtwebengine.part.

# 2. 上传所有分卷
ls qtwebengine.part.* | xargs -I {} gh release upload v1.0 {}

# 3. 修改下载逻辑支持分卷下载和合并
```

## 📊 成本估算

| CDN服务 | 免费额度 | 超出计费 | 适合场景 |
|---------|----------|----------|----------|
| Gitee | 1GB存储,100MB/文件 | - | 测试/个人项目 |
| GitHub | 无限存储,2GB/文件 | - | 开源项目 |
| 阿里云OSS | 5GB存储/月 | ¥0.12/GB流量 | 国内商业项目 |
| 腾讯云COS | 10GB存储/月 | ¥0.15/GB流量 | 国内商业项目 |
| AWS S3 | 5GB存储/年 | $0.09/GB流量 | 国际项目 |

## 🚀 测试CDN速度

```bash
# 测试下载速度
curl -o /dev/null -s -w "Time: %{time_total}s\nSpeed: %{speed_download} bytes/s\n" \
  https://your-cdn-url/qtwebengine-6.5-macos.tar.gz

# 使用智能CDN选择器测试
python3 -c "
from cdn_selector import CDNSelector
selector = CDNSelector()
urls = ['url1', 'url2', 'url3']
best = selector.select_best_cdn(urls)
print('Best CDN:', best[0])
"
```

## ✅ 最佳实践

1. **多CDN备份**：配置至少2个国内+2个国际CDN
2. **智能选择**：使用cdn_selector.py自动选择最快源
3. **分卷上传**：大文件分卷以适应不同CDN限制
4. **定期测试**：监控CDN可用性和速度
5. **版本管理**：使用版本号管理不同版本的依赖

## 📱 用户体验优化

1. **显示下载源**：告诉用户正在从哪里下载
2. **速度显示**：显示实时下载速度
3. **断点续传**：支持下载中断后继续
4. **手动切换**：允许用户手动选择CDN源
5. **离线安装**：提供离线安装包下载选项