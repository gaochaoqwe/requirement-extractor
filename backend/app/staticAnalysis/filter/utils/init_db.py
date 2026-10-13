"""
数据库初始化脚本
用于创建鉴定测评表单辅助工具的数据库表
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.staticAnalysis.filter.database.database import init_database
from app.staticAnalysis.filter.models.models import Base, StaticAnalysisSession, StaticAnalysisIssue
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("assessment_db_init")

def main():
    """主函数：初始化数据库"""
    try:
        logger.info("开始初始化鉴定测评表单辅助工具数据库...")

        # 初始化数据库表
        init_database()

        logger.info("数据库初始化完成！")
        logger.info("创建的表：")
        logger.info("- assessment_sessions: 评估会话表")
        logger.info("- requirement_items: 需求项表")
        logger.info("- generation_logs: 生成日志表")

        return True

    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 