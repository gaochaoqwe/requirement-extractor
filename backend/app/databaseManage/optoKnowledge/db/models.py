import uuid

from sqlalchemy import Column, DateTime, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func

from .database import Base


class OptoKnowledgeNode(Base):
    __tablename__ = "opto_knowledge_node"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain = Column(String(50), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    summary = Column(Text, nullable=True)

    content_json = Column(JSONB, nullable=True)
    plain_text = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class OptoKnowledgeEdge(Base):
    __tablename__ = "opto_knowledge_edge"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    domain = Column(String(50), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)

    source_id = Column(UUID(as_uuid=True), ForeignKey("opto_knowledge_node.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id = Column(UUID(as_uuid=True), ForeignKey("opto_knowledge_node.id", ondelete="CASCADE"), nullable=False, index=True)

    props_json = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OptoKnowledgeAsset(Base):
    __tablename__ = "opto_knowledge_asset"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = Column(UUID(as_uuid=True), ForeignKey("opto_knowledge_node.id", ondelete="CASCADE"), nullable=False, index=True)

    asset_type = Column(String(50), nullable=False)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(100), nullable=True)
    file_path = Column(Text, nullable=False)

    meta_json = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
