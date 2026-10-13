"""
创建CWE规则数据库
"""
import sqlite3
from pathlib import Path
from cwe_rules_classified import CWE_ACCURATE_RULES, CWE_UNCERTAIN_RULES

# 数据库路径
db_path = Path(__file__).parent / "cwe_rules.db"

# 如果数据库已存在，删除它
if db_path.exists():
    db_path.unlink()
    print(f"✅ 已删除旧数据库: {db_path}")

# 创建新数据库
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print(f"📁 创建新数据库: {db_path}")

# 创建CWE规则表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS cwe_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_code TEXT UNIQUE NOT NULL,
        rule_name TEXT NOT NULL,
        accuracy_type TEXT NOT NULL,
        category TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

print("✅ 创建表: cwe_rules")

# 插入确定规则
print(f"\n📥 插入确定规则 ({len(CWE_ACCURATE_RULES)} 个)...")
for rule_code, rule_name, category in CWE_ACCURATE_RULES:
    cursor.execute('''
        INSERT INTO cwe_rules (rule_code, rule_name, accuracy_type, category, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (rule_code, rule_name, 'accurate', category, rule_name))

print(f"✅ 已插入 {len(CWE_ACCURATE_RULES)} 条确定规则")

# 插入不确定规则
print(f"\n📥 插入不确定规则 ({len(CWE_UNCERTAIN_RULES)} 个)...")
for rule_data in CWE_UNCERTAIN_RULES:
    if len(rule_data) == 3:
        rule_code, rule_name, category = rule_data
    else:
        rule_code, rule_name = rule_data
        category = "需要分析"
    cursor.execute('''
        INSERT INTO cwe_rules (rule_code, rule_name, accuracy_type, category, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (rule_code, rule_name, 'uncertain', category, rule_name))

print(f"✅ 已插入 {len(CWE_UNCERTAIN_RULES)} 条不确定规则")

# 提交事务
conn.commit()

# 验证数据
cursor.execute("SELECT COUNT(*) FROM cwe_rules")
total = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM cwe_rules WHERE accuracy_type = 'accurate'")
accurate_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM cwe_rules WHERE accuracy_type = 'uncertain'")
uncertain_count = cursor.fetchone()[0]

print(f"\n{'='*80}")
print(f"📊 数据库统计:")
print(f"  总规则数: {total}")
print(f"  确定规则: {accurate_count}")
print(f"  不确定规则: {uncertain_count}")
print(f"{'='*80}")

# 显示前10条记录
print(f"\n📋 前10条记录:")
cursor.execute("SELECT rule_code, rule_name, accuracy_type FROM cwe_rules LIMIT 10")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} ({row[2]})")

conn.close()

print(f"\n🎉 CWE规则数据库创建完成!")
print(f"📁 数据库文件: {db_path}")

