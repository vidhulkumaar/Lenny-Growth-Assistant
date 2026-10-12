import re
import logging
import httpx
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

from app.core.config import settings

try:
    import anthropic
    from anthropic import (
        AsyncAnthropic,
        APIError,
        AuthenticationError,
        RateLimitError,
        APITimeoutError,
        APIConnectionError,
    )
    HAS_ANTHROPIC_SDK = True
except ImportError:
    HAS_ANTHROPIC_SDK = False

logger = logging.getLogger(__name__)

class ModelProviderError(Exception):
    """Raised when an LLM provider fails, is unreachable, or misconfigured."""
    pass

class BaseModelAdapter(ABC):
    """Abstract model adapter interface for agent generation."""
    provider_name: str = "base"
    model_name: str = "base-model"

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        """Generate a completion for the given prompt and optional system prompt."""
        pass

class OllamaAdapter(BaseModelAdapter):
    """
    Adapter for local Ollama instance (default: qwen3:4b).
    Preserves 100% offline local demo functionality.
    """
    provider_name: str = "ollama"

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[float] = None,
        temperature: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model_name = model_name or settings.AGENT_MODEL
        self.timeout = timeout or settings.AGENT_TIMEOUT_SECONDS
        self.temperature = temperature if temperature is not None else 0.2

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        url = f"{self.base_url}/api/generate"
        options: Dict[str, Any] = {
            "temperature": self.temperature,
            "num_predict": 4096,
        }
        if top_p is not None:
            options["top_p"] = float(top_p)
        if "top_k" in kwargs and kwargs["top_k"] is not None:
            options["top_k"] = int(kwargs["top_k"])

        # Disable think mode in Ollama payload to prevent qwen3 from exhausting num_predict in reasoning
        payload: Dict[str, Any] = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": options,
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    raw = data.get("response", "").strip()
                    if not raw and data.get("thinking"):
                        raw = data.get("thinking", "").strip()
                    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", raw).strip()
                    if not cleaned and "<think>" in raw:
                        cleaned_partial = re.sub(r"<think>[\s\S]*?(?:</think>|$)", "", raw).strip()
                        if cleaned_partial:
                            cleaned = cleaned_partial
                        else:
                            cleaned = re.sub(r"</?think>", "", raw).strip()
                    return cleaned or raw
                else:
                    logger.error(f"Ollama returned error {response.status_code}: {response.text}")
                    raise ModelProviderError(
                        f"Ollama server returned an error (HTTP {response.status_code}). "
                        f"Please verify the model is installed with 'ollama run {self.model_name}'."
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
    Adapter for Anthropic Claude API using the official Anthropic SDK.
    Never exposes API keys in logs or responses.
    """
    provider_name: str = "claude"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[float] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 4096,
    ):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model_name = model_name or settings.CLAUDE_MODEL
        self.timeout = timeout or settings.AGENT_TIMEOUT_SECONDS
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        top_p: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        if not self.api_key or not self.api_key.strip():
            raise ModelProviderError(
                "Anthropic API key is not configured. Please set ANTHROPIC_API_KEY in your backend .env file "
                "or switch to Ollama (Local) in the model settings."
            )

        if not HAS_ANTHROPIC_SDK:
            raise ModelProviderError(
                "The 'anthropic' Python package is not available in the virtual environment. "
                "Please run 'pip install anthropic' to enable Claude integration."
            )

        try:
            client = AsyncAnthropic(
                api_key=self.api_key,
                timeout=self.timeout,
            )
            message_kwargs: Dict[str, Any] = {
                "model": self.model_name,
                "max_tokens": self.max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system_prompt:
                message_kwargs["system"] = system_prompt
            extra_body: Dict[str, Any] = {}
            if self.temperature is not None:
                # Claude supports temperature in range [0.0, 1.0]
                extra_body["temperature"] = max(0.0, min(float(self.temperature), 1.0))
            if top_p is not None:
                # Claude supports top_p in range [0.0, 1.0]
                extra_body["top_p"] = max(0.0, min(float(top_p), 1.0))

            if extra_body:
                message_kwargs["extra_body"] = extra_body

            response = await client.messages.create(**message_kwargs)

            text_blocks: List[str] = []
            for block in response.content:
                if getattr(block, "type", None) == "text" or hasattr(block, "text"):
                    text_blocks.append(block.text)

            result_text = "".join(text_blocks).strip()
            if not result_text:
                raise ModelProviderError("Claude returned an empty response.")
            return result_text

        except AuthenticationError as e:
            logger.error("Anthropic authentication failed (invalid API key).")
            raise ModelProviderError(
                "Anthropic authentication failed. Please verify that your ANTHROPIC_API_KEY is valid."
            )
        except RateLimitError as e:
            logger.warning("Anthropic rate limit reached.")
            raise ModelProviderError(
                "Anthropic rate limit reached. Please wait a moment before trying again."
            )
        except APITimeoutError as e:
            logger.error(f"Anthropic API request timed out after {self.timeout}s.")
            raise ModelProviderError(
                f"Claude request timed out after {self.timeout} seconds. The provider may be experiencing delays."
            )
        except APIConnectionError as e:
            logger.error("Could not connect to Anthropic API.")
            raise ModelProviderError(
                "Could not connect to Anthropic Claude API. Please check your internet connection."
            )
        except APIError as e:
            logger.error(f"Anthropic API returned error: {e.message}")
            raise ModelProviderError(f"Claude API error: {e.message}")
        except Exception as e:
            if isinstance(e, ModelProviderError):
                raise
            logger.error(f"Unexpected error communicating with Anthropic Claude: {e}", exc_info=True)
            raise ModelProviderError(f"Unexpected error communicating with Claude: {str(e)}")

class MockModelAdapter(BaseModelAdapter):
    """
    Deterministic mock adapter for automated testing and isolated validation.
    """
    provider_name: str = "mock"
    model_name: str = "mock-model"

    def __init__(self, response_text: str = "Mocked grounded response"):
        self.response_text = response_text
        self.should_fail: bool = False
        self.failure_reason: str = "Simulated provider outage"

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if self.should_fail:
            raise ModelProviderError(self.failure_reason)
        return self.response_text

SUPPORTED_PROVIDERS = ("ollama", "claude", "anthropic", "mock")

def validate_provider(provider: Optional[str]) -> str:
    """
    Validates and normalizes provider name.
    Raises ValueError if an unsupported provider identifier is supplied.
    """
    if not provider:
        return settings.AGENT_PROVIDER.lower()
    p = provider.lower().strip()
    if p not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unsupported model provider '{provider}'. Supported providers are: 'ollama' (Local), 'claude' (Cloud)."
        )
    return "claude" if p == "anthropic" else p

def get_model_adapter(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
) -> BaseModelAdapter:
    """Factory function to resolve the active model adapter with hyperparameter support."""
    selected_provider = validate_provider(provider)
    if selected_provider == "claude":
        return AnthropicAdapter(
            model_name=model or settings.CLAUDE_MODEL,
            temperature=temperature,
        )
    elif selected_provider == "mock":
        return MockModelAdapter()
    else:
        return OllamaAdapter(
            model_name=model or settings.AGENT_MODEL,
            temperature=temperature,
        )

def get_providers_info() -> Dict[str, Any]:
    """Returns available provider metadata for the UI toggle and system status."""
    has_anthropic_key = bool(settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY.strip())
    active = validate_provider(settings.AGENT_PROVIDER)

    return {
        "active_provider": active,
        "providers": [
            {
                "id": "ollama",
                "name": "Ollama (Local)",
                "type": "local",
                "model": settings.AGENT_MODEL,
                "available": True,
                "description": "Local offline model running directly via Ollama",
            },
            {
                "id": "claude",
                "name": "Claude AI (Cloud)",
                "type": "cloud",
                "model": settings.CLAUDE_MODEL,
                "available": has_anthropic_key,
                "description": (
                    "Anthropic Claude 3.5 Sonnet cloud model via ANTHROPIC_API_KEY"
                    if has_anthropic_key
                    else "Requires ANTHROPIC_API_KEY in backend/.env"
                ),
            },
        ],
    }
