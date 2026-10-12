import uuid
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict, Field

from app.db.session import get_db
from app.repositories.chat import ChatRepository
from app.repositories.artifact import ArtifactRepository
from app.models.chat import ChatSession
from app.services.agent.service import AgentService
from app.services.agent.types import Citation
from app.services.agent.artifacts import (
    ArtifactModel,
    ArtifactGenerationInput,
    ArtifactGenerator,
)

router = APIRouter()

from app.services.agent.adapters import (
    get_providers_info,
    validate_provider,
    get_model_adapter,
)

class CitationModel(BaseModel):
    source_key: str
    title: str
    excerpt: Optional[str] = None
    page_number: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class ChatMessageModel(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    created_at: Optional[datetime.datetime] = None
    citations: Optional[List[CitationModel]] = None
    provider: Optional[str] = Field(None, description="Active LLM provider used ('ollama' or 'claude')")
    model: Optional[str] = Field(None, description="Model identifier used")

    model_config = ConfigDict(from_attributes=True)

class ChatRequest(BaseModel):
    content: str = Field(..., min_length=1, description="Message text from user")
    session_id: Optional[uuid.UUID] = Field(None, description="Optional existing session ID")
    document_ids: List[uuid.UUID] = Field(default_factory=list, description="IDs of documents to ground retrieval on")
    mode: Optional[str] = Field("chat", description="Interaction mode: 'chat', 'ship30', or 'artifact'")
    provider: Optional[str] = Field(None, description="Requested LLM provider: 'ollama' (Local) or 'claude' (Cloud)")
    model: Optional[str] = Field(None, description="Optional specific model override")
    temperature: Optional[float] = Field(None, description="Optional sampling temperature (e.g. 0.0 - 1.0)")
    writing_options: Optional[dict] = Field(None, description="Optional options for Ship 30 for 30 writing skill")
    artifact_options: Optional[dict] = Field(None, description="Optional options for Artifact generation")

class ChatResponse(BaseModel):
    session_id: uuid.UUID
    response: ChatMessageModel
    artifact: Optional[ArtifactModel] = None
    provider: str = Field("ollama", description="Active LLM provider used")
    model: str = Field("qwen3:4b", description="Model identifier used")

class SessionResponse(BaseModel):
    id: uuid.UUID
    title: Optional[str]
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class BatchDeleteSessionsRequest(BaseModel):
    session_ids: List[uuid.UUID] = Field(..., min_length=1, description="List of chat session UUIDs to delete")

@router.get("/providers")
def get_providers():
    """
    Returns available LLM providers (Ollama Local vs Claude Cloud)
    and their configuration/availability status.
    """
    return get_providers_info()

@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Delegate user request to the AgentService, which handles session management,
    retrieval tool execution, model synthesis, artifact generation, and message persistence.
    Routes execution to the requested LLM provider (Ollama or Claude).
    """
    agent = AgentService(db=db)
    try:
        # Validate requested provider
        if request.provider:
            validate_provider(request.provider)

        chat_result = await agent.process_chat(
            content=request.content,
            session_id=request.session_id,
            document_ids=request.document_ids,
            mode=request.mode or "chat",
            provider=request.provider,
            model=request.model,
            temperature=request.temperature,
            writing_options=request.writing_options,
            artifact_options=request.artifact_options,
        )
    except ValueError as e:
        if "Unsupported model provider" in str(e):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent processing failed: {str(e)}"
        )

    session_id = chat_result.session_id
    assistant_msg = chat_result.assistant_msg
    citations = chat_result.citations
    artifact_record = chat_result.artifact
    used_provider = getattr(chat_result, "provider", "ollama")
    used_model = getattr(chat_result, "model", "qwen3:4b")

    citation_models = [
        CitationModel(
            source_key=c.source_key,
            title=c.title,
            page_number=c.page_number,
            excerpt=c.excerpt,
        )
        for c in citations
    ] if citations else None

    artifact_model = None
    if artifact_record:
        artifact_model = ArtifactModel.model_validate(artifact_record)

    return ChatResponse(
        session_id=session_id,
        response=ChatMessageModel(
            id=assistant_msg.id,
            role=assistant_msg.role.value if hasattr(assistant_msg.role, "value") else str(assistant_msg.role),
            content=assistant_msg.content,
            created_at=assistant_msg.created_at,
            citations=citation_models,
            provider=used_provider,
            model=used_model,
        ),
        artifact=artifact_model,
        provider=used_provider,
        model=used_model,
    )

@router.get("/sessions", response_model=List[SessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    """List all available user chat sessions ordered by most recently updated."""
    sessions = db.execute(select(ChatSession).order_by(ChatSession.updated_at.desc())).scalars().all()
    return [s for s in sessions if not (s.session_metadata and s.session_metadata.get("system"))]

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageModel])
def get_session_messages(session_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieve message history and persistent citations for a specific chat session.
    Enforces session isolation.
    """
    repo = ChatRepository(db)
    session = repo.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{session_id}' not found."
        )

    messages = repo.list_messages(session_id)
    result = []
    for m in messages:
        c_models = None
        if m.citations and isinstance(m.citations, list):
            c_models = [
                CitationModel(
                    source_key=item.get("source_key", ""),
                    title=item.get("title", ""),
                    page_number=item.get("page_number"),
                    excerpt=item.get("excerpt"),
                )
                for item in m.citations
            ]
        result.append(ChatMessageModel(
            id=m.id,
            role=m.role.value if hasattr(m.role, "value") else str(m.role),
            content=m.content,
            created_at=m.created_at,
            citations=c_models,
        ))
    return result

@router.get("/sessions/{session_id}/artifacts", response_model=List[ArtifactModel])
def get_session_artifacts(session_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieve all artifacts generated for a specific chat session.
    Strictly isolated to the requested session.
    """
    chat_repo = ChatRepository(db)
    session = chat_repo.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{session_id}' not found."
        )

    artifact_repo = ArtifactRepository(db)
    artifacts = artifact_repo.list_session_artifacts(session_id)
    return [ArtifactModel.model_validate(a) for a in artifacts]

@router.get("/artifacts/{artifact_id}", response_model=ArtifactModel)
def get_artifact(artifact_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieve a specific artifact by its unique ID.
    """
    artifact_repo = ArtifactRepository(db)
    artifact = artifact_repo.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact '{artifact_id}' not found."
        )
    return ArtifactModel.model_validate(artifact)

@router.post("/sessions/{session_id}/artifacts", response_model=ArtifactModel)
async def create_session_artifact(
    session_id: uuid.UUID,
    input_data: ArtifactGenerationInput,
    db: Session = Depends(get_db),
):
    """
    Directly generate and attach an artifact to an existing chat session.
    """
    chat_repo = ChatRepository(db)
    session = chat_repo.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{session_id}' not found."
        )

    agent = AgentService(db=db)
    adapter = agent.model_adapter
    if input_data.provider or input_data.model:
        adapter = get_model_adapter(provider=input_data.provider, model=input_data.model)

    gen_result = await ArtifactGenerator.generate_artifact(
        db=db,
        model_adapter=adapter,
        input_data=input_data,
    )

    artifact_repo = ArtifactRepository(db)
    citations_data = [c.model_dump() for c in gen_result.citations] if gen_result.citations else None
    artifact = artifact_repo.create_artifact(
        session_id=session_id,
        title=gen_result.title,
        artifact_type=gen_result.artifact_type,
        content=gen_result.content,
        citations=citations_data,
    )
    return ArtifactModel.model_validate(artifact)

@router.delete("/sessions/{session_id}")
def delete_session(session_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Safely delete a specific chat conversation and its messages.
    Preserves generated artifacts and unrelated records.
    """
    repo = ChatRepository(db)
    success = repo.delete_session(session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session '{session_id}' not found."
        )
    return {"status": "ok", "deleted_session_id": str(session_id)}

@router.post("/sessions/batch-delete")
def batch_delete_sessions(request: BatchDeleteSessionsRequest, db: Session = Depends(get_db)):
    """
    Delete multiple selected conversations while preserving artifacts and unrelated records.
    """
    repo = ChatRepository(db)
    deleted_count = repo.delete_sessions(request.session_ids)
    return {"status": "ok", "deleted_count": deleted_count}

@router.post("/history/clear")
@router.delete("/history")
def clear_all_history(db: Session = Depends(get_db)):
    """
    Permanently clear all chat conversations and search message history.
    Preserves all uploaded documents, transcripts, embeddings, and generated artifacts.
    """
    repo = ChatRepository(db)
    result = repo.clear_all_history()
    return {"status": "ok", **result}

@router.get("/artifacts", response_model=List[ArtifactModel])
def list_artifacts(db: Session = Depends(get_db)):
    """
    Retrieve all generated artifacts across the system.
    """
    repo = ArtifactRepository(db)
    artifacts = repo.list_all_artifacts()
    return [ArtifactModel.model_validate(a) for a in artifacts]


