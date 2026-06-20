"""Typed output-token limit policy for GenAI requests."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, model_validator

from tnh_scholar.gen_ai_service.models.errors import SafetyBlocked


class OutputTokenLimitMode(str, Enum):
    """How output token limits should be resolved."""

    CAPPED = "capped"
    MODEL_MAX = "model_max"


class OutputTokenLimitPolicy(BaseModel):
    """Typed token-limit policy before prompt-aware resolution."""

    mode: OutputTokenLimitMode = OutputTokenLimitMode.CAPPED
    capped_tokens: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_mode_requirements(self) -> "OutputTokenLimitPolicy":
        """Require capped token count only for capped mode."""
        if self.mode is OutputTokenLimitMode.CAPPED and self.capped_tokens is None:
            raise ValueError("capped_tokens is required when output token limit mode is capped")
        if self.mode is OutputTokenLimitMode.MODEL_MAX and self.capped_tokens is not None:
            raise ValueError("capped_tokens must be omitted when output token limit mode is model_max")
        return self


class EffectiveOutputTokenLimit(BaseModel):
    """Prompt-aware resolved token limit used for provider requests."""

    mode: OutputTokenLimitMode
    effective_max_output_tokens: int = Field(ge=1)
    model_max_output_tokens: int = Field(ge=1)
    available_context_tokens: int = Field(ge=0)


def resolve_output_token_limit(
    *,
    policy: OutputTokenLimitPolicy,
    provider: str,
    model: str,
    prompt_tokens: int,
) -> EffectiveOutputTokenLimit:
    """Resolve the effective output token budget for a rendered prompt."""
    from tnh_scholar.gen_ai_service.config.registry import get_model_info

    model_info = get_model_info(provider, model)
    context_limit = int(model_info.context_window)
    model_max_output_tokens = int(model_info.max_output_tokens)
    available_context_tokens = context_limit - prompt_tokens

    if available_context_tokens < 1:
        raise SafetyBlocked(
            f"Context window exceeded for model {model}: {prompt_tokens} tokens >= {context_limit}"
        )

    if policy.mode is OutputTokenLimitMode.MODEL_MAX:
        return EffectiveOutputTokenLimit(
            mode=policy.mode,
            effective_max_output_tokens=min(model_max_output_tokens, available_context_tokens),
            model_max_output_tokens=model_max_output_tokens,
            available_context_tokens=available_context_tokens,
        )

    if policy.capped_tokens is None:
        raise ValueError("capped token resolution requires capped_tokens")
    if policy.capped_tokens > model_max_output_tokens:
        raise SafetyBlocked(
            f"Requested max output tokens {policy.capped_tokens} exceed model limit "
            f"{model_max_output_tokens} for {model}"
        )
    if policy.capped_tokens > available_context_tokens:
        raise SafetyBlocked(
            f"Context window exceeded for model {model}: "
            f"{prompt_tokens + policy.capped_tokens} tokens > {context_limit}"
        )
    return EffectiveOutputTokenLimit(
        mode=policy.mode,
        effective_max_output_tokens=policy.capped_tokens,
        model_max_output_tokens=model_max_output_tokens,
        available_context_tokens=available_context_tokens,
    )
