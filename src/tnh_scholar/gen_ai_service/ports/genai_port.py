"""genai_port.py: GenAIService Port Definitions.

Defines structural Protocol interfaces for domain-level service entry points.
Separates orchestration (service.py) from provider and catalog implementations.

Connected modules:
  - service.GenAIService
  - providers.base.ProviderClient
  - pattern_catalog.catalog.PatternCatalog
"""