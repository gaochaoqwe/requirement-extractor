"""
项目管理模块的数据库初始化
"""
import logging
from ..databaseManage.dynamicDatabaseManage.db.database import engine, Base
from .models import Project

logger = logging.getLogger(__name__)


def init_project_db():
    """初始化项目管理模块的数据库表"""
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("项目管理模块数据库表创建成功")
        return True
    except Exception as e:
        logger.error(f"项目管理模块数据库表创建失败: {e}")
        return False


if __name__ == "__main__":
    init_project_db()