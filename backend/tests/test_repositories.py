import pytest
from sqlalchemy.exc import IntegrityError, DataError
from app.repositories.chat import ChatRepository
from app.repositories.transcript import TranscriptRepository
from app.models.chat import MessageRole

def test_chat_session_and_messages(db):
    chat_repo = ChatRepository(db)
    
    # Test session creation
    session = chat_repo.create_session(title="Test Session", metadata={"user_id": 123})
    assert session.id is not None
    assert session.title == "Test Session"
    assert session.session_metadata == {"user_id": 123}
    
    # Test adding messages
    msg1 = chat_repo.add_message(session.id, MessageRole.user, "Hello")
    msg2 = chat_repo.add_message(session.id, MessageRole.assistant, "Hi there")
    
    # Test listing messages
    messages = chat_repo.list_messages(session.id)
    assert len(messages) == 2
    assert messages[0].content == "Hello"
    assert messages[1].content == "Hi there"
    
    # Test session isolation
    session2 = chat_repo.create_session(title="Session 2")
    chat_repo.add_message(session2.id, MessageRole.user, "Isolated")
    
    messages1 = chat_repo.list_messages(session.id)
    messages2 = chat_repo.list_messages(session2.id)
    assert len(messages1) == 2
    assert len(messages2) == 1

def test_transcript_and_chunks(db):
    transcript_repo = TranscriptRepository(db)
    
    # Create transcript
    t1 = transcript_repo.create_or_update_transcript(
        source_key="pod_123",
        title="Podcast 123",
        content_hash="hash1",
        source_url="http://example.com/123"
    )
    assert t1.id is not None
    
    # Update transcript (duplicate source identifier)
    t1_updated = transcript_repo.create_or_update_transcript(
        source_key="pod_123",
        title="Podcast 123 Updated",
        content_hash="hash2"
    )
    assert t1.id == t1_updated.id
    assert t1_updated.title == "Podcast 123 Updated"
    
    # Add chunks
    dummy_embedding = [0.1] * 384
    chunk1 = transcript_repo.add_chunk(t1.id, 1, "Chunk 1", dummy_embedding)
    chunk2 = transcript_repo.add_chunk(t1.id, 2, "Chunk 2", dummy_embedding)
    
    chunks = transcript_repo.list_chunks(t1.id)
    assert len(chunks) == 2
    
    # Test duplicate chunk positions (constraint violation)
    with pytest.raises(IntegrityError):
        transcript_repo.add_chunk(t1.id, 1, "Duplicate Chunk 1", dummy_embedding)
        
def test_embedding_dimensions(db):
    transcript_repo = TranscriptRepository(db)
    
    t1 = transcript_repo.create_or_update_transcript(
        source_key="pod_456",
        title="Podcast 456",
        content_hash="hash3"
    )
    
    # Incorrect dimension embedding
    wrong_embedding = [0.1] * 128
    with pytest.raises(DataError):
        # Database should raise an error due to pgvector dim=384 constraint
        transcript_repo.add_chunk(t1.id, 1, "Wrong embedding chunk", wrong_embedding)
