"""
数据迁移脚本：从test_management.db迁移数据到新的documentReview.db
"""
import sqlite3
import os
from pathlib import Path
from datetime import datetime


def migrate_data():
    """
    从原有的test_management.db迁移数据到新的documentReview.db
    """
    # 数据库路径
    current_dir = Path(__file__).parent
    new_db_path = current_dir / "documentReview.db"
    
    # 原有数据库路径
    backend_dir = Path(__file__).parent.parent.parent.parent.parent
    old_db_path = backend_dir / "test_management.db"
    
    print(f"原数据库路径: {old_db_path}")
    print(f"新数据库路径: {new_db_path}")
    
    if not old_db_path.exists():
        print("错误：原数据库文件不存在！")
        return False
    
    try:
        # 连接到新数据库
        new_conn = sqlite3.connect(str(new_db_path))
        new_cursor = new_conn.cursor()
        
        # 连接到原数据库
        old_conn = sqlite3.connect(str(old_db_path))
        old_cursor = old_conn.cursor()
        
        # 迁移review_sessions表
        print("正在迁移review_sessions表...")
        old_cursor.execute("SELECT id, project_id, created_at FROM review_sessions")
        sessions = old_cursor.fetchall()
        
        for session in sessions:
            new_cursor.execute(
                "INSERT OR REPLACE INTO review_sessions (id, project_id, created_at) VALUES (?, ?, ?)",
                session
            )
        print(f"已迁移 {len(sessions)} 条review_sessions记录")
        
        # 迁移review_results表，并为每条记录添加默认的问题等级
        print("正在迁移review_results表...")
        old_cursor.execute("""
            SELECT id, session_id, doc_type, doc_name, requirement_content, 
                   violation_rules, issue_name, issue_location, 
                   description_requirement, description_issue, 
                   description_location, description_impact 
            FROM review_results
        """)
        results = old_cursor.fetchall()
        
        # 问题等级分配逻辑：根据问题名称关键词判断等级
        def get_issue_level(issue_name, violation_rules):
            """根据问题名称和违反规则判断问题等级"""
            if not issue_name:
                return '一般问题'
                
            issue_name = issue_name.lower()
            violation_rules = (violation_rules or '').lower()
            
            # 重要问题关键词
            important_keywords = ['安全', '性能', '关键', '严重', '错误', '失败', '崩溃', '数据丢失']
            # 建议改进关键词  
            suggestion_keywords = ['建议', '优化', '改进', '完善', '增强', '美化']
            
            # 检查是否包含重要问题关键词
            for keyword in important_keywords:
                if keyword in issue_name or keyword in violation_rules:
                    return '重要问题'
            
            # 检查是否包含建议改进关键词
            for keyword in suggestion_keywords:
                if keyword in issue_name or keyword in violation_rules:
                    return '建议改进'
            
            # 默认为一般问题
            return '一般问题'
        
        for result in results:
            # 为每条记录分配问题等级
            issue_level = get_issue_level(result[6], result[5])  # issue_name, violation_rules
            
            new_cursor.execute("""
                INSERT OR REPLACE INTO review_results 
                (id, session_id, doc_type, doc_name, requirement_content, 
                 violation_rules, issue_level, issue_name, issue_location, 
                 description_requirement, description_issue, 
                 description_location, description_impact) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, result + (issue_level,))
        
        print(f"已迁移 {len(results)} 条review_results记录")
        
        # 提交更改
        new_conn.commit()
        
        print("数据迁移完成！")
        return True
        
    except Exception as e:
        print(f"数据迁移失败: {e}")
        if 'new_conn' in locals():
            new_conn.rollback()
        return False
    finally:
        if 'new_conn' in locals():
            new_conn.close()
        if 'old_conn' in locals():
            old_conn.close()


if __name__ == "__main__":
    # 首先初始化数据库表结构
    from .database import init_db
    print("正在初始化数据库表结构...")
    init_db(drop_all=True)
    
    # 然后迁移数据
    print("开始数据迁移...")
    success = migrate_data()
    
    if success:
        print("数据迁移成功完成！")
    else:
        print("数据迁移失败！") 