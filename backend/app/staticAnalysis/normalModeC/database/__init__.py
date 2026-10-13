"""普通模式 C 数据库（任务/文件/问题 SQLite）。规则库由 services.rules 按需加载。"""
from .database import get_scoped_session, init_db, engine, SessionLocal, Base
from .deps import get_db, get_repository
from .repository import (
    RepositoryFactory,
    TaskRepository,
    FileRepository,
    FunctionRepository,
    ProblemRepository,
)
from .models import AnalysisTask, AnalysisFile, AnalysisFunction, AnalysisProblem

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
