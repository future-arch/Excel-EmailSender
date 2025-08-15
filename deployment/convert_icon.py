#!/usr/bin/env python3
"""
图标转换工具 - 将macOS的.icns转换为Windows的.ico
"""

import os
from pathlib import Path

def convert_icns_to_ico():
    """尝试将icns文件转换为ico文件"""
    
    assets_path = Path('assets')
    icns_file = assets_path / 'SmartEmailSender.icns'
    ico_file = assets_path / 'SmartEmailSender.ico'
    
    if ico_file.exists():
        print(f"✅ Windows图标文件已存在: {ico_file}")
        return True
    
    if not icns_file.exists():
        print(f"❌ 未找到macOS图标文件: {icns_file}")
        return False
    
    try:
        from PIL import Image
        print(f"🔄 正在转换 {icns_file} -> {ico_file}")
        
        # 尝试打开icns文件
        img = Image.open(icns_file)
        
        # 转换为ico格式，包含多种尺寸
        img.save(ico_file, format='ICO', sizes=[
            (16, 16), (24, 24), (32, 32), (48, 48), 
            (64, 64), (128, 128), (256, 256)
        ])
        
        print(f"✅ 图标转换成功: {ico_file}")
        return True
        
    except ImportError:
        print("❌ 未安装Pillow库，无法转换图标")
        print("请运行: pip install Pillow")
        return False
        
    except Exception as e:
        print(f"❌ 图标转换失败: {e}")
        print("\n建议手动转换:")
        print("1. 访问 https://www.icoconverter.com/")
        print(f"2. 上传 {icns_file}")
        print(f"3. 下载转换后的ico文件并保存为 {ico_file}")
        return False

def create_placeholder_icon():
    """创建一个简单的占位符图标"""
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        assets_path = Path('assets')
        ico_file = assets_path / 'SmartEmailSender.ico'
        
        if ico_file.exists():
            return True
            
        # 创建256x256的图标
        img = Image.new('RGBA', (256, 256), (0, 123, 255, 255))  # 蓝色背景
        draw = ImageDraw.Draw(img)
        
        # 画一个简单的邮件图标
        # 邮件外框
        draw.rectangle([50, 100, 206, 180], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))
        
        # 邮件封口
        draw.polygon([50, 100, 128, 140, 206, 100], fill=(220, 220, 220, 255), outline=(0, 0, 0, 255))
        
        # 添加文字 "S" (SmartEmailSender的首字母)
        try:
            font = ImageFont.truetype("arial.ttf", 60)
        except:
            font = ImageFont.load_default()
            
        # 计算文字位置使其居中
        bbox = draw.textbbox((0, 0), "S", font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (256 - text_width) // 2
        y = (256 - text_height) // 2 + 20
        
        draw.text((x, y), "S", fill=(255, 255, 255, 255), font=font)
        
        # 保存为ico格式
        img.save(ico_file, format='ICO', sizes=[
            (16, 16), (24, 24), (32, 32), (48, 48), 
            (64, 64), (128, 128), (256, 256)
        ])
        
        print(f"✅ 已创建占位符图标: {ico_file}")
        return True
        
    except ImportError:
        print("❌ 需要安装Pillow来创建图标: pip install Pillow")
        return False
        
    except Exception as e:
        print(f"❌ 创建图标失败: {e}")
        return False

def main():
    print("🎨 SmartEmailSender 图标转换工具")
    print("=" * 40)
    
    # 确保assets目录存在
    Path('assets').mkdir(exist_ok=True)
    
    # 尝试转换icns到ico
    if convert_icns_to_ico():
        return
    
    # 如果转换失败，创建占位符图标
    print("\n🔄 尝试创建占位符图标...")
    if create_placeholder_icon():
        return
    
    print("\n❌ 无法创建Windows图标文件")
    print("请手动创建SmartEmailSender.ico文件并放入assets目录")

if __name__ == "__main__":
    main()