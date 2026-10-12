import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base

def utc_now():
    return datetime.now(timezone.utc)

class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    artifact_type = Column(String, nullable=False)  # "markdown" or "html"
    content = Column(Text, nullable=False)
    citations = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    session = relationship("ChatSession", back_populates="artifacts")

    __table_args__ = (
        Index("ix_artifacts_session_id", "session_id"),
        Index("ix_artifacts_session_id_created_at", "session_id", "created_at"),
    )
