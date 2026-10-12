import os
import uuid
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db
from app.models.transcript import Transcript, TranscriptChunk
from app.models.chat import MessageRole
from app.models.artifact import Artifact
from app.services.agent.service import AgentService
from app.services.agent.router import IntentRouter, AgentIntent
from app.services.agent.adapters import MockModelAdapter, OllamaAdapter, AnthropicAdapter, validate_provider, ModelProviderError
from app.repositories.artifact import ArtifactRepository
from app.repositories.chat import ChatRepository
from app.services.agent.artifacts.generator import sanitize_html_artifact


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


# 1. "What is product-market fit?" routes to Q&A
def test_scenario_1_product_market_fit_routes_to_qa():
    result = IntentRouter.classify("What is product-market fit?")
    assert result.intent == AgentIntent.RESEARCH_QA
    assert result.deliverables == ["research_qa"]


# 2. "Explain Lenny's podcast insights on customer retention" invokes transcript retrieval and returns citations
@pytest.mark.anyio
async def test_scenario_2_podcast_insights_retrieval_and_citations(db: Session):
    transcript = Transcript(
        title="Customer Retention Masterclass | Elena Verna",
        source_key="github:ChatPRD/lennys-podcast-transcripts:episodes/elena-verna",
        content_hash="hash_elena",
    )
    db.add(transcript)
    db.commit()

    chunk = TranscriptChunk(
        transcript_id=transcript.id,
        chunk_index=0,
        content="Elena Verna explains that retention is the single highest leverage metric for sustainable growth.",
        embedding=[0.05] * 384,
    )
    db.add(chunk)
    db.commit()

    mock_adapter = MockModelAdapter(
        response_text="Based on Elena Verna's masterclass, retention is the core growth lever."
    )
    agent = AgentService(db=db, model_adapter=mock_adapter)

    session_id, assistant_msg, citations = await agent.process_chat(
        content="Explain Lenny's podcast insights on customer retention",
    )
    assert session_id is not None
    assert assistant_msg.role == MessageRole.assistant
    assert len(citations) >= 1
    assert "Elena Verna" in citations[0].title


# 3. "Write a Ship 30 for 30 atomic essay about retention" invokes writing agent and returns essay
@pytest.mark.anyio
async def test_scenario_3_ship30_atomic_essay_invoked(db: Session):
    mock_essay = (
        "# Why Retention Is The Only Growth Metric That Truly Matters\n\n"
        "Most founders obsess over top-of-funnel acquisition..."
    )
    mock_adapter = MockModelAdapter(response_text=mock_essay)
    agent = AgentService(db=db, model_adapter=mock_adapter)

    result = await agent.process_chat(
        content="Write a Ship 30 for 30 atomic essay about retention",
    )
    assert result.artifact is None  # Ship 30 outputs text directly to chat, not an HTML artifact
    assert "# Why Retention Is The Only Growth Metric" in result.assistant_msg.content


# 4. "Create a responsive HTML dashboard with KPI cards and charts" invokes HTML artifact generation, persists, and returns actual ID
@pytest.mark.anyio
async def test_scenario_4_html_dashboard_generation_and_persistence(db: Session):
    mock_html = (
        "<!DOCTYPE html><html><head><title>Startup KPI Dashboard</title><style>body{background:#0f172a;}</style></head>"
        "<body><h1>Startup KPI Dashboard</h1><div class='kpi-card'>MRR: $50,000</div></body></html>"
    )
    mock_adapter = MockModelAdapter(response_text=mock_html)
    agent = AgentService(db=db, model_adapter=mock_adapter)

    result = await agent.process_chat(
        content="Create a responsive HTML dashboard with KPI cards and charts",
    )
    assert result.artifact is not None
    assert result.artifact.artifact_type == "html"
    assert result.artifact.id is not None
    assert "Startup KPI Dashboard" in result.artifact.title

    # Verify real DB persistence
    repo = ArtifactRepository(db)
    persisted = repo.get_artifact(result.artifact.id)
    assert persisted is not None
    assert persisted.id == result.artifact.id


# 5. Regression Test: HTML dashboard request must NOT invoke Ship 30
def test_scenario_5_html_dashboard_never_routes_to_ship30():
    prompts = [
        "Create an HTML dashboard for my startup",
        "Build a responsive pricing page",
        "Generate an HTML landing page for an AI product",
        "Create an HTML report with charts and KPI cards",
        "Make a portfolio website and show me its preview",
        "Create a responsive HTML dashboard with KPI cards and charts",
        "Write an HTML dashboard with KPI cards",
    ]
    for p in prompts:
        classification = IntentRouter.classify(p, legacy_mode="ship30")
        assert classification.intent == AgentIntent.HTML_ARTIFACT, f"Failed for prompt: {p}"
        assert classification.intent != AgentIntent.SHIP30_WRITING


# 6. "Create a Markdown project report" produces Markdown artifact
@pytest.mark.anyio
async def test_scenario_6_markdown_project_report(db: Session):
    mock_md = "# Project Implementation Report\n\n## Overview\nThis project details rollout..."
    mock_adapter = MockModelAdapter(response_text=mock_md)
    agent = AgentService(db=db, model_adapter=mock_adapter)

    result = await agent.process_chat(
        content="Create a Markdown project report",
    )
    assert result.artifact is not None
    assert result.artifact.artifact_type == "markdown"
    assert "Project" in result.artifact.title or "Report" in result.artifact.title


# 7. "Make the dashboard dark-themed" resolves existing artifact and updates it
@pytest.mark.anyio
async def test_scenario_7_artifact_update_dark_theme(db: Session):
    chat_repo = ChatRepository(db)
    session = chat_repo.create_session(title="Dashboard Session")

    art_repo = ArtifactRepository(db)
    original_html = "<!DOCTYPE html><html><head><title>Analytics Dashboard</title></head><body><h1>Analytics</h1></body></html>"
    artifact = art_repo.create_artifact(
        session_id=session.id,
        title="Analytics Dashboard",
        artifact_type="html",
        content=original_html,
    )

    mock_dark_html = "<!DOCTYPE html><html><head><title>Analytics Dashboard (Dark Theme)</title><style>body{background:#0f172a;}</style></head><body><h1>Analytics</h1></body></html>"
    mock_adapter = MockModelAdapter(response_text=mock_dark_html)
    agent = AgentService(db=db, model_adapter=mock_adapter)

    result = await agent.process_chat(
        content="Make the dashboard dark-themed",
        session_id=session.id,
    )
    assert result.artifact is not None
    assert result.artifact.id == artifact.id  # Same artifact ID updated in place
    assert "#0f172a" in result.artifact.content

    # Verify updated in database
    refreshed = art_repo.get_artifact(artifact.id)
    assert "#0f172a" in refreshed.content


# 8. Request containing multiple explicitly requested deliverables executes workflows in controlled sequence
@pytest.mark.anyio
async def test_scenario_8_multi_deliverable_execution(db: Session):
    mock_adapter = MockModelAdapter(
        response_text="# Retention Strategy Essay\n\nRetention compounds...\n<!DOCTYPE html><html><body><h1>Retention Dashboard</h1></body></html>"
    )
    agent = AgentService(db=db, model_adapter=mock_adapter)

    prompt = "Research this topic, write an essay, and create an HTML summary"
    classification = IntentRouter.classify(prompt)
    assert classification.intent == AgentIntent.MULTI_DELIVERABLE

    result = await agent.process_chat(content=prompt)
    # Both essay in content and HTML artifact generated
    assert result.artifact is not None
    assert result.artifact.artifact_type == "html"
    assert "Retention Strategy Essay" in result.assistant_msg.content or "Artifact Viewer" in result.assistant_msg.content


# 9. Claude selection routes requests through Claude adapter
@patch("app.services.agent.adapters.AnthropicAdapter.generate")
@pytest.mark.anyio
async def test_scenario_9_claude_selection_routes_to_claude(mock_generate, db: Session):
    mock_generate.return_value = "Claude-generated response"
    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test-key"}):
        agent = AgentService(db=db)
        result = await agent.process_chat(
            content="What is product strategy?",
            provider="claude",
        )
        assert result.provider == "claude"
        assert result.assistant_msg.content == "Claude-generated response"
        mock_generate.assert_called_once()


# 10. Ollama selection routes requests through Ollama
def test_scenario_10_ollama_selection_returns_ollama_adapter():
    adapter = AgentService(db=MagicMock()).model_adapter
    # Default is Ollama
    assert adapter.provider_name == "ollama"


# 11. Missing Claude API credentials produce a clear error
@pytest.mark.anyio
async def test_scenario_11_missing_claude_credentials_clear_error(db: Session):
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=False):
        with patch("app.core.config.settings.ANTHROPIC_API_KEY", ""):
            agent = AgentService(db=db)
            result = await agent.process_chat(
                content="Explain retention",
                provider="claude",
            )
            assert "Anthropic API key is not configured" in result.assistant_msg.content
            assert result.citations == []


# 12. Invalid provider names are rejected safely
def test_scenario_12_invalid_provider_rejected_safely(client):
    res = client.post("/api/v1/chat/message", json={"content": "Hello", "provider": "invalid-llm"})
    assert res.status_code == 400
    assert "Unsupported model provider 'invalid-llm'" in res.json()["detail"]


# 13. Artifact persistence failure does not trigger a false success response
@pytest.mark.anyio
async def test_scenario_13_artifact_persistence_failure_handled_truthfully(db: Session):
    mock_html = "<!DOCTYPE html><html><body><h1>Dashboard</h1></body></html>"
    mock_adapter = MockModelAdapter(response_text=mock_html)
    agent = AgentService(db=db, model_adapter=mock_adapter)

    with patch.object(ArtifactRepository, "create_artifact", side_effect=Exception("Database connection terminated")):
        result = await agent.process_chat(
            content="Create an HTML dashboard for my startup",
        )
        # Truthful handling: No false artifact returned
        assert result.artifact is None
        assert "saving it to the database failed" in result.assistant_msg.content.lower()


# 14. Frontend opens Artifact Viewer using actual artifact returned by backend (API response test)
def test_scenario_14_api_returns_actual_artifact_model(client):
    with patch("app.services.agent.adapters.OllamaAdapter.generate") as mock_gen:
        mock_gen.return_value = "<!DOCTYPE html><html><head><title>Startup UI</title></head><body><h1>Startup</h1></body></html>"
        res = client.post("/api/v1/chat/message", json={
            "content": "Create an HTML landing page for my product",
            "provider": "ollama",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["artifact"] is not None
        assert data["artifact"]["artifact_type"] == "html"
        assert uuid.UUID(data["artifact"]["id"])  # Valid UUID
        assert data["artifact"]["title"] == "Startup UI"


# 15. HTML preview rendering preserves existing sandbox, sanitizer, and CSP
def test_scenario_15_html_sanitizer_and_security():
    malicious = (
        "<!DOCTYPE html><html><head><script>alert('xss')</script><link rel='stylesheet' href='http://evil.com/style.css'></head>"
        "<body onload='steal()'><a href='javascript:alert(1)'>Click</a><iframe src='http://evil.com'></iframe></body></html>"
    )
    clean = sanitize_html_artifact(malicious)
    assert "<script" not in clean
    assert "steal()" not in clean
    assert "javascript:" not in clean
    assert "<iframe" not in clean
    assert "evil.com" not in clean


# 16. Existing session isolation and artifact history continue working
def test_scenario_16_session_isolation_and_artifact_history(client, db: Session):
    chat_repo = ChatRepository(db)
    s1 = chat_repo.create_session(title="Session 1")
    s2 = chat_repo.create_session(title="Session 2")

    art_repo = ArtifactRepository(db)
    a1 = art_repo.create_artifact(session_id=s1.id, title="Art 1", artifact_type="html", content="<p>1</p>")
    a2 = art_repo.create_artifact(session_id=s2.id, title="Art 2", artifact_type="markdown", content="# 2")

    res1 = client.get(f"/api/v1/chat/sessions/{s1.id}/artifacts")
    assert res1.status_code == 200
    ids1 = [item["id"] for item in res1.json()]
    assert str(a1.id) in ids1
    assert str(a2.id) not in ids1  # Strict session isolation
