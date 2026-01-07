"""
LLM Client Factory

Provides LangChain-based LLM client factory supporting OpenAI and Anthropic.

Story: 3.5 - Smart Summary Generator
AC: #1 - LLM Integration Setup
"""

import logging
import os
from typing import Optional, Tuple, Union

from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

logger = logging.getLogger(__name__)


class LLMClientError(Exception):
    """Raised when LLM client operations fail."""
    pass


class LLMConfig:
    """Configuration for LLM client from environment variables."""

    def __init__(self):
        # AC#1: Environment variables control model selection and API keys
        self.provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self.timeout_seconds = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1500"))
        self.token_usage_alert_threshold = int(
            os.getenv("TOKEN_USAGE_ALERT_THRESHOLD", "100000")
        )

    @property
    def is_configured(self) -> bool:
        """Check if required API keys are configured."""
        if self.provider == "openai":
            return bool(self.openai_api_key)
        elif self.provider == "anthropic":
            return bool(self.anthropic_api_key)
        return False

    def get_model_name(self) -> str:
        """Get the model name to use based on provider."""
        if self.model:
            return self.model

        # Default models per provider
        if self.provider == "openai":
            return "gpt-4-turbo-preview"
        elif self.provider == "anthropic":
            return "claude-3-sonnet-20240229"
        return "gpt-4-turbo-preview"


def get_llm_config() -> LLMConfig:
    """Get LLM configuration."""
    return LLMConfig()


def get_llm_client(config: Optional[LLMConfig] = None) -> BaseChatModel:
    """
    Factory for LLM client based on configuration.

    AC#1: Creates appropriate LangChain client based on LLM_PROVIDER env var.

    Args:
        config: Optional config override. Uses environment if not provided.

    Returns:
        LangChain chat model instance

    Raises:
        LLMClientError: If provider is not configured or unsupported
    """
    if config is None:
        config = get_llm_config()

    if not config.is_configured:
        raise LLMClientError(
            f"LLM provider '{config.provider}' not configured. "
            f"Set {config.provider.upper()}_API_KEY environment variable."
        )

    try:
        if config.provider == "openai":
            return ChatOpenAI(
                model=config.get_model_name(),
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                timeout=config.timeout_seconds,
                api_key=config.openai_api_key,
            )
        elif config.provider == "anthropic":
            # Import anthropic only when needed to avoid dependency issues
            try:
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(
                    model=config.get_model_name(),
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    timeout=float(config.timeout_seconds),
                    api_key=config.anthropic_api_key,
                )
            except ImportError:
                raise LLMClientError(
                    "langchain-anthropic not installed. "
                    "Install with: pip install langchain-anthropic"
                )
        else:
            raise LLMClientError(
                f"Unsupported LLM provider: {config.provider}. "
                "Supported providers: openai, anthropic"
            )

    except Exception as e:
        if isinstance(e, LLMClientError):
            raise
        raise LLMClientError(f"Failed to create LLM client: {e}") from e


async def check_llm_health(config: Optional[LLMConfig] = None) -> dict:
    """
    Perform health check on LLM service.

    AC#1: Connection is validated on startup with a health check.

    Args:
        config: Optional config override

    Returns:
        Health check result dictionary
    """
    if config is None:
        config = get_llm_config()

    if not config.is_configured:
        return {
            "status": "not_configured",
            "provider": config.provider,
            "message": f"API key not configured for {config.provider}",
            "healthy": False,
        }

    try:
        client = get_llm_client(config)

        # Simple health check - invoke with minimal prompt
        from langchain_core.messages import HumanMessage
        response = await client.ainvoke([HumanMessage(content="Hello")])

        return {
            "status": "healthy",
            "provider": config.provider,
            "model": config.get_model_name(),
            "message": "LLM service is responding",
            "healthy": True,
        }

    except LLMClientError as e:
        return {
            "status": "error",
            "provider": config.provider,
            "message": str(e),
            "healthy": False,
        }
    except Exception as e:
        logger.error(f"LLM health check failed: {e}")
        return {
            "status": "unhealthy",
            "provider": config.provider,
            "message": f"Health check failed: {str(e)}",
            "healthy": False,
        }


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.

    Uses a simple heuristic (words * 1.3) if tiktoken is not available.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    try:
        import tiktoken
        # Use cl100k_base encoding (GPT-4 default)
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except ImportError:
        # Fallback: rough estimate based on word count
        words = len(text.split())
        return int(words * 1.3)
