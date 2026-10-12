import os
import uuid
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import get_db
from app.services.agent.adapters import (
    validate_provider,
    get_model_adapter,
    get_providers_info,
    OllamaAdapter,
    AnthropicAdapter,
    ModelProviderError,
)

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

# 1. Validation tests
def test_validate_provider_valid():
    assert validate_provider("ollama") == "ollama"
    assert validate_provider("OLLAMA") == "ollama"
    assert validate_provider("claude") == "claude"
    assert validate_provider("anthropic") == "claude"
    assert validate_provider("Claude") == "claude"

def test_validate_provider_invalid():
    with pytest.raises(ValueError) as exc:
        validate_provider("gpt-4")
    assert "Unsupported model provider 'gpt-4'" in str(exc.value)

# 2. Adapter factory tests
def test_factory_returns_ollama():
    adapter = get_model_adapter(provider="ollama", model="qwen3:4b")
    assert isinstance(adapter, OllamaAdapter)
    assert adapter.provider_name == "ollama"
    assert adapter.model_name == "qwen3:4b"

def test_factory_returns_claude():
    adapter = get_model_adapter(provider="claude", model="claude-3-5-sonnet-20241022")
    assert isinstance(adapter, AnthropicAdapter)
    assert adapter.provider_name == "claude"
    assert adapter.model_name == "claude-3-5-sonnet-20241022"

# 3. Missing API key handling
@pytest.mark.asyncio
async def test_anthropic_missing_key_raises_model_provider_error():
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=False):
        with patch("app.core.config.settings.ANTHROPIC_API_KEY", ""):
            adapter = AnthropicAdapter(api_key="", model_name="claude-3-5-sonnet-20241022")
            with pytest.raises(ModelProviderError) as exc:
                await adapter.generate("Test prompt")
            assert "Anthropic API key is not configured" in str(exc.value)
            assert "switch to Ollama (Local)" in str(exc.value)

# 4. Anthropic Adapter execution with mock SDK
@pytest.mark.asyncio
async def test_anthropic_adapter_generates_response():
    mock_response = MagicMock()
    content_block = MagicMock()
    content_block.text = "This is a high quality response from Claude 3.5 Sonnet."
    mock_response.content = [content_block]

    mock_client = AsyncMock()
    mock_client.messages = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    with patch("app.services.agent.adapters.AsyncAnthropic", return_value=mock_client):
        adapter = AnthropicAdapter(api_key="sk-ant-test-key", model_name="claude-3-5-sonnet-20241022", temperature=0.2)
        result = await adapter.generate("Summarize retention strategies", top_p=0.9)

        assert result == "This is a high quality response from Claude 3.5 Sonnet."
        mock_client.messages.create.assert_awaited_once_with(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            messages=[{"role": "user", "content": "Summarize retention strategies"}],
            extra_body={"temperature": 0.2, "top_p": 0.9},
        )

# 5. Providers info endpoint
def test_get_providers_endpoint(client: TestClient):
    resp = client.get("/api/v1/chat/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert "active_provider" in data
    assert "providers" in data
    provider_ids = [p["id"] for p in data["providers"]]
    assert "ollama" in provider_ids
    assert "claude" in provider_ids

# 6. Chat API routing with provider selection
def test_chat_message_routes_to_ollama(client: TestClient):
    with patch(
        "app.services.agent.adapters.OllamaAdapter.generate",
        new_callable=AsyncMock,
        return_value="Answer from Ollama model."
    ):
        resp = client.post("/api/v1/chat/message", json={
            "content": "What is PLG?",
            "provider": "ollama"
        })

    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "ollama"
    assert data["response"]["provider"] == "ollama"
    assert "Answer from Ollama model" in data["response"]["content"]

def test_chat_message_routes_to_claude(client: TestClient):
    with patch(
        "app.services.agent.adapters.AnthropicAdapter.generate",
        new_callable=AsyncMock,
        return_value="Answer synthesized by Claude AI."
    ):
        resp = client.post("/api/v1/chat/message", json={
            "content": "Explain product market fit.",
            "provider": "claude"
        })

    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "claude"
    assert data["response"]["provider"] == "claude"
    assert "Answer synthesized by Claude AI" in data["response"]["content"]

def test_chat_message_rejects_invalid_provider(client: TestClient):
    resp = client.post("/api/v1/chat/message", json={
        "content": "Hello",
        "provider": "non-existent-provider"
    })
    assert resp.status_code == 400
    assert "Unsupported model provider" in resp.json()["detail"]

def test_chat_message_graceful_missing_claude_key(client: TestClient):
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=False):
        with patch("app.core.config.settings.ANTHROPIC_API_KEY", ""):
            resp = client.post("/api/v1/chat/message", json={
                "content": "Draft an essay",
                "provider": "claude"
            })

    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "claude"
    assert "Anthropic API key is not configured" in data["response"]["content"]
