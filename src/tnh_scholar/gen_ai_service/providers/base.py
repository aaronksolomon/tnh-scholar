"""Base Provider Protocols.

Defines ProviderClient and related Protocols that standardize
`generate()` or `complete()` signatures across AI providers.

Connected modules:
  - providers.openai_adapter
  - providers.anthropic_adapter
  - ports.genai_port
"""

# providers/base.py
from typing import Protocol

from tnh_scholar.gen_ai_service.models.transport import ProviderRequest, ProviderResponse


class ProviderClient(Protocol):
    def generate(self, request: ProviderRequest) -> ProviderResponse: ...