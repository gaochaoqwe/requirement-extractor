"""
从SQLite迁移规则数据到PostgreSQL

功能：
1. 从gjb8114_rules.db迁移GJB8114规则和关键字
2. 从cwe_rules.db迁移CWE规则
"""
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
current_file = Path(__file__).resolve()
db_dir = current_file.parent
filter_dir = db_dir.parent
static_analysis_dir = filter_dir.parent
app_dir = static_analysis_dir.parent
backend_dir = app_dir.parent
project_root = backend_dir.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.app.staticAnalysis.filter.database.postgresql_database import get_db_session
from backend.app.staticAnalysis.filter.database.postgresql_models import GJB8114Rule, GJB8114RuleKeyword, CWERule
from backend.app.staticAnalysis.filter.database.rule_texts import (
    build_gjb8114_texts,
    build_cwe_texts,
)

# SQLite数据库路径
GJB_DB_PATH = db_dir / "gjb8114_rules.db"
CWE_DB_PATH = db_dir / "cwe_rules.db"


def migrate_gjb_rules():
    """迁移GJB8114规则数据"""
    if not GJB_DB_PATH.exists():
        print(f"    ERROR: GJB8114规则数据库不存在: {GJB_DB_PATH}")
        return 0
    
    try:
        # 连接SQLite数据库
        sqlite_conn = sqlite3.connect(str(GJB_DB_PATH))
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()
        
        # 获取PostgreSQL会话
        pg_session = get_db_session()
        
        # 检查是否已有数据
        existing_count = pg_session.query(GJB8114Rule).count()
        if existing_count > 0:
            print(f"    WARNING: PostgreSQL中已有 {existing_count} 条GJB8114规则，跳过迁移")
            sqlite_conn.close()
            pg_session.close()
            return existing_count
        
        # 迁移规则
        sqlite_cursor.execute("SELECT * FROM gjb8114_rules")
        rules = sqlite_cursor.fetchall()
        
        rule_count = 0
        for row in rules:
            row_dict = dict(row)
            texts = build_gjb8114_texts(row_dict)
            rule = GJB8114Rule(
                rule_code=row_dict.get('rule_code'),
                rule_name=row_dict.get('rule_name'),
                rule_description=row_dict.get('rule_description'),
                category=row_dict.get('category'),
                accuracy_type=row_dict.get('accuracy_type'),
                analysis_complexity=row_dict.get('analysis_complexity'),
                detection_method=row_dict.get('detection_method'),
                problem_name=texts['problem_name'],
                requirement_description=texts['requirement_description'],
                impact_analysis=texts['impact_analysis'],
                improvement_suggestion=texts['improvement_suggestion'],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            pg_session.add(rule)
            rule_count += 1
        
        # 迁移关键字
        sqlite_cursor.execute("SELECT * FROM rule_keywords")
        keywords = sqlite_cursor.fetchall()
        
        keyword_count = 0
        for row in keywords:
            keyword = GJB8114RuleKeyword(
                rule_code=row['rule_code'],
                keyword=row['keyword'],
                keyword_type=row['keyword_type']
            )
            pg_session.add(keyword)
            keyword_count += 1
        
        # 提交
        pg_session.commit()
        
        # 关闭连接
        sqlite_conn.close()
        pg_session.close()
        
        print(f"       - 规则: {rule_count} 条")
        print(f"       - 关键字: {keyword_count} 条")
        
        return rule_count
        
    except Exception as e:
        print(f"    ERROR: GJB8114规则迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return 0


def migrate_cwe_rules():
    """迁移CWE规则数据"""
    if not CWE_DB_PATH.exists():
        print(f"    ERROR: CWE规则数据库不存在: {CWE_DB_PATH}")
        return 0
    
    try:
        # 连接SQLite数据库
        sqlite_conn = sqlite3.connect(str(CWE_DB_PATH))
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()
        
        # 获取PostgreSQL会话
        pg_session = get_db_session()
        
        # 检查是否已有数据
        existing_count = pg_session.query(CWERule).count()
        if existing_count > 0:
            print(f"    WARNING: PostgreSQL中已有 {existing_count} 条CWE规则，跳过迁移")
            sqlite_conn.close()
            pg_session.close()
            return existing_count
        
        # 迁移规则
        sqlite_cursor.execute("SELECT * FROM cwe_rules")
        rules = sqlite_cursor.fetchall()
        
        rule_count = 0
        for row in rules:
            row_dict = dict(row)
            texts = build_cwe_texts(row_dict)
            rule = CWERule(
                rule_code=row_dict.get('rule_code'),
                rule_name=row_dict.get('rule_name'),
                accuracy_type=row_dict.get('accuracy_type'),
                category=row_dict.get('category') if 'category' in row_dict else None,
                description=row_dict.get('description') if 'description' in row_dict else None,
                problem_name=texts['problem_name'],
                requirement_description=texts['requirement_description'],
                impact_analysis=texts['impact_analysis'],
                improvement_suggestion=texts['improvement_suggestion'],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            pg_session.add(rule)
            rule_count += 1
        
        # 提交
        pg_session.commit()
        
        # 关闭连接
        sqlite_conn.close()
        pg_session.close()
        
        return rule_count
        
    except Exception as e:
        print(f"    ERROR: CWE规则迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return 0


def main():
    """主函数"""
    print("="*70)
    print("规则数据迁移工具")
    print("从SQLite迁移到PostgreSQL")
    print("="*70)
    print()
    
    print("[1/2] 迁移GJB8114规则...")
    gjb_count = migrate_gjb_rules()
    print(f"    OK 完成，共迁移 {gjb_count} 条规则")
    print()
    
    print("[2/2] 迁移CWE规则...")
    cwe_count = migrate_cwe_rules()
    print(f"    OK 完成，共迁移 {cwe_count} 条规则")
    print()
    
    print("="*70)
    print("迁移完成！")
    print("="*70)


if __name__ == "__main__":
    main()

