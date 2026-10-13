"""数据库依赖项"""
from typing import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from .database import SessionLocal
from .repository import RepositoryFactory


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_repository(repo_name: str, db: Session):
    def _get_repo(db: Session = Depends(get_db)):
        return RepositoryFactory.get_repository(repo_name, db)

    return _get_repo
