import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.services.agent.types import Citation

class ArtifactModel(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    title: str
    artifact_type: str  # "markdown" or "html"
    content: str
    created_at: datetime
    citations: Optional[List[Citation]] = None

    model_config = ConfigDict(from_attributes=True)

class ArtifactGenerationInput(BaseModel):
    prompt: str = Field(..., min_length=2, description="Instruction or topic for the artifact")
    artifact_type: Optional[str] = Field("markdown", description="Type of artifact: 'markdown' or 'html'")
    title: Optional[str] = Field(None, description="Optional custom title for the artifact")
    document_ids: List[uuid.UUID] = Field(default_factory=list, description="Document IDs to ground the artifact upon")

class ArtifactGenerationResult(BaseModel):
    title: str
    artifact_type: str
    content: str
    citations: List[Citation] = Field(default_factory=list)
    grounded: bool = False
    is_empty_evidence: bool = False
