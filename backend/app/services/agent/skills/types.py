from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID

class WritingSkillInput(BaseModel):
    topic: str = Field(..., min_length=2, description="The topic, question, or rough idea to write about")
    audience: Optional[str] = Field("Product Managers, Founders, and Growth Operators", description="Target readership")
    objective: Optional[str] = Field("Provide clear, actionable takeaways and lessons", description="The key goal of the piece")
    format_style: Optional[str] = Field("Atomic Essay", description="Writing format (Atomic Essay, Framework Breakdown, Actionable Steps)")
    tone: Optional[str] = Field("Clear, compelling, direct, and actionable", description="Voice and tone")
    document_ids: List[UUID] = Field(default_factory=list, description="Documents to use as evidence sources")

class WritingSkillResult(BaseModel):
    content: str
    grounded: bool
    is_empty_evidence: bool = False
