import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.main import app
from app.db.session import get_db
from app.models.chat import ChatSession, ChatMessage, MessageRole
from app.models.artifact import Artifact
from app.models.document import Document, DocumentChunk
from app.models.transcript import Transcript, TranscriptChunk
from app.repositories.chat import ChatRepository
from app.repositories.artifact import ArtifactRepository


@pytest.fixture
def client(db: Session):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_delete_single_session_removes_messages_and_preserves_others(client: TestClient, db: Session):
    repo = ChatRepository(db)
    
    # Create session 1 with messages
    session1 = repo.create_session(title="Session 1 to Delete")
    repo.add_message(session1.id, MessageRole.user, "What is PMF?")
    repo.add_message(session1.id, MessageRole.assistant, "Product market fit is...")

    # Create session 2 with messages
    session2 = repo.create_session(title="Session 2 to Keep")
    repo.add_message(session2.id, MessageRole.user, "Explain retention.")
    repo.add_message(session2.id, MessageRole.assistant, "Retention is key.")

    # Delete session 1 via API
    resp = client.delete(f"/api/v1/chat/sessions/{session1.id}")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "deleted_session_id": str(session1.id)}

    # Verify session 1 is gone from DB
    assert repo.get_session(session1.id) is None
    assert len(repo.list_messages(session1.id)) == 0

    # Verify session 2 and its messages are untouched
    assert repo.get_session(session2.id) is not None
    s2_messages = repo.list_messages(session2.id)
    assert len(s2_messages) == 2
    assert s2_messages[0].content == "Explain retention."


def test_delete_session_safely_preserves_generated_artifacts(client: TestClient, db: Session):
    chat_repo = ChatRepository(db)
    art_repo = ArtifactRepository(db)

    # Create session with an artifact
    session = chat_repo.create_session(title="Session with Artifact")
    chat_repo.add_message(session.id, MessageRole.user, "Generate growth dashboard")
    
    artifact = art_repo.create_artifact(
        session_id=session.id,
        title="SaaS Growth Metrics",
        artifact_type="html",
        content="<div>Revenue Chart</div>"
    )
    artifact_id = artifact.id

    # Delete session
    resp = client.delete(f"/api/v1/chat/sessions/{session.id}")
    assert resp.status_code == 200

    # Verify session is deleted
    assert chat_repo.get_session(session.id) is None

    # CRITICAL: Verify artifact is NOT deleted (preserved in archive session)
    preserved_artifact = art_repo.get_artifact(artifact_id)
    assert preserved_artifact is not None
    assert preserved_artifact.title == "SaaS Growth Metrics"
    assert preserved_artifact.content == "<div>Revenue Chart</div>"

    # Verify accessible via general artifact endpoints
    art_resp = client.get(f"/api/v1/chat/artifacts/{artifact_id}")
    assert art_resp.status_code == 200
    assert art_resp.json()["title"] == "SaaS Growth Metrics"


def test_batch_delete_selected_sessions(client: TestClient, db: Session):
    repo = ChatRepository(db)
    s1 = repo.create_session(title="Batch Item 1")
    s2 = repo.create_session(title="Batch Item 2")
    s3 = repo.create_session(title="Batch Item 3 - Keep")

    resp = client.post("/api/v1/chat/sessions/batch-delete", json={
        "session_ids": [str(s1.id), str(s2.id)]
    })
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "deleted_count": 2}

    assert repo.get_session(s1.id) is None
    assert repo.get_session(s2.id) is None
    assert repo.get_session(s3.id) is not None


def test_clear_all_history_preserves_unrelated_documents_transcripts_and_artifacts(
    client: TestClient, db: Session
):
    chat_repo = ChatRepository(db)
    art_repo = ArtifactRepository(db)

    # 1. Seed unrelated Document & Chunk (must NOT be deleted)
    doc = Document(
        id=uuid.uuid4(),
        filename="founder_guide.pdf",
        content_hash="hash_doc_123",
        status="indexed"
    )
    db.add(doc)
    db.flush()

    chunk_vector = [0.01] * 384
    doc_chunk = DocumentChunk(
        document_id=doc.id,
        chunk_index=0,
        page_number=1,
        content="Chapter 1: Product-Market Fit",
        embedding=chunk_vector
    )
    db.add(doc_chunk)

    # 2. Seed unrelated Transcript & Chunk (must NOT be deleted)
    transcript = Transcript(
        id=uuid.uuid4(),
        source_key="brian_chesky_podcast",
        title="Brian Chesky on Designing Culture",
        content_hash="hash_tr_456"
    )
    db.add(transcript)
    db.flush()

    tr_chunk = TranscriptChunk(
        transcript_id=transcript.id,
        chunk_index=0,
        content="Brian explains 11-star experience",
        embedding=chunk_vector
    )
    db.add(tr_chunk)

    # 3. Seed Chat Sessions, Messages, and an Artifact
    s1 = chat_repo.create_session(title="User Chat 1")
    chat_repo.add_message(s1.id, MessageRole.user, "First query")
    chat_repo.add_message(s1.id, MessageRole.assistant, "First answer")

    s2 = chat_repo.create_session(title="User Chat 2")
    chat_repo.add_message(s2.id, MessageRole.user, "Second query")

    art = art_repo.create_artifact(
        session_id=s1.id,
        title="Key Retention Takeaways",
        artifact_type="markdown",
        content="# Retention Takeaways\n- Churn is vital."
    )
    art_id = art.id
    db.commit()

    # 4. Invoke clear_all_history via POST /api/v1/chat/history/clear
    resp = client.post("/api/v1/chat/history/clear")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["deleted_sessions"] >= 2
    assert data["deleted_messages"] >= 3

    # 5. VERIFY: User chat sessions list is now empty (system archive is hidden)
    sessions_resp = client.get("/api/v1/chat/sessions")
    assert sessions_resp.status_code == 200
    assert len(sessions_resp.json()) == 0

    # 6. VERIFY: All chat messages are gone
    all_msgs = db.execute(select(ChatMessage)).scalars().all()
    assert len(all_msgs) == 0

    # 7. CRITICAL VERIFICATION: Unrelated documents and chunks are 100% PRESERVED
    preserved_doc = db.execute(select(Document).where(Document.id == doc.id)).scalar_one_or_none()
    assert preserved_doc is not None
    assert preserved_doc.filename == "founder_guide.pdf"

    preserved_chunk = db.execute(
        select(DocumentChunk).where(DocumentChunk.document_id == doc.id)
    ).scalar_one_or_none()
    assert preserved_chunk is not None
    assert preserved_chunk.content == "Chapter 1: Product-Market Fit"

    # 8. CRITICAL VERIFICATION: Unrelated transcripts and chunks are 100% PRESERVED
    preserved_tr = db.execute(select(Transcript).where(Transcript.id == transcript.id)).scalar_one_or_none()
    assert preserved_tr is not None
    assert preserved_tr.title == "Brian Chesky on Designing Culture"

    preserved_tr_chunk = db.execute(
        select(TranscriptChunk).where(TranscriptChunk.transcript_id == transcript.id)
    ).scalar_one_or_none()
    assert preserved_tr_chunk is not None
    assert preserved_tr_chunk.content == "Brian explains 11-star experience"

    # 9. CRITICAL VERIFICATION: Generated artifact is 100% PRESERVED
    preserved_art = art_repo.get_artifact(art_id)
    assert preserved_art is not None
    assert preserved_art.title == "Key Retention Takeaways"


def test_delete_nonexistent_session_returns_404(client: TestClient):
    random_id = uuid.uuid4()
    resp = client.delete(f"/api/v1/chat/sessions/{random_id}")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()
