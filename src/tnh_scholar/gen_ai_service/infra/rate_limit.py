"""Rate Limiting Infrastructure.

Implements global or provider-specific rate-limiting policies using
token bucket or exponential backoff strategies.

Connected modules:
  - providers.*_adapter
  - service.GenAIService
"""