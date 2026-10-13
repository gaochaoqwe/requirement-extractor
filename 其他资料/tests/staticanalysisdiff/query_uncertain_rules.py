"""
查询数据库中的不确定规则名称
"""
import sqlite3
import sys
from pathlib import Path

# 数据库路径
DB_PATH = Path(__file__).parent.parent.parent / "app" / "testTools" / "static_analysis_filter" / "database" / "gjb8114_rules.db"

print(f"数据库路径: {DB_PATH}")
print(f"数据库存在: {DB_PATH.exists()}\n")

if not DB_PATH.exists():
    print("❌ 数据库文件不存在！")
    sys.exit(1)

try:
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # 查询不确定规则
    cursor.execute("""
        SELECT rule_code, rule_name, rule_description, accuracy_type 
        FROM gjb8114_rules 
        WHERE accuracy_type = 'uncertain'
        ORDER BY rule_code
    """)
    
    rules = cursor.fetchall()
    
    print(f"找到 {len(rules)} 个不确定规则:\n")
    print("="*100)
    
    for idx, (code, name, desc, acc_type) in enumerate(rules, 1):
        print(f"{idx}. 规则编号: {code}")
        print(f"   规则名称: {name}")
        print(f"   规则描述: {desc[:100] if desc else 'N/A'}...")
        print(f"   准确度类型: {acc_type}")
        print("-"*100)
    
    conn.close()
    
except Exception as e:
    print(f"❌ 错误: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

