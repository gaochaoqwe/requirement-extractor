from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import OptoKnowledgeNode
from ...schemas.schemas import NodeCreate, NodeOut, NodeUpdate


router = APIRouter()


@router.post("/node", response_model=NodeOut)
def create_node(payload: NodeCreate, db: Session = Depends(get_db)):
    node = OptoKnowledgeNode(**payload.model_dump())
    db.add(node)
    db.commit()
    db.refresh(node)
    return NodeOut.model_validate(node)


@router.get("/node/{node_id}", response_model=NodeOut)
def get_node(node_id: UUID, db: Session = Depends(get_db)):
    node = db.query(OptoKnowledgeNode).filter(OptoKnowledgeNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return NodeOut.model_validate(node)


@router.put("/node/{node_id}", response_model=NodeOut)
def update_node(node_id: UUID, payload: NodeUpdate, db: Session = Depends(get_db)):
    node = db.query(OptoKnowledgeNode).filter(OptoKnowledgeNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(node, k, v)

    db.commit()
    db.refresh(node)
    return NodeOut.model_validate(node)


@router.delete("/node/{node_id}")
def delete_node(node_id: UUID, db: Session = Depends(get_db)):
    node = db.query(OptoKnowledgeNode).filter(OptoKnowledgeNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    db.delete(node)
    db.commit()
    return {"success": True}
