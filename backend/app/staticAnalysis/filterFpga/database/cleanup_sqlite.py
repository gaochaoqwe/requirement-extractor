"""
清理SQLite相关文件和代码

⚠️ 警告：此脚本会删除所有SQLite数据库文件和SQLite相关代码！
使用前请确保：
1. PostgreSQL数据库已正常工作
2. 数据已完全迁移
3. 已测试所有功能正常

使用方法：
cd backend/app/staticAnalysis/filter/database
python cleanup_sqlite.py --yes
"""
import os
import sys
import argparse
from pathlib import Path

# 当前脚本所在目录
CURRENT_DIR = Path(__file__).parent

# 要删除的SQLite数据库文件
SQLITE_DB_FILES = [
    "static_analysis_filter.db",
    "static_analysis_filter.db-shm",
    "static_analysis_filter.db-wal",
    "gjb8114_rules.db",
    "cwe_rules.db",
]

# 要删除的SQLite代码文件（可选）
SQLITE_CODE_FILES = [
    "rules_database.py",        # SQLite版GJB规则数据库
    "cwe_rules_database.py",    # SQLite版CWE规则数据库
]

# 可选删除的环境变量脚本
OPTIONAL_FILES = [
    "set_postgresql_env.bat",
    "set_postgresql_env.ps1",
]


def cleanup_sqlite_files(auto_yes=False, delete_code=False, delete_optional=False):
    """清理SQLite相关文件"""
    try:
        print("="*70)
        print("  SQLite清理脚本".center(70))
        print("  静态分析过滤工具".center(70))
        print("="*70)
        print()
        
        # 统计要删除的文件
        db_files_to_delete = []
        code_files_to_delete = []
        optional_files_to_delete = []
        
        print("检查要删除的文件...")
        print()
        
        # 检查数据库文件
        print("SQLite数据库文件：")
        for filename in SQLITE_DB_FILES:
            filepath = CURRENT_DIR / filename
            if filepath.exists():
                size = filepath.stat().st_size / 1024  # KB
                db_files_to_delete.append((filepath, size))
                print(f"  ✓ {filename} ({size:.2f} KB)")
            else:
                print(f"  - {filename} (不存在)")
        print()
        
        # 检查代码文件
        if delete_code:
            print("SQLite代码文件：")
            for filename in SQLITE_CODE_FILES:
                filepath = CURRENT_DIR / filename
                if filepath.exists():
                    size = filepath.stat().st_size / 1024  # KB
                    code_files_to_delete.append((filepath, size))
                    print(f"  ✓ {filename} ({size:.2f} KB)")
                else:
                    print(f"  - {filename} (不存在)")
            print()
        else:
            print("SQLite代码文件：跳过（使用 --delete-code 参数可删除）")
            print()
        
        # 检查可选文件
        if delete_optional:
            print("可选文件：")
            for filename in OPTIONAL_FILES:
                filepath = CURRENT_DIR / filename
                if filepath.exists():
                    size = filepath.stat().st_size / 1024  # KB
                    optional_files_to_delete.append((filepath, size))
                    print(f"  ✓ {filename} ({size:.2f} KB)")
                else:
                    print(f"  - {filename} (不存在)")
            print()
        else:
            print("可选文件：跳过（使用 --delete-optional 参数可删除）")
            print()
        
        # 统计
        total_files = len(db_files_to_delete) + len(code_files_to_delete) + len(optional_files_to_delete)
        total_size = sum(size for _, size in db_files_to_delete + code_files_to_delete + optional_files_to_delete)
        
        if total_files == 0:
            print("没有找到需要删除的文件！")
            return True
        
        print(f"总计：{total_files} 个文件，{total_size:.2f} KB")
        print()
        
        if not auto_yes:
            print("⚠️  警告：将删除以上所有文件！")
            response = input("确认删除？(yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("\n已取消删除")
                return False
        else:
            print("自动确认模式：继续删除...")
        
        print()
        
        # 删除数据库文件
        deleted_count = 0
        if db_files_to_delete:
            print("[1/3] 删除SQLite数据库文件...")
            for filepath, size in db_files_to_delete:
                try:
                    filepath.unlink()
                    print(f"    OK 已删除: {filepath.name}")
                    deleted_count += 1
                except Exception as e:
                    print(f"    ERROR 删除失败 {filepath.name}: {e}")
            print()
        
        # 删除代码文件
        if code_files_to_delete:
            print("[2/3] 删除SQLite代码文件...")
            for filepath, size in code_files_to_delete:
                try:
                    filepath.unlink()
                    print(f"    OK 已删除: {filepath.name}")
                    deleted_count += 1
                except Exception as e:
                    print(f"    ERROR 删除失败 {filepath.name}: {e}")
            print()
            
            # 提示需要修改factory文件
            print("    ⚠️  注意：已删除SQLite代码文件，需要修改 rules_database_factory.py")
            print("    移除SQLite的fallback逻辑，仅保留PostgreSQL版本")
            print()
        
        # 删除可选文件
        if optional_files_to_delete:
            print("[3/3] 删除可选文件...")
            for filepath, size in optional_files_to_delete:
                try:
                    filepath.unlink()
                    print(f"    OK 已删除: {filepath.name}")
                    deleted_count += 1
                except Exception as e:
                    print(f"    ERROR 删除失败 {filepath.name}: {e}")
            print()
        
        print("="*70)
        print(f"  OK 清理完成，共删除 {deleted_count} 个文件".center(70))
        print("="*70)
        print()
        
        if code_files_to_delete:
            print("后续步骤：")
            print("1. 修改 rules_database_factory.py，移除SQLite fallback")
            print("2. 测试所有功能是否正常")
            print()
        
        return True
        
    except Exception as e:
        print(f"\nERROR 清理失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='清理SQLite相关文件')
    parser.add_argument('--yes', '-y', action='store_true', help='自动确认，跳过交互式提示')
    parser.add_argument('--delete-code', action='store_true', help='同时删除SQLite代码文件')
    parser.add_argument('--delete-optional', action='store_true', help='同时删除可选文件（环境变量脚本）')
    args = parser.parse_args()
    
    success = cleanup_sqlite_files(
        auto_yes=args.yes,
        delete_code=args.delete_code,
        delete_optional=args.delete_optional
    )
    sys.exit(0 if success else 1)

