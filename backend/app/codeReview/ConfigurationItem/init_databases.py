"""
初始化PostgreSQL多数据库系统（独立脚本）

直接运行此脚本来初始化三个独立的PostgreSQL数据库
注意：运行前需要先设置环境变量（数据库连接信息）
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from db.database import init_database, check_database, get_connection_info
from db.database_chain import init_chain_database, check_chain_database, get_connection_info as get_chain_info
from db.database_feature import init_feature_database, check_feature_database, get_connection_info as get_feature_info

def main():
    """初始化所有PostgreSQL数据库"""
    print("=" * 70)
    print("  PostgreSQL多数据库系统初始化".center(70))
    print("=" * 70)
    print()
    
    # 检查环境变量
    required_vars = ["POSTGRES_HOST", "POSTGRES_USER", "POSTGRES_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("⚠️  警告：缺少以下环境变量：")
        for var in missing_vars:
            print(f"    - {var}")
        print()
        print("提示：请先设置环境变量或运行 init_postgresql.py 脚本")
        print()
        response = input("是否继续使用默认配置？(yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("已取消")
            sys.exit(0)
        print()
    
    try:
        # 1. 初始化主数据库（函数审查）
        print("[1/3] 初始化主数据库（函数审查）")
        print("-" * 70)
        init_database()
        print("✅ 主数据库初始化成功\n")
        
        # 2. 初始化链路审查数据库
        print("[2/3] 初始化链路审查数据库")
        print("-" * 70)
        init_chain_database()
        print("✅ 链路审查数据库初始化成功\n")
        
        # 3. 初始化功能审查数据库
        print("[3/3] 初始化功能审查数据库")
        print("-" * 70)
        init_feature_database()
        print("✅ 功能审查数据库初始化成功\n")
        
        print("=" * 70)
        print("  🎉 所有PostgreSQL数据库初始化完成！".center(70))
        print("=" * 70)
        
        # 显示数据库连接信息
        func_info = get_connection_info()
        chain_info = get_chain_info()
        feature_info = get_feature_info()
        
        print(f"\nPostgreSQL数据库连接信息:")
        print(f"  主机: {func_info['host']}:{func_info['port']}")
        print(f"  用户: {func_info['user']}")
        print(f"  数据库: {func_info['database']} (统一数据库)")
        print(f"  说明: 函数审查、链路审查、功能审查共享同一个数据库")
        print()
        
    except Exception as e:
        print(f"\n❌ PostgreSQL数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("提示：")
        print("1. 确保PostgreSQL服务已启动")
        print("2. 确保数据库已创建（运行 db/init_postgresql.py）")
        print("3. 确保环境变量配置正确")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()

