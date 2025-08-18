#!/bin/bash
cd "$(dirname "$0")"

echo "SmartEmailSender 启动器"
echo "======================="

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，创建中..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 检查依赖
echo "🔍 检查依赖..."
python -c "
import sys
print(f'Python: {sys.executable}')

deps = ['pandas', 'requests', 'msal', 'jinja2', 'dotenv', 'PySide6', 'openpyxl']
for dep in deps:
    try:
        if dep == 'dotenv':
            import python_dotenv as dotenv
            module = dotenv
        else:
            module = __import__(dep)
        version = getattr(module, '__version__', 'unknown')
        print(f'✅ {dep}: {version}')
    except ImportError as e:
        print(f'❌ {dep}: {e}')
"

echo ""
echo "🚀 启动SmartEmailSender..."
python src/SmartEmailSender.py