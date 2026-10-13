from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, schemas, models # Adjusted imports for current structure
from ...databaseManage.dynamicDatabaseManage.db.database import get_db # Use databaseManage module's get_db

router = APIRouter(
    prefix="/projects",
    # tags=["Projects"] # Tags are often better defined when including the router
)

@router.post("/", response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
def create_new_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """
    Create a new project.
    """
    import logging
    import sys
    import traceback
    
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG)
    
    try:
        logger.info(f"Attempting to create project with name: {project.name}")
        db_project_by_name = crud.get_project_by_name(db, name=project.name)
        
        if db_project_by_name:
            logger.warning(f"Project with name '{project.name}' already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project with name '{project.name}' already exists."
            )
            
        logger.info("Creating new project in database")
        return crud.create_project(db=db, project=project)
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating project: {str(e)}"
        )

@router.get("/", response_model=List[schemas.Project])
def read_all_projects(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """
    Retrieve all projects with pagination.
    """
    projects = crud.get_projects(db, skip=skip, limit=limit)
    return projects

@router.get("/{project_id}", response_model=schemas.Project)
def read_single_project(project_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a single project by its ID.
    """
    db_project = crud.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return db_project

@router.put("/{project_id}", response_model=schemas.Project)
def update_existing_project(
    project_id: int, project_update: schemas.ProjectUpdate, db: Session = Depends(get_db)
):
    """
    Update an existing project.
    """
    db_project = crud.get_project(db, project_id=project_id)
    if not db_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Check if new name conflicts with another project
    if project_update.name and project_update.name != db_project.name:
        conflicting_project = crud.get_project_by_name(db, name=project_update.name)
        if conflicting_project and conflicting_project.id != project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another project with name '{project_update.name}' already exists."
            )
            
    updated_project = crud.update_project(db=db, project_id=project_id, project_update=project_update)
    return updated_project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_project(project_id: int, db: Session = Depends(get_db)):
    """
    Delete an existing project.
    """
    success = crud.delete_project(db=db, project_id=project_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return # No content to return for 204
