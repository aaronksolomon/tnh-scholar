"""PatternCatalog Core.

Manages retrieval and rendering of prompt patterns used by GenAIService.
Implements the PatternCatalog Protocol for lookup, rendering, and fingerprinting.

Connected modules:
  - pattern_catalog.render
  - pattern_catalog.fingerprint
  - pattern_catalog.adapters.legacy_patterns_adapter
  - service.GenAIService
"""