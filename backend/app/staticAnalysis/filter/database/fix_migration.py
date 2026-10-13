"""
自动修复模块的库表初始化 / 迁移

幂等操作：
1. 创建 static_analysis_fix_tasks / static_analysis_fixes 两张表
2. 为 static_analysis_issues 补充 fix_status / fix_id 两列（老库升级用）

说明：models.Base.metadata.create_all 只建新表、不会给已存在的表补列，
因此老库需要这里显式 ALTER TABLE。
"""
import logging

logger = logging.getLogger("static_analysis_fix_migration")

_MIGRATION_DONE = False


def ensure_fix_schema(force: bool = False) -> bool:
    """确保修复相关库表结构就绪（幂等，可在启动时或首次调用修复接口时执行）"""
    global _MIGRATION_DONE
    if _MIGRATION_DONE and not force:
        return True

    try:
        from sqlalchemy import inspect, text
        from app.staticAnalysis.filter.database.database import get_engine
        from app.staticAnalysis.filter.models.models import (
            StaticAnalysisFixTask,
            StaticAnalysisFix,
        )

        engine = get_engine()

        # 1) 建新表（checkfirst 保证幂等）
        StaticAnalysisFixTask.__table__.create(bind=engine, checkfirst=True)
        StaticAnalysisFix.__table__.create(bind=engine, checkfirst=True)

        # 2) 给已有 issues 表补列
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        if 'static_analysis_issues' in table_names:
            existing_columns = {col['name'] for col in inspector.get_columns('static_analysis_issues')}
            with engine.begin() as conn:
                if 'fix_status' not in existing_columns:
                    conn.execute(text(
                        "ALTER TABLE static_analysis_issues ADD COLUMN fix_status INTEGER DEFAULT 0"
                    ))
                    logger.info("[修复迁移] 已为 static_analysis_issues 添加 fix_status 列")
                if 'fix_id' not in existing_columns:
                    conn.execute(text(
                        "ALTER TABLE static_analysis_issues ADD COLUMN fix_id INTEGER"
                    ))
                    logger.info("[修复迁移] 已为 static_analysis_issues 添加 fix_id 列")

        _MIGRATION_DONE = True
        logger.info("[修复迁移] 修复相关库表结构检查完成")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error(f"[修复迁移] 库表初始化失败: {exc}")
        return False
