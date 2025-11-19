# mappers/completion_mapper.py
from typing import Optional

from tnh_scholar.gen_ai_service.models.domain import CompletionEnvelope, CompletionResult, Provenance, Usage
from tnh_scholar.gen_ai_service.models.transport import ProviderResponse, ProviderStatus, TextPayload


def provider_to_completion(
    resp: ProviderResponse, 
    *, 
    provenance: Provenance
    ) -> CompletionEnvelope:
    if resp.status != ProviderStatus.OK or not isinstance(resp.payload, TextPayload):
        # Decide how to surface non-OK: raise, or map to a domain error result.
        # Currently default to raise.
        raise ValueError(f"Non-OK provider response: {resp.status} ({resp.incomplete_reason})")

    dom_usage: Optional[Usage] = None
    if resp.usage:
        dom_usage = Usage(
            prompt_tokens=resp.usage.tokens_in or 0,
            completion_tokens=resp.usage.tokens_out or 0,
            total_tokens=resp.usage.tokens_total or 0
        )

    result = CompletionResult(
        text=resp.payload.text,
        usage=dom_usage,
        model=resp.model,
        provider=resp.provider,
        parsed=resp.payload.parsed,
    )

    return CompletionEnvelope(
        result=result,
        provenance=provenance,
        policy_applied={},
        warnings=[],
    )
