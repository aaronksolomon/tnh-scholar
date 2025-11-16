"""Pattern Rendering Logic.

Responsible for merging user requests with template variables and producing
a RenderedPrompt or RenderedMessage sequence ready for provider input.

Connected modules:
  - pattern_catalog.catalog.PatternCatalog
  - pattern_catalog.fingerprint
"""