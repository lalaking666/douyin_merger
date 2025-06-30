#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
抖音视频合并工具安装脚本
"""

import os
import shutil
from pathlib import Path

def setup_project():
    """设置项目配置文件"""
    src_dir = Path(__file__).parent / "src"
    
    # 检查并创建示例配置文件
    if not (src_dir / "cookies.json").exists():
        if (src_dir / "cookies.example.json").exists():
            shutil.copy(src_dir / "cookies.example.json", src_dir / "cookies.json")
            print("✅ 已创建 cookies.json 配置文件")
            print("   请编辑 src/cookies.json 文件，填入你的Cookie信息")
        else:
            print("❌ 未找到 cookies.example.json 文件")
    
    if not (src_dir / "config.json").exists():
        if (src_dir / "config.example.json").exists():
            shutil.copy(src_dir / "config.example.json", src_dir / "config.json")
            print("✅ 已创建 config.json 配置文件")
            print("   请编辑 src/config.json 文件，填入要下载的用户信息")
        else:
            print("❌ 未找到 config.example.json 文件")
    
    # 创建数据目录
    data_dir = src_dir / "data"
    data_dir.mkdir(exist_ok=True)
    print("✅ 已创建数据目录")
    
    print("\n📝 配置说明:")
    print("1. 编辑 src/cookies.json - 填入从Cookie Editor导出的Cookie信息")
    print("2. 编辑 src/config.json - 填入要下载的用户昵称和sec_uid")
    print("3. 运行: python src/core.py")
    print("\n📖 详细说明请查看 README.md 文件")

if __name__ == "__main__":
    setup_project() 