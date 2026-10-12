from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class Citation(BaseModel):
    source_key: str = Field(..., description="Document identifier or unique source key")
    title: str = Field(..., description="Filename or title of the source document")
    page_number: Optional[int] = Field(None, description="Page number of the citation (1-indexed)")
    excerpt: Optional[str] = Field(None, description="Verbatim text excerpt supporting the citation")

class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page_number: Optional[int] = None
    content: str

class RetrievalInput(BaseModel):
    query: str = Field(..., min_length=1, description="The query string to search for in documents")
    document_ids: List[UUID] = Field(default_factory=list, description="List of document UUIDs to filter retrieval")
    top_k: int = Field(default=5, ge=1, le=20, description="Maximum number of relevant chunks to retrieve")

class RetrievalResult(BaseModel):
    query: str
    chunks: List[RetrievedChunk] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    is_empty: bool = True
    message: str = ""

class AgentResponse(BaseModel):
    content: str
    citations: Optional[List[Citation]] = None
    tool_calls_made: List[str] = Field(default_factory=list)
    grounded: bool = False
