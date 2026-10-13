from sqlalchemy.orm import Session
from . import models, schemas
from typing import List, Optional

# --- Project CRUD Operations ---
def get_project(db: Session, project_id: int) -> Optional[models.Project]:
    return db.query(models.Project).filter(models.Project.id == project_id).first()

def get_project_by_name(db: Session, name: str) -> Optional[models.Project]:
    return db.query(models.Project).filter(models.Project.name == name).first()

def get_projects(
    db: Session, skip: int = 0, limit: int = 100
) -> List[models.Project]:
    return db.query(models.Project).order_by(models.Project.id.desc()).offset(skip).limit(limit).all()

def create_project(db: Session, project: schemas.ProjectCreate) -> models.Project:
    db_project = models.Project(
        name=project.name
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def update_project(
    db: Session, project_id: int, project_update: schemas.ProjectUpdate
) -> Optional[models.Project]:
    db_project = get_project(db, project_id)
    if not db_project:
        return None
    
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_project, field, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project

def delete_project(db: Session, project_id: int) -> bool:
    db_project = get_project(db, project_id)
    if not db_project:
        return False
    
    db.delete(db_project)
    db.commit()
    return True

