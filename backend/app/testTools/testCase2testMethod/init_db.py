"""
测试用例反向推导工具数据库初始化
"""
import sqlite3
from pathlib import Path

def init_database():
    """初始化数据库"""
    # 数据库文件路径
    db_path = Path(__file__).parent / "test_case_reverse.db"
    
    # 如果数据库文件已存在，删除它
    if db_path.exists():
        db_path.unlink()
        print(f"已删除旧数据库文件: {db_path}")
    
    # 创建新数据库
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print(f"创建新数据库: {db_path}")
    
    # 创建测试用例反向推导会话表
    cursor.execute("""
        CREATE TABLE test_case_reverse_sessions (
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
    print("✓ 创建 test_case_reverse_sessions 表")
    
    # 创建测试项表
    cursor.execute("""
        CREATE TABLE test_items (
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
    print("✓ 创建 test_items 表")
    
    # 创建生成日志表
    cursor.execute("""
        CREATE TABLE generation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id VARCHAR(50) NOT NULL,
            operation_type VARCHAR(50) NOT NULL,
            status VARCHAR(20) NOT NULL,
            message TEXT,
            execution_time REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ 创建 generation_logs 表")
    
    # 创建索引
    cursor.execute("CREATE INDEX idx_sessions_session_id ON test_case_reverse_sessions(session_id)")
    cursor.execute("CREATE INDEX idx_test_items_session_id ON test_items(session_id)")
    cursor.execute("CREATE INDEX idx_test_items_status ON test_items(generation_status)")
    cursor.execute("CREATE INDEX idx_logs_session_id ON generation_logs(session_id)")
    print("✓ 创建索引")
    
    # 提交更改
    conn.commit()
    conn.close()
    
    print("数据库初始化完成！")
    return True

if __name__ == "__main__":
    init_database() 