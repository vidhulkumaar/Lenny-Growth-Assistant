import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
from app.db.base import Base

def utc_now():
    return datetime.now(timezone.utc)

class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_key = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    source_url = Column(String, nullable=True)
    source_path = Column(String, nullable=True)
    content_hash = Column(String, nullable=False)
    ingested_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    chunks = relationship(
        "TranscriptChunk", 
        back_populates="transcript", 
        cascade="all, delete-orphan",
        order_by="TranscriptChunk.chunk_index"
    )

class TranscriptChunk(Base):
    __tablename__ = "transcript_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transcript_id = Column(UUID(as_uuid=True), ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    # Ensure the embedding dimensions match sentence-transformers/all-MiniLM-L6-v2 (384)
    embedding = Column(Vector(384), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    transcript = relationship("Transcript", back_populates="chunks")

    __table_args__ = (
        UniqueConstraint("transcript_id", "chunk_index", name="uq_transcript_chunk_index"),
        # Create an HNSW index for fast cosine distance search on pgvector
        Index("ix_transcript_chunks_embedding", "embedding", postgresql_using="hnsw", postgresql_with={"m": 16, "ef_construction": 64}, postgresql_ops={"embedding": "vector_cosine_ops"}),
    )
