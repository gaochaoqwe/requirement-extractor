"""
数据库迁移脚本：添加 rule_type 字段
"""
import sqlite3
from pathlib import Path

def migrate_database(db_path: str):
    """添加 rule_type 字段到 static_analysis_issues 表"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(static_analysis_issues)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'rule_type' not in columns:
            print("Adding rule_type field...")
            cursor.execute("""
                ALTER TABLE static_analysis_issues 
                ADD COLUMN rule_type TEXT
            """)
            
            # 根据 sheet_name 填充 rule_type
            print("Filling rule_type based on sheet_name...")
            cursor.execute("""
                UPDATE static_analysis_issues 
                SET rule_type = 'gjb' 
                WHERE sheet_name LIKE '%GJB%' OR sheet_name LIKE '%8114%'
            """)
            cursor.execute("""
                UPDATE static_analysis_issues 
                SET rule_type = 'cwe' 
                WHERE sheet_name LIKE '%CWE%' OR sheet_name LIKE '%缺陷检测%'
            """)
            
            conn.commit()
            print("[OK] rule_type field added successfully")
        else:
            print("[SKIP] rule_type field already exists")
        
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Migration failed: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    # 获取数据库路径
    current_dir = Path(__file__).parent
    db_path = current_dir / "static_analysis_filter.db"
    
    if db_path.exists():
        print(f"Migrating database: {db_path}")
        migrate_database(str(db_path))
    else:
        print(f"Database not found: {db_path}")

