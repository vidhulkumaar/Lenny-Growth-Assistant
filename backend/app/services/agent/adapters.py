import re
import logging
import httpx
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

class ModelProviderError(Exception):
    """Raised when an LLM provider fails or is unreachable."""
    pass

class BaseModelAdapter(ABC):
    """Abstract model adapter interface for agent generation."""

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a completion for the given prompt and optional system prompt."""
        pass

class OllamaAdapter(BaseModelAdapter):
    """
    Adapter for local Ollama instance (default: qwen3:4b).
    Preserves 100% offline local demo functionality.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model_name = model_name or settings.AGENT_MODEL
        self.timeout = timeout or settings.AGENT_TIMEOUT_SECONDS

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        url = f"{self.base_url}/api/generate"
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 512,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    raw = data.get("response", "").strip()
                    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()
                    return cleaned
                else:
                    logger.error(f"Ollama returned error {response.status_code}: {response.text}")
                    raise ModelProviderError(
                        f"Ollama server returned an error (HTTP {response.status_code}). "
                        "Please verify the model is installed with 'ollama run "
                        f"{self.model_name}'."
                    )
        except httpx.ConnectError as e:
            logger.error(f"Could not connect to Ollama at {self.base_url}: {e}")
            raise ModelProviderError(
                "Could not connect to the local Ollama instance. "
                f"Please ensure Ollama is running at {self.base_url}."
            )
        except httpx.TimeoutException as e:
            logger.error(f"Timeout while waiting for Ollama ({self.timeout}s): {e}")
            raise ModelProviderError(
                f"The language model timed out after {self.timeout} seconds. "
                "The system may be under heavy load."
            )
        except Exception as e:
            if isinstance(e, ModelProviderError):
                raise
            logger.error(f"Unexpected error communicating with Ollama: {e}")
            raise ModelProviderError(f"Unexpected error contacting model provider: {str(e)}")

class AnthropicAdapter(BaseModelAdapter):
    """
    Adapter for Anthropic Claude API when cloud provider is configured.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model_name = model_name or "claude-3-5-sonnet-20241022"
        self.timeout = timeout or settings.AGENT_TIMEOUT_SECONDS

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.api_key:
            raise ModelProviderError("Anthropic API key is not configured in environment.")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                )
                if response.status_code == 200:
                    data = response.json()
                    content_blocks = data.get("content", [])
                    return "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text").strip()
                else:
                    raise ModelProviderError(f"Anthropic API error HTTP {response.status_code}: {response.text}")
        except httpx.ConnectError as e:
            raise ModelProviderError(f"Could not connect to Anthropic API: {e}")
        except httpx.TimeoutException as e:
            raise ModelProviderError(f"Anthropic API request timed out after {self.timeout}s: {e}")

class MockModelAdapter(BaseModelAdapter):
    """
    Deterministic mock adapter for automated testing and isolated validation.
    """

    def __init__(self, response_text: str = "Mocked grounded response"):
        self.response_text = response_text
        self.should_fail: bool = False
        self.failure_reason: str = "Simulated provider outage"

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if self.should_fail:
            raise ModelProviderError(self.failure_reason)
        return self.response_text

def get_model_adapter(provider: Optional[str] = None) -> BaseModelAdapter:
    """Factory function to resolve the active model adapter."""
    selected_provider = (provider or settings.AGENT_PROVIDER).lower()
    if selected_provider == "anthropic":
        return AnthropicAdapter()
    elif selected_provider == "mock":
        return MockModelAdapter()
    else:
        # Default to Ollama for reliable local execution
        return OllamaAdapter()
