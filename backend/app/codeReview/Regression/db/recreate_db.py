#!/usr/bin/env python3
"""
重新创建回归测试数据库
"""
import os
import sys
from .database import init_db, DATABASE_URL

def recreate_database():
    """重新创建数据库"""
    try:
        # 获取数据库文件路径
        if DATABASE_URL.startswith('sqlite:///'):
            db_path = DATABASE_URL.replace('sqlite:///', '')
            sys.stderr.write(f"数据库文件位置: {DATABASE_URL}\n")
            
            # 删除现有数据库文件
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                    sys.stderr.write(f"删除数据库文件: {db_path}\n")
                    sys.stderr.write("旧数据库文件已删除\n")
                except Exception as e:
                    sys.stderr.write(f"删除数据库文件时出错: {e}\n")
        
        # 重新初始化数据库
        sys.stderr.write("正在初始化数据库...\n")
        init_db()
        
        sys.stderr.write("数据库重新创建完成！\n")
    except Exception as e:
        sys.stderr.write(f"数据库初始化失败: {e}\n")
        raise

if __name__ == "__main__":
    recreate_database()
