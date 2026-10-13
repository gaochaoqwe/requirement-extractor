"""
测试用例总结工具数据库初始化脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from backend.app.testTools.test_case_summary.models.models import Base
from backend.app.testTools.test_case_summary.config.config import DATABASE_URL

def init_database():
    """初始化数据库"""
    try:
        print("开始初始化测试用例总结工具数据库...")
        
        # 创建数据库引擎
        engine = create_engine(DATABASE_URL, echo=True)
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        print("✅ 测试用例总结工具数据库初始化成功！")
        print(f"数据库文件: {DATABASE_URL}")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1) 