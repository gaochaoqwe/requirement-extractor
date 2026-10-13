"""兼容 shim：canonical 实现在 normalModeC.database。"""
from app.staticAnalysis.normalModeC.database import (  # noqa: F401
    Base,
    get_db,
    init_db,
    get_repository,
    RepositoryFactory,
    TaskRepository,
    FileRepository,
    FunctionRepository,
    ProblemRepository,
)

__all__ = [
    "Base",
    "get_db",
    "init_db",
    "get_repository",
    "RepositoryFactory",
    "TaskRepository",
    "FileRepository",
    "FunctionRepository",
    "ProblemRepository",
]
