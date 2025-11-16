"""Tracing Utilities.

Provides decorators or context managers for distributed trace spans,
enabling per-request observability across adapters and orchestrators.

Connected modules:
  - infra.metrics
  - infra.usage
  - service.GenAIService
"""