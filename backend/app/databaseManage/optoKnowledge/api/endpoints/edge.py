from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import OptoKnowledgeEdge
from ...schemas.schemas import EdgeCreate, EdgeOut


router = APIRouter()


@router.post("/edge", response_model=EdgeOut)
def create_edge(payload: EdgeCreate, db: Session = Depends(get_db)):
    edge = OptoKnowledgeEdge(**payload.model_dump())
    db.add(edge)
    db.commit()
    db.refresh(edge)
    return EdgeOut.model_validate(edge)


@router.delete("/edge/{edge_id}")
def delete_edge(edge_id: UUID, db: Session = Depends(get_db)):
    edge = db.query(OptoKnowledgeEdge).filter(OptoKnowledgeEdge.id == edge_id).first()
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")

    db.delete(edge)
    db.commit()
    return {"success": True}
