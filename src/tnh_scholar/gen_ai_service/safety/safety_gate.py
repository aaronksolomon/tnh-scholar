"""Safety Gate.

Evaluates pre- and post-generation safety policies before finalizing output.
Integrates with rulesets defined under runtime_assets/policies/safety.

Connected modules:
  - safety.rules
  - service.GenAIService
  - models.errors.SafetyError
"""

from dataclasses import dataclass
from typing import List, Sequence

from tnh_scholar.gen_ai_service.config.params_policy import ResolvedParams
from tnh_scholar.gen_ai_service.config.settings import Settings
from tnh_scholar.gen_ai_service.models.domain import (
    CompletionResult,
    Message,
    RenderedPrompt,
    Role,
)
from tnh_scholar.gen_ai_service.models.errors import SafetyBlocked
from tnh_scholar.gen_ai_service.utils.token_utils import (
    FALLBACK_CONTEXT_LIMIT,
    MODEL_CONTEXT_LIMITS,
    token_count_messages,
)
from tnh_scholar.prompt_system.domain.models import PromptMetadata


@dataclass(frozen=True)
class SafetyReport:
    prompt_tokens: int
    context_limit: int
    estimated_cost: float
    warnings: List[str]


def _context_limit_for_model(model: str) -> int:
    return next(
        (limit for name, limit in MODEL_CONTEXT_LIMITS if model.lower().startswith(name.lower())),
        FALLBACK_CONTEXT_LIMIT,
    )


def _estimate_cost(tokens_in: int, max_tokens_out: int) -> float:
    total = tokens_in + max_tokens_out
    return total / 1000.0


def _normalize_messages(prompt: RenderedPrompt) -> Sequence[Message]:
    """Flatten system + user messages for counting."""
    messages: list[Message] = []
    if prompt.system:
        messages.append(Message(role=Role.system, content=prompt.system))
    messages.extend(prompt.messages)
    return messages


def pre_check(
    prompt: RenderedPrompt,
    selection: ResolvedParams,
    settings: Settings,
    *,
    prompt_metadata: PromptMetadata | None = None,
) -> SafetyReport:
    """
    Apply basic size and budget checks before provider call.

    - Max input chars from settings
    - Context window guard (prompt + max_output_tokens)
    - Budget guard using simple token-based estimator

    Args:
        prompt: Rendered prompt (system + messages).
        selection: Resolved parameters (provider, model, max tokens).
        settings: Service settings for limits/pricing.
        prompt_metadata: Optional metadata to emit additional warnings.

    Returns:
        SafetyReport with prompt tokens, context limit, estimated cost, warnings.

    Raises:
        SafetyBlocked: when character, context, or budget limits are exceeded.
    """
    messages = _normalize_messages(prompt)
    prompt_tokens = token_count_messages(messages, model=selection.model)
    context_limit = _context_limit_for_model(selection.model)

    # Character bound
    warnings: list[str] = []
    text_parts: list[str] = []
    for m in messages:
        if isinstance(m.content, str):
            text_parts.append(m.content)
        elif isinstance(m.content, list):
            text_parts.append("".join(str(part) for part in m.content))
            warnings.append("non-string-content-coerced")
        else:
            warnings.append("non-string-content-ignored")
    text_concat = "".join(text_parts)
    if len(text_concat) > settings.max_input_chars:
        raise SafetyBlocked(f"Prompt too large: {len(text_concat)} chars > limit {settings.max_input_chars}")

    if prompt_tokens + selection.max_output_tokens > context_limit:
        raise SafetyBlocked(
            f"Context window exceeded for model {selection.model}: "
            f"{prompt_tokens + selection.max_output_tokens} tokens > {context_limit}"
        )

    estimated_cost = _estimate_cost(prompt_tokens, selection.max_output_tokens)
    estimated_cost *= settings.price_per_1k_tokens
    if estimated_cost > settings.max_dollars:
        raise SafetyBlocked(f"Estimated cost {estimated_cost:.4f} exceeds budget {settings.max_dollars:.4f}")

    if prompt_metadata and prompt_metadata.safety_level == "sensitive":
        warnings.append("prompt-metadata: sensitive content")

    return SafetyReport(
        prompt_tokens=prompt_tokens,
        context_limit=context_limit,
        estimated_cost=estimated_cost,
        warnings=warnings,
    )


def post_check(result: CompletionResult | None) -> list[str]:
    """
    Post-generation validation hooks (stubbed for now).

    Args:
        result: CompletionResult or None when provider response missing.

    Returns:
        List of warning codes (empty when no issues detected).
    """
    warnings: list[str] = []
    if result is None:
        return warnings

    if not result.text:
        warnings.append("empty-result")

    return warnings
