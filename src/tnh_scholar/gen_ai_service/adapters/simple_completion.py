"""Simple completion adapter for easier migration from legacy openai_interface.

Provides a simpler, legacy-compatible API that wraps GenAIService.
This is a temporary migration aid - production code should use GenAIService directly.

Connected modules:
  - gen_ai_service.service.GenAIService
  - gen_ai_service.models.domain (RenderRequest, Message)
  - gen_ai_service.utils.response_utils
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from pydantic import BaseModel

from tnh_scholar.gen_ai_service.models.domain import Message, Role
from tnh_scholar.gen_ai_service.service import GenAIService
from tnh_scholar.logging_config import get_logger

logger = get_logger("tnh_scholar.gen_ai_service.adapters.simple_completion")


@dataclass(frozen=True)
class SimpleCompletionPolicy:
    """Policy configuration for simple completion adapter.

    This policy defines defaults for the simple_completion adapter.
    It's kept local to this module since simple_completion is a temporary
    migration aid expected to be removed once all code migrates to GenAIService.

    Attributes:
        default_model: Default OpenAI model to use when not specified
        default_temperature: Default sampling temperature (0.0-2.0)
        default_max_tokens: Default maximum tokens for completion
        default_provider: Default LLM provider (currently only OpenAI supported)
    """

    default_model: str = "gpt-4o"
    default_temperature: float = 0.7
    default_max_tokens: int = 4096
    default_provider: str = "openai"


# Policy instance - single source of defaults for this adapter
POLICY = SimpleCompletionPolicy()

# Global service instance (initialized on first use)
_service: Optional[GenAIService] = None


def _get_service() -> GenAIService:
    """Get or initialize the global GenAIService instance."""
    global _service
    if _service is None:
        _service = GenAIService()
    return _service

def simple_completion(
    system_message: str,
    user_message: str,
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    response_model: type[BaseModel] | None = None,
) -> Union[str, BaseModel]:
    """
    Simple completion interface compatible with legacy openai_interface usage.

    This is a migration adapter that provides a simple API similar to the legacy
    run_immediate_completion_simple() function. It uses the OpenAI client directly,
    bypassing the pattern catalog to allow drop-in replacement during migration.

    NOTE: This bypasses GenAIService's pattern catalog. It's intentional for migration
    to allow replacing legacy calls without first moving prompts to the catalog.
    Once migration is complete, refactor to use GenAIService with proper catalog prompts.

    Args:
        system_message: System prompt/instructions
        user_message: User input/query
        model: Model to use (e.g., "gpt-4o") - optional, uses default if not specified
        max_tokens: Maximum tokens in completion
        temperature: Sampling temperature (0-2)
        response_model: Optional Pydantic model class for structured outputs

    Returns:
        str | BaseModel: Generated text or structured response

    Example:
        >>> # Simple text generation
        >>> text = simple_completion(
        ...     system_message="You are a translator",
        ...     user_message="Translate 'hello' to French"
        ... )
        >>> print(text)
        "bonjour"
        >>> # Structured response
        >>> class Translation(BaseModel):
        ...     translated: str
        ...
        >>> translated = simple_completion(
        ...     system_message="Return JSON",
        ...     user_message="{'translated': 'bonjour'}",
        ...     response_model=Translation,
        ... )

    Note:
        This is a temporary migration aid that bypasses the pattern catalog.
        Refactor to use GenAIService with proper prompts for better features.
    """
    from tnh_scholar.gen_ai_service.models.transport import ProviderRequest, ProviderStatus

    # Get or create OpenAI client from service (reuse existing setup)
    service = _get_service()
    client = service.openai_client

    # Build messages
    messages = []
    if system_message:
        messages.append(Message(role=Role.system, content=system_message))
    messages.append(Message(role=Role.user, content=user_message))

    # Build provider request using policy defaults
    provider_request = ProviderRequest(
        provider=POLICY.default_provider,
        model=model or POLICY.default_model,
        system=system_message,
        messages=messages,
        temperature=temperature or POLICY.default_temperature,
        max_output_tokens=max_tokens or POLICY.default_max_tokens,
        seed=None,
        response_format=response_model,
    )

    try:
        # Call OpenAI client directly
        response = client.generate(provider_request)

        # Check status
        if response.status != ProviderStatus.OK:
            raise RuntimeError(
                f"Completion failed with status {response.status}: {response.error}"
            )

        if not response.payload:
            raise ValueError("Provider response did not include payload")

        if response_model is not None:
            parsed_payload = response.payload.parsed
            if parsed_payload is None:
                raise ValueError(
                    "Provider response did not include structured payload despite response_model"
                )
            if not isinstance(parsed_payload, response_model):
                raise TypeError(
                    f"Parsed payload type {type(parsed_payload).__name__} "
                    f"did not match expected {response_model.__name__}"
                )
            return parsed_payload

        return response.payload.text

    except Exception as e:
        logger.error(f"Simple completion failed: {e}")
        raise

def simple_completion_from_file(
    system_message: str,
    user_message_file: Union[str, Path],
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
    response_model: type[BaseModel] | None = None,
) -> Union[str, BaseModel]:
    """
    Simple completion with user message loaded from file.

    Args:
        system_message: System prompt/instructions
        user_message_file: Path to file containing user message
        model: Model to use (optional)
        max_tokens: Maximum tokens in completion
        temperature: Sampling temperature

    Returns:
        str: Generated response

    Example:
        >>> text = simple_completion_from_file(
        ...     system_message="Summarize this text",
        ...     user_message_file="document.txt"
        ... )
    """
    from tnh_scholar.utils.file_utils import read_str_from_file

    path = Path(user_message_file) if isinstance(user_message_file, str) else user_message_file
    user_message = read_str_from_file(path)

    return simple_completion(
        system_message=system_message,
        user_message=user_message,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        response_model=response_model,
    )


__all__ = ["simple_completion", "simple_completion_from_file"]
