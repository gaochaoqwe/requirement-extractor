#!/usr/bin/env python3
"""
初始化文档审查配置项数据库
"""
import sys
import os
import sqlite3
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.documentReview.ConfigurationItem.db.database import init_db, DATABASE_PATH, DATABASE_URL

def create_database():
    """创建数据库表结构"""
    try:
        # 确保数据库目录存在
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        sys.stderr.write(f"正在初始化数据库: {DATABASE_PATH}\n")
        
        # 初始化数据库表
        init_db()
        
        sys.stderr.write("数据库表创建完成\n")
        
        # 显示创建的表
        conn = sqlite3.connect(str(DATABASE_PATH))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        sys.stderr.write("数据库中的表:\n")
        for table in tables:
            sys.stderr.write(f"- {table[0]}\n")
        conn.close()
        
        return True
        
    except Exception as e:
        sys.stderr.write(f"数据库创建失败: {e}\n")
        return False

def migrate_data():
    """数据迁移函数"""
    try:
        # 检查是否存在旧数据库需要迁移
        old_db_path = current_dir / "document_review.db"
        sys.stderr.write(f"原数据库路径: {old_db_path}\n")
        sys.stderr.write(f"新数据库路径: {DATABASE_PATH}\n")
        
        if not old_db_path.exists():
            sys.stderr.write("警告：原数据库文件不存在，跳过数据迁移\n")
            return True
        
        # 连接到旧数据库和新数据库
        old_conn = sqlite3.connect(str(old_db_path))
        new_conn = sqlite3.connect(str(DATABASE_PATH))
        
        try:
            old_cursor = old_conn.cursor()
            new_cursor = new_conn.cursor()
            
            # 迁移review_sessions表
            try:
                old_cursor.execute("SELECT * FROM review_sessions")
                sessions = old_cursor.fetchall()
                
                if sessions:
                    sys.stderr.write("正在迁移review_sessions表...\n")
                    
                    # 获取列信息
                    old_cursor.execute("PRAGMA table_info(review_sessions)")
                    columns = [col[1] for col in old_cursor.fetchall()]
                    
                    placeholders = ','.join(['?' for _ in columns])
                    column_names = ','.join(columns)
                    
                    new_cursor.executemany(
                        f"INSERT OR REPLACE INTO review_sessions ({column_names}) VALUES ({placeholders})",
                        sessions
                    )
                    
                    sys.stderr.write(f"已迁移 {len(sessions)} 条review_sessions记录\n")
                    
            except sqlite3.Error as e:
                sys.stderr.write(f"迁移review_sessions表时出错: {e}\n")
            
            # 迁移review_results表
            try:
                old_cursor.execute("SELECT * FROM review_results")
                results = old_cursor.fetchall()
                
                if results:
                    sys.stderr.write("正在迁移review_results表...\n")
                    
                    # 获取列信息
                    old_cursor.execute("PRAGMA table_info(review_results)")
                    columns = [col[1] for col in old_cursor.fetchall()]
                    
                    placeholders = ','.join(['?' for _ in columns])
                    column_names = ','.join(columns)
                    
                    new_cursor.executemany(
                        f"INSERT OR REPLACE INTO review_results ({column_names}) VALUES ({placeholders})",
                        results
                    )
                    
                    sys.stderr.write(f"已迁移 {len(results)} 条review_results记录\n")
                    
            except sqlite3.Error as e:
                sys.stderr.write(f"迁移review_results表时出错: {e}\n")
            
            # 提交事务
            new_conn.commit()
            sys.stderr.write("数据迁移完成！\n")
            return True
            
        except Exception as e:
            new_conn.rollback()
            sys.stderr.write(f"数据迁移失败: {e}\n")
            return False
            
        finally:
            old_conn.close()
            new_conn.close()
            
    except Exception as e:
        sys.stderr.write(f"数据迁移过程出错: {e}\n")
        return False

def main():
    """主函数"""
    try:
        sys.stderr.write("开始初始化文档审查配置项数据库...\n")
        
        # 创建数据库
        if not create_database():
            sys.stderr.write("数据库创建失败，退出\n")
            return
        
        # 数据迁移
        sys.stderr.write("\n开始数据迁移...\n")
        if migrate_data():
            sys.stderr.write("\n数据库初始化和数据迁移完成！\n")
        else:
            sys.stderr.write("\n数据库初始化完成，但数据迁移失败！\n")
            
    except Exception as e:
        sys.stderr.write(f"初始化过程出错: {e}\n")

if __name__ == "__main__":
    main() 