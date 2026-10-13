"""
数据库依赖项

注意：此文件为避免循环导入，在运行时动态导入SessionLocal
"""
from typing import Generator
from sqlalchemy.orm import Session

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
    # 运行时导入，避免循环导入
    from ..config_database import SessionLocal
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
