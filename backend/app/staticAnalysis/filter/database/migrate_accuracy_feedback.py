"""
数据库迁移脚本：为静态分析C/C++模块添加问题单准确率反馈字段

运行方式：
    python -m backend.app.staticAnalysis.filter.database.migrate_accuracy_feedback
"""

from sqlalchemy import create_engine, text, Column, String, DateTime
from sqlalchemy.orm import sessionmaker
from ..config.config import get_database_url
import sys

def migrate_add_problem_sheet_accuracy_fields():
    """
    为 static_analysis_sessions 表添加问题单准确率反馈字段
    """
    db_url = get_database_url()
    print(f"[迁移] 数据库URL: {db_url}")
    
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 检查字段是否已存在
        check_sql = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'static_analysis_sessions' 
        AND column_name = 'problem_sheet_accuracy_rate'
        """
        result = session.execute(text(check_sql))
        
        if result.fetchone():
            print("[迁移] 字段 'problem_sheet_accuracy_rate' 已存在，跳过")
        else:
            # 添加字段
            alter_sql = """
            ALTER TABLE static_analysis_sessions 
            ADD COLUMN problem_sheet_accuracy_rate VARCHAR(50),
            ADD COLUMN problem_sheet_feedback_at TIMESTAMP
            """
            session.execute(text(alter_sql))
            session.commit()
            print("[迁移] 成功添加字段：")
            print("  - problem_sheet_accuracy_rate (VARCHAR(50))")
            print("  - problem_sheet_feedback_at (TIMESTAMP)")
        
        print("[迁移] C/C++模块迁移完成")
        
    except Exception as e:
        session.rollback()
        print(f"[迁移] 错误: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    migrate_add_problem_sheet_accuracy_fields()
