"""
数据库依赖项
"""
from typing import Generator
from sqlalchemy.orm import Session
from .database import SessionLocal

def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    
    Yields:
        Session: SQLAlchemy 数据库会话
        
    Example:
        ```python
        def some_endpoint(db: Session = Depends(get_db)):
            # 使用 db 进行数据库操作
            pass
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 导入仓库工厂
from .repository import RepositoryFactory

def get_repository(repo_name: str, db: Session):
    """
    获取指定名称的仓库实例
    
    Args:
        repo_name: 仓库名称，如 'task', 'file' 等
        db: 数据库会话
        
    Returns:
        对应的仓库实例
        
    Example:
        ```python
        def some_endpoint(
            task_repo: TaskRepository = Depends(Depends(get_repository('task')))
        ):
            # 使用 task_repo 进行数据库操作
            pass
        ```
    """
    def _get_repo(db: Session = Depends(get_db)):
        return RepositoryFactory.get_repository(repo_name, db)
        
    return _get_repo
