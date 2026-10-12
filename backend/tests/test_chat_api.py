import uuid
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import get_db
from app.models.chat import MessageRole
from app.repositories.chat import ChatRepository
from app.services.agent.types import Citation

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

def test_chat_message_endpoint_creates_session(client: TestClient, db: Session):
    with patch(
        "app.services.agent.adapters.OllamaAdapter.generate",
        new_callable=AsyncMock,
        return_value="Growth loops generate sustainable user compounding."
    ):
        resp = client.post("/api/v1/chat/message", json={
            "content": "What are growth loops?",
            "document_ids": []
        })

    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert data["response"]["role"] == "assistant"
    assert "Growth loops" in data["response"]["content"]

def test_chat_sessions_endpoint(client: TestClient, db: Session):
    repo = ChatRepository(db)
    session = repo.create_session(title="Test Session Alpha")

    resp = client.get("/api/v1/chat/sessions")
    assert resp.status_code == 200
    sessions = resp.json()
    assert any(s["id"] == str(session.id) for s in sessions)

def test_get_session_messages_endpoint(client: TestClient, db: Session):
    repo = ChatRepository(db)
    session = repo.create_session(title="Persistent Chat")
    
    citations_data = [{
        "source_key": "doc-uuid-1",
        "title": "guide.pdf",
        "page_number": 2,
        "excerpt": "Key insight here."
    }]
    repo.add_message(session.id, MessageRole.user, "Question 1")
    repo.add_message(session.id, MessageRole.assistant, "Answer 1", citations=citations_data)

    resp = client.get(f"/api/v1/chat/sessions/{session.id}/messages")
    assert resp.status_code == 200
    messages = resp.json()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Question 1"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Answer 1"
    assert len(messages[1]["citations"]) == 1
    assert messages[1]["citations"][0]["page_number"] == 2
    assert messages[1]["citations"][0]["title"] == "guide.pdf"

def test_chat_invalid_session_404(client: TestClient, db: Session):
    fake_id = str(uuid.uuid4())
    resp = client.post("/api/v1/chat/message", json={
        "content": "Hello",
        "session_id": fake_id,
        "document_ids": []
    })
    assert resp.status_code == 404
