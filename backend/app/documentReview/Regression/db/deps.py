"""
文档审查回归测试数据库依赖注入
"""
from typing import Generator
from sqlalchemy.orm import Session
from .database import SessionLocal

def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的依赖注入函数
    
    用于FastAPI路由的依赖注入：
    
    @router.get("/api/sessions")
    async def get_sessions(db: Session = Depends(get_db)):
        # 使用db进行数据库操作
        pass
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_with_commit() -> Generator[Session, None, None]:
    """
    获取数据库会话的依赖注入函数（自动提交）
    
    用于需要事务自动提交的场景：
    
    @router.post("/api/sessions")
    async def create_session(db: Session = Depends(get_db_with_commit)):
        # 使用db进行数据库操作，自动提交事务
        pass
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close() 