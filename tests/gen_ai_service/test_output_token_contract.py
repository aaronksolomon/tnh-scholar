"""Request boundaries reject missing or invalid output enforcement limits."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from tnh_scholar.gen_ai_service.models.transport import ProviderRequest
from tnh_scholar.gen_ai_service.providers.openai_adapter import OpenAIChatCompletionRequest


@pytest.mark.parametrize(
    ("request_type", "field"),
    [(ProviderRequest, "max_output_tokens"), (OpenAIChatCompletionRequest, "max_completion_tokens")],
)
@pytest.mark.parametrize("limit", [None, 0, -1, True, 1.5, "128"])
def test_request_requires_positive_integer_output_bound(
    request_type: type[BaseModel],
    field: str,
    limit: object,
) -> None:
    """Neither transport boundary accepts an absent or coerced limit."""
    payload = {"provider": "openai", "model": "gpt-test", "messages": [], "temperature": 0.2}
    with pytest.raises(ValidationError, match=field):
        request_type.model_validate(payload | {field: limit})
    with pytest.raises(ValidationError, match=field):
        request_type.model_validate(payload)
