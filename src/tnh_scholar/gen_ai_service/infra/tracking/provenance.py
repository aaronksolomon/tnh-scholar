"""Provenance builder (V1 per ADR-A12).

This module no longer defines the Provenance model itself; that model
now lives in `domain.py` alongside all other domain-level types.

This module provides a single helper:

    build_provenance(fingerprint=..., provider=..., model=..., ...)

The builder constructs a Provenance object *purely* from:
- a Fingerprint (what was rendered)
- runtime execution metadata (provider, model, timestamps, attempts)

No hashing or prompt-system logic lives here. Hashing and
Prompt-to-domain mapping are performed in the PromptsAdapter.

This builder is called by GenAIService after the provider call
completes, allowing provenance to record true runtime properties.
"""

from __future__ import annotations

from tnh_scholar.gen_ai_service.models.domain import Fingerprint, Provenance

__all__ = [
    "build_provenance",
]

def build_provenance(
    *,
    fingerprint: Fingerprint,
    provider: str,
    model: str,
    sdk_version: str | None,
    started_at,
    finished_at,
    attempt_count: int,
) -> Provenance:
    """Construct a Provenance object from a Fingerprint plus runtime metadata.

    All hashing and prompt-system interactions occur in the PromptsAdapter.
    This function is purely a domain/transport assembly step.
    """

    return Provenance(
        provider=provider,
        model=model,
        sdk_version=sdk_version,
        started_at=started_at,
        finished_at=finished_at,
        attempt_count=attempt_count,
        fingerprint=fingerprint,
    )
