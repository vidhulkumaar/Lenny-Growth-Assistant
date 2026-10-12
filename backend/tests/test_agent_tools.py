import uuid
import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk
from app.services.agent.tools import RetrievalTool
from app.services.agent.types import RetrievalResult, Citation

def test_retrieval_tool_empty_query(db: Session):
    result = RetrievalTool.execute(db, query="   ", document_ids=[uuid.uuid4()])
    assert isinstance(result, RetrievalResult)
    assert result.is_empty is True
    assert "cannot be empty" in result.message
    assert len(result.chunks) == 0
    assert len(result.citations) == 0

def test_retrieval_tool_no_documents_selected(db: Session):
    result = RetrievalTool.execute(db, query="What is product growth?", document_ids=[])
    assert result.is_empty is True
    assert "No documents selected" in result.message
    assert len(result.chunks) == 0
    assert len(result.citations) == 0

def test_retrieval_tool_document_filtering(db: Session):
    # Create two documents with chunks
    doc1 = Document(filename="growth_loops.pdf", content_hash="hash_doc1", status="indexed")
    doc2 = Document(filename="retention_metrics.pdf", content_hash="hash_doc2", status="indexed")
    db.add_all([doc1, doc2])
    db.commit()

    chunk1 = DocumentChunk(
        document_id=doc1.id,
        chunk_index=0,
        page_number=3,
        content="Growth loops describe how a product acquires and retains users sustainably.",
        embedding=[0.01] * 384,
    )
    chunk2 = DocumentChunk(
        document_id=doc2.id,
        chunk_index=0,
        page_number=12,
        content="Cohort retention measures how many users return over time.",
        embedding=[0.01] * 384,
    )
    db.add_all([chunk1, chunk2])
    db.commit()

    # Filter only for doc1
    result = RetrievalTool.execute(db, query="growth loops", document_ids=[doc1.id], top_k=5)
    assert result.is_empty is False
    assert len(result.chunks) == 1
    assert result.chunks[0].document_id == str(doc1.id)
    assert result.chunks[0].filename == "growth_loops.pdf"
    assert result.chunks[0].page_number == 3

    # Ensure doc2 chunk is NOT returned
    doc_ids_returned = {c.document_id for c in result.chunks}
    assert str(doc2.id) not in doc_ids_returned

def test_retrieval_tool_citation_metadata(db: Session):
    doc = Document(filename="playbook.pdf", content_hash="hash_playbook", status="indexed")
    db.add(doc)
    db.commit()

    long_content = "Word " * 60  # > 160 characters
    chunk = DocumentChunk(
        document_id=doc.id,
        chunk_index=0,
        page_number=7,
        content=long_content,
        embedding=[0.02] * 384,
    )
    db.add(chunk)
    db.commit()

    result = RetrievalTool.execute(db, query="playbook", document_ids=[doc.id], top_k=1)
    assert len(result.citations) == 1
    citation = result.citations[0]
    assert citation.title == "playbook.pdf"
    assert citation.page_number == 7
    assert citation.source_key == str(doc.id)
    assert citation.excerpt.endswith("...")
    assert len(citation.excerpt) <= 165

def test_retrieval_tool_db_failure_recovery(db: Session):
    with patch("app.services.agent.tools.retrieve_relevant_chunks", side_effect=RuntimeError("Database connection lost")):
        result = RetrievalTool.execute(db, query="testing error", document_ids=[uuid.uuid4()])
        assert result.is_empty is True
        assert "Retrieval failed due to an internal database error" in result.message
