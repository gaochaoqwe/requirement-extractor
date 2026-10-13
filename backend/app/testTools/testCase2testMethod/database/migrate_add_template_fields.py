"""
数据库迁移脚本：添加用例模板字段和处理模式字段
"""
import sqlite3
from pathlib import Path
import logging

def migrate_database():
    """执行数据库迁移"""
    # 数据库文件路径
    db_path = Path(__file__).parent.parent / "test_case_reverse.db"
    
    try:
        # 连接数据库（如果不存在会自动创建）
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("开始数据库迁移...")
        print(f"数据库路径: {db_path}")
        
        # 检查表是否存在，如果不存在则创建
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_case_reverse_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(50) UNIQUE NOT NULL,
                original_filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                status VARCHAR(20) DEFAULT 'uploaded',
                processing_mode VARCHAR(20) DEFAULT 'normal',
                total_test_items INTEGER DEFAULT 0,
                processed_test_items INTEGER DEFAULT 0,
                error_message TEXT,
                output_filename VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(50) NOT NULL,
                test_item_name TEXT NOT NULL,
                test_cases_data TEXT,
                test_content TEXT,
                test_method TEXT,
                case_template_name TEXT,
                case_template_input TEXT,
                case_template_expected TEXT,
                generation_status VARCHAR(20) DEFAULT 'pending',
                ai_response_raw TEXT,
                error_message TEXT,
                processing_time REAL,
                retry_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id VARCHAR(50) NOT NULL,
                operation_type VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL,
                message TEXT,
                execution_time REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("✓ 数据库表创建/验证完成")
        
        # 检查是否已经存在新字段（针对已有数据库）
        cursor.execute("PRAGMA table_info(test_case_reverse_sessions)")
        session_columns = [row[1] for row in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(test_items)")
        item_columns = [row[1] for row in cursor.fetchall()]
        
        # 为 test_case_reverse_sessions 表添加 processing_mode 字段（如果不存在）
        if 'processing_mode' not in session_columns:
            print("添加 processing_mode 字段到 test_case_reverse_sessions 表...")
            cursor.execute("""
                ALTER TABLE test_case_reverse_sessions 
                ADD COLUMN processing_mode VARCHAR(20) DEFAULT 'normal'
            """)
            print("✓ processing_mode 字段添加成功")
        else:
            print("✓ processing_mode 字段已存在")
        
        # 为 test_items 表添加用例模板字段（如果不存在）
        template_fields = [
            ('case_template_name', 'TEXT'),
            ('case_template_input', 'TEXT'), 
            ('case_template_expected', 'TEXT'),
            ('retry_count', 'INTEGER DEFAULT 0')
        ]
        
        for field_name, field_type in template_fields:
            if field_name not in item_columns:
                print(f"添加 {field_name} 字段到 test_items 表...")
                cursor.execute(f"""
                    ALTER TABLE test_items 
                    ADD COLUMN {field_name} {field_type}
                """)
                print(f"✓ {field_name} 字段添加成功")
            else:
                print(f"✓ {field_name} 字段已存在")
        
        # 提交更改
        conn.commit()
        print("数据库迁移完成！")
        
        return True
        
    except Exception as e:
        print(f"数据库迁移失败: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_database() 