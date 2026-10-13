from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class NodeBase(BaseModel):
    domain: str
    type: str
    name: str
    summary: Optional[str] = None
    content_json: Optional[Dict[str, Any]] = None
    plain_text: Optional[str] = None
    tags: Optional[Any] = None


class NodeCreate(NodeBase):
    pass


class NodeUpdate(BaseModel):
    domain: Optional[str] = None
    type: Optional[str] = None
    name: Optional[str] = None
    summary: Optional[str] = None
    content_json: Optional[Dict[str, Any]] = None
    plain_text: Optional[str] = None
    tags: Optional[Any] = None


class NodeOut(NodeBase):
    id: UUID

    class Config:
        from_attributes = True


class EdgeBase(BaseModel):
    domain: str
    type: str
    source_id: UUID
    target_id: UUID
    props_json: Optional[Dict[str, Any]] = None


class EdgeCreate(EdgeBase):
    pass


class EdgeOut(EdgeBase):
    id: UUID

    class Config:
        from_attributes = True


class GraphOut(BaseModel):
    nodes: List[NodeOut] = Field(default_factory=list)
    edges: List[EdgeOut] = Field(default_factory=list)


class AssetOut(BaseModel):
    id: UUID
    node_id: UUID
    asset_type: str
    filename: str
    content_type: Optional[str] = None
    meta_json: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
