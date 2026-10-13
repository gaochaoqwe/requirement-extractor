#!/usr/bin/env python3
"""
文档批注转问题报告单工具 - 数据库初始化脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from database.database import create_tables, drop_tables

def init_database():
    """初始化数据库"""
    try:
        print("正在初始化文档批注转问题报告单工具数据库...")
        
        # 删除现有表（如果存在）
        print("删除现有表...")
        drop_tables()
        
        # 创建新表
        print("创建数据库表...")
        create_tables()
        
        print("✅ 数据库初始化成功！")
        return True
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1) 