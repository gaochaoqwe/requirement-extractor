from collections import deque
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...db.models import OptoKnowledgeEdge, OptoKnowledgeNode
from ...schemas.schemas import GraphOut, NodeOut, EdgeOut


router = APIRouter()


@router.get("/graph", response_model=GraphOut)
def get_graph(
    domain: str = Query(..., description="turret/countermeasure/optoradar/pod"),
    root_id: Optional[UUID] = Query(None),
    depth: int = Query(2, ge=0, le=3),
    db: Session = Depends(get_db),
):
    base_nodes_q = db.query(OptoKnowledgeNode).filter(OptoKnowledgeNode.domain == domain)

    if root_id is None:
        nodes = base_nodes_q.all()
        node_ids = [n.id for n in nodes]
        edges = (
            db.query(OptoKnowledgeEdge)
            .filter(OptoKnowledgeEdge.domain == domain)
            .filter(OptoKnowledgeEdge.source_id.in_(node_ids))
            .filter(OptoKnowledgeEdge.target_id.in_(node_ids))
            .all()
        )
        return GraphOut(
            nodes=[NodeOut.model_validate(n) for n in nodes],
            edges=[EdgeOut.model_validate(e) for e in edges],
        )

    # BFS 按跳数取子图（无向遍历，边仍保持有向）
    visited = set([root_id])
    q = deque([(root_id, 0)])

    while q:
        nid, d = q.popleft()
        if d >= depth:
            continue

        neighbors = (
            db.query(OptoKnowledgeEdge)
            .filter(OptoKnowledgeEdge.domain == domain)
            .filter((OptoKnowledgeEdge.source_id == nid) | (OptoKnowledgeEdge.target_id == nid))
            .all()
        )

        for e in neighbors:
            other = e.target_id if e.source_id == nid else e.source_id
            if other not in visited:
                visited.add(other)
                q.append((other, d + 1))

    nodes = base_nodes_q.filter(OptoKnowledgeNode.id.in_(list(visited))).all()
    edges = (
        db.query(OptoKnowledgeEdge)
        .filter(OptoKnowledgeEdge.domain == domain)
        .filter(OptoKnowledgeEdge.source_id.in_(list(visited)))
        .filter(OptoKnowledgeEdge.target_id.in_(list(visited)))
        .all()
    )

    return GraphOut(
        nodes=[NodeOut.model_validate(n) for n in nodes],
        edges=[EdgeOut.model_validate(e) for e in edges],
    )
