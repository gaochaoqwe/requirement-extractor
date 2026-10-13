"""
普通模式 FPGA 数据库：独立的 PostgreSQL 表（fpga_static_analysis_filter 数据库）

使用独立的4张 nm_fpga_ 表，与 normalModeC 完全分离
"""
from app.staticAnalysis.normalModeFpga.database.postgresql_database import (
    engine,
    SessionLocal,
    get_db,
    get_scoped_session,
    init_database as init_db,
)
from app.staticAnalysis.normalModeFpga.database.postgresql_models import (
    Base,
    AnalysisTask,
    AnalysisFile,
    AnalysisFunction,
    AnalysisProblem,
)
from app.staticAnalysis.normalModeFpga.database.repository import (
    TaskRepository,
    FileRepository,
    FunctionRepository,
    ProblemRepository,
)

# Repository工厂（兼容旧代码）
class RepositoryFactory:
    @staticmethod
    def get_repository(repo_class, db):
        return repo_class(db)

def get_repository(repo_class, db):
    """获取Repository实例"""
    return repo_class(db)

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "get_scoped_session",
    "init_db",
    "get_repository",
    "RepositoryFactory",
    "TaskRepository",
    "FileRepository",
    "FunctionRepository",
    "ProblemRepository",
    "AnalysisTask",
    "AnalysisFile",
    "AnalysisFunction",
    "AnalysisProblem",
]
