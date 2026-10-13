#!/usr/bin/env python3
"""
数据库优化脚本
"""
import os
import sys
import sqlite3
from pathlib import Path
from .database import DATABASE_URL

def optimize_database():
    """优化数据库结构和性能"""
    try:
        # 获取数据库文件路径
        if DATABASE_URL.startswith('sqlite:///'):
            db_path = DATABASE_URL.replace('sqlite:///', '')
            sys.stderr.write(f"数据库路径: {db_path}\n")
            
            if not os.path.exists(db_path):
                sys.stderr.write("错误：数据库文件不存在！\n")
                return
            
            # 连接数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            try:
                # 添加索引以提高查询性能
                sys.stderr.write("正在添加索引...\n")
                
                # 为常用查询字段添加索引
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_tasks_status ON regression_tasks(status)",
                    "CREATE INDEX IF NOT EXISTS idx_files_task_id ON regression_files(task_id)",
                    "CREATE INDEX IF NOT EXISTS idx_functions_file_id ON regression_functions(file_id)",
                    "CREATE INDEX IF NOT EXISTS idx_problems_task_id ON regression_problems(task_id)",
                    "CREATE INDEX IF NOT EXISTS idx_problems_file_id ON regression_problems(file_id)",
                    "CREATE INDEX IF NOT EXISTS idx_problems_function_id ON regression_problems(function_id)",
                    "CREATE INDEX IF NOT EXISTS idx_problems_issue_level ON regression_problems(issue_level)",
                    "CREATE INDEX IF NOT EXISTS idx_files_created_at ON regression_files(created_at)",
                    "CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON regression_tasks(created_at)"
                ]
                
                for index_sql in indexes:
                    cursor.execute(index_sql)
                
                # 检查并添加缺失的字段
                cursor.execute("PRAGMA table_info(regression_tasks)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'code_file_id' not in columns:
                    sys.stderr.write("检测到缺少字段 'code_file_id'，正在添加...\n")
                    cursor.execute("ALTER TABLE regression_tasks ADD COLUMN code_file_id INTEGER")
                    sys.stderr.write("已成功添加 code_file_id 字段\n")
                
                # 提交更改
                conn.commit()
                
                # 优化数据库
                cursor.execute("VACUUM")
                cursor.execute("ANALYZE")
                
                sys.stderr.write("数据库优化完成！\n")
                
            finally:
                cursor.close()
                conn.close()
                
    except Exception as e:
        sys.stderr.write(f"数据库优化失败: {e}\n")
        raise

def main():
    """主函数"""
    try:
        optimize_database()
        sys.stderr.write("数据库优化成功完成！\n")
    except Exception:
        sys.stderr.write("数据库优化过程中出现错误。\n")

if __name__ == "__main__":
    main()
