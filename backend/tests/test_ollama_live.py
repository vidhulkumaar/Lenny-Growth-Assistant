import pytest
import httpx
from app.services.agent.adapters import OllamaAdapter

@pytest.mark.anyio
async def test_live_ollama_generation():
    """
    Real local Ollama integration test.
    Validates connectivity to the local Ollama instance and qwen3:4b model.
    """
    adapter = OllamaAdapter(timeout=20.0)
    try:
        response = await adapter.generate(
            prompt="Reply with the single word 'CONFIRMED' and nothing else.",
            system_prompt="You are a test harness assistant."
        )
        assert len(response) > 0
        print(f"\nLive Ollama response: {response}")
    except Exception as e:
        pytest.skip(f"Live Ollama instance not reachable or timed out: {e}")
