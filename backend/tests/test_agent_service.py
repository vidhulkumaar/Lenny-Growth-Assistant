import uuid
import pytest
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk
from app.models.chat import MessageRole
from app.services.agent.service import AgentService
from app.services.agent.adapters import MockModelAdapter, ModelProviderError
from app.repositories.chat import ChatRepository

@pytest.mark.anyio
async def test_agent_invocation_with_grounded_answer(db: Session):
    # Setup document and chunk
    doc = Document(filename="metrics_guide.pdf", content_hash="hash_metrics", status="indexed")
    db.add(doc)
    db.commit()

    chunk = DocumentChunk(
        document_id=doc.id,
        chunk_index=0,
        page_number=4,
        content="North Star Metric for Airbnb is Nights Booked.",
        embedding=[0.05] * 384,
    )
    db.add(chunk)
    db.commit()

    mock_adapter = MockModelAdapter(
        response_text="According to [metrics_guide.pdf, Page 4], Airbnb's North Star Metric is Nights Booked."
    )
    agent = AgentService(db=db, model_adapter=mock_adapter)

    session_id, assistant_msg, citations = await agent.process_chat(
        content="What is Airbnb's North Star Metric?",
        document_ids=[doc.id],
    )

    assert session_id is not None
    assert assistant_msg.role == MessageRole.assistant
    assert "metrics_guide.pdf" in assistant_msg.content
    assert len(citations) == 1
    assert citations[0].title == "metrics_guide.pdf"
    assert citations[0].page_number == 4

    # Verify database persistence
    chat_repo = ChatRepository(db)
    messages = chat_repo.list_messages(session_id)
    assert len(messages) == 2  # user + assistant
    assert messages[0].role == MessageRole.user
    assert messages[1].role == MessageRole.assistant
    assert messages[1].citations is not None
    assert messages[1].citations[0]["page_number"] == 4

@pytest.mark.anyio
async def test_agent_insufficient_evidence_unanswerable(db: Session):
    doc = Document(filename="empty_notes.pdf", content_hash="hash_empty", status="indexed")
    db.add(doc)
    db.commit()

    mock_adapter = MockModelAdapter(response_text="Should not be called")
    agent = AgentService(db=db, model_adapter=mock_adapter)

    # Question about topic with no chunks in database
    session_id, assistant_msg, citations = await agent.process_chat(
        content="What is the mascot for this project?",
        document_ids=[doc.id],
    )

    # Must give explicit insufficient evidence response and NO fabricated citations
    assert "found no relevant content or evidence" in assistant_msg.content
    assert len(citations) == 0

@pytest.mark.anyio
async def test_agent_no_documents_selected(db: Session):
    mock_adapter = MockModelAdapter(
        response_text="Product-market fit is achieved when retention curves flatten out."
    )
    agent = AgentService(db=db, model_adapter=mock_adapter)

    session_id, assistant_msg, citations = await agent.process_chat(
        content="How do you define PMF?",
        document_ids=[],
    )

    assert session_id is not None
    assert "Product-market fit" in assistant_msg.content
    assert len(citations) == 0

@pytest.mark.anyio
async def test_agent_model_unavailable_recovery(db: Session):
    mock_adapter = MockModelAdapter()
    mock_adapter.should_fail = True
    mock_adapter.failure_reason = "Could not connect to the local Ollama instance."

    agent = AgentService(db=db, model_adapter=mock_adapter)

    session_id, assistant_msg, citations = await agent.process_chat(
        content="Tell me about growth loops",
        document_ids=[],
    )

    assert "Could not connect to the local Ollama instance" in assistant_msg.content
    assert len(citations) == 0

    # Ensure message was saved so the conversation remains intact
    chat_repo = ChatRepository(db)
    messages = chat_repo.list_messages(session_id)
    assert len(messages) == 2

@pytest.mark.anyio
async def test_agent_model_timeout_recovery(db: Session):
    mock_adapter = MockModelAdapter()
    mock_adapter.should_fail = True
    mock_adapter.failure_reason = "The language model timed out after 60.0 seconds."

    agent = AgentService(db=db, model_adapter=mock_adapter)

    session_id, assistant_msg, citations = await agent.process_chat(
        content="Complex analytical query",
        document_ids=[],
    )

    assert "timed out after 60.0 seconds" in assistant_msg.content
    assert len(citations) == 0

@pytest.mark.anyio
async def test_session_isolation_and_persistence(db: Session):
    mock_adapter = MockModelAdapter(response_text="Session-specific answer")
    agent = AgentService(db=db, model_adapter=mock_adapter)

    # Session 1
    session_id_1, msg1, _ = await agent.process_chat(
        content="Hello in session 1",
        document_ids=[],
    )

    # Session 2
    session_id_2, msg2, _ = await agent.process_chat(
        content="Hello in session 2",
        document_ids=[],
    )

    assert session_id_1 != session_id_2

    chat_repo = ChatRepository(db)
    messages_1 = chat_repo.list_messages(session_id_1)
    messages_2 = chat_repo.list_messages(session_id_2)

    assert len(messages_1) == 2
    assert len(messages_2) == 2

    assert messages_1[0].content == "Hello in session 1"
    assert messages_2[0].content == "Hello in session 2"

    # Verify no message from Session 2 appears in Session 1
    session_1_contents = [m.content for m in messages_1]
    assert "Hello in session 2" not in session_1_contents
