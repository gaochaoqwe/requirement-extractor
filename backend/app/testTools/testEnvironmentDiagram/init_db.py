#!/usr/bin/env python3
"""
初始化测试环境图工具数据库
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 直接导入本地模块
from config.config import DATABASE_URL
from models.models import Base
from sqlalchemy import create_engine

def init_database():
    """初始化数据库"""
    try:
        print("正在初始化测试环境图工具数据库...")
        print(f"数据库路径: {DATABASE_URL}")
        
        # 创建数据库引擎
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        
        # 删除现有表（如果存在）
        print("删除现有表...")
        Base.metadata.drop_all(bind=engine)
        
        # 创建新表
        print("创建新表...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ 数据库初始化完成！")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    init_database() 