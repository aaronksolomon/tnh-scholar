"""Retry Policy Management.

Defines exponential retry strategies and transient error recovery wrappers.
Used by all adapter layers to ensure robust API interactions.

Connected modules:
  - providers.*_adapter
  - infra.rate_limit
"""