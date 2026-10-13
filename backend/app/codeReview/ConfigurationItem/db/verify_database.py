"""
验证PostgreSQL数据库表是否创建成功
"""
import psycopg2

# 数据库配置
POSTGRES_HOST = "localhost"
POSTGRES_PORT = 5432
POSTGRES_DB = "code_review"
POSTGRES_USER = "code_review"
POSTGRES_PASSWORD = "123456"

def verify_database():
    """验证数据库和表"""
    try:
        print("="*70)
        print("  PostgreSQL数据库验证".center(70))
        print("="*70)
        print()
        
        print(f"正在连接到数据库 {POSTGRES_DB}...")
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB
        )
        cursor = conn.cursor()
        print("OK 连接成功\n")
        
        # 查询所有表
        print("查询数据库中的表...")
        cursor.execute("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n找到 {len(tables)} 个表：")
            print("-"*70)
            expected_tables = [
                'code_review_tasks',
                'code_review_files',
                'code_review_functions',
                'code_review_problems',
                'chain_review_problems',
                'features',
                'feature_review_problems'
            ]
            
            for table in tables:
                table_name = table[0]
                status = "OK" if table_name in expected_tables else "EXTRA"
                print(f"  [{status}] {table_name}")
            
            print("-"*70)
            
            # 检查是否所有期望的表都存在
            actual_tables = [t[0] for t in tables]
            missing_tables = [t for t in expected_tables if t not in actual_tables]
            
            if missing_tables:
                print(f"\nWARNING 缺少以下表：")
                for t in missing_tables:
                    print(f"  - {t}")
            else:
                print("\nOK 所有期望的表都已创建！")
            
            # 查询每个表的行数
            print("\n表记录统计：")
            print("-"*70)
            for table in actual_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table:30s} : {count} 条记录")
            print("-"*70)
            
        else:
            print("WARNING 数据库中没有表！")
        
        cursor.close()
        conn.close()
        
        print("\n="*70)
        print("  验证完成".center(70))
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\nERROR: {e}")
        return False

if __name__ == "__main__":
    verify_database()

