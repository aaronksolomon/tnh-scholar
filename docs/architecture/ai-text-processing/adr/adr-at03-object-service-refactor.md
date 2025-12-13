---
title: "ADR-AT03: Minimal AI Text Processing Refactor for tnh-gen"
description: "Focused refactor of ai_text_processing module to support tnh-gen CLI release: TextObject robustness, GenAI Service integration, and basic prompt system adoption"
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Sonnet 4.5"
status: proposed
created: "2025-12-07"
updated: "2025-12-12"
---

# ADR-AT03: Minimal AI Text Processing Refactor for tnh-gen

This ADR defines a **minimal viable refactor** of the `ai_text_processing` module to support the tnh-gen CLI release (ADR-TG01). It focuses on TextObject robustness, GenAI Service integration, and basic prompt system adoption—without implementing the full platform architecture proposed in ADR-AT04.

- **Status**: Proposed
- **Date**: 2025-12-07
- **Updated**: 2025-12-12
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, Claude Sonnet 4.5

## Executive Summary

**Problem**: tnh-gen CLI (ADR-TG01) is blocked pending robust ai_text_processing, but the full AT04 platform (13-17 weeks) would delay the release significantly.

**Solution**: Implement a focused 1-2 week refactor that:

1. Fixes critical TextObject/NumberedText bugs (section boundary validation, metadata propagation)
2. Integrates GenAI Service (removes direct OpenAI SDK calls, adds provenance)
3. Adopts basic prompt system (load prompts from catalog, variable substitution)
4. Provides structured error handling for tnh-gen CLI exit codes

**Scope Constraint**: This ADR explicitly **does NOT** implement AT04's Task Orchestration, Context Propagation Graph, Strategy Catalog, Validation Loops, or Experimentation Harness. Those capabilities are deferred to AT04's phased implementation.

**Relationship to AT04**: This refactor establishes the **foundation** that AT04 builds upon. The TextObject improvements, GenAI Service integration, and prompt system adoption are prerequisites for AT04's platform architecture (as noted in AT04 §5 "Migration from AT03").

## Context

### The Release Blocker

The tnh-gen CLI (ADR-TG01) requires a functional ai_text_processing module to:

- Execute prompts from the catalog with variable substitution
- Return structured results with provenance tracking
- Raise structured exceptions that map to CLI exit codes
- Support batch processing of multiple files

However, the current `ai_text_processing` module suffers from critical issues that block tnh-gen:

### Critical Pain Points (Blocking tnh-gen)

1. **TextObject Brittleness**:
   - Implicit end_line calculation produces off-by-one errors
   - No validation for section gaps/overlaps
   - Metadata propagation bugs during merging

2. **Direct OpenAI Dependencies**:
   - Direct SDK calls scattered in `openai_process_interface.py`, `line_translator.py`
   - No response fingerprinting for provenance
   - Cannot route through GenAI Service policies (budget limits, rate limiting)

3. **Hard-Coded Prompts**:
   - Prompts in `prompts.py` as Python strings
   - No versioning or variable validation
   - Cannot leverage tnh-gen's prompt catalog integration

4. **Unstructured Errors**:
   - Generic exceptions don't map to tnh-gen's exit codes
   - No distinction between PolicyError, TransportError, etc.

### Non-Critical Issues (Deferred to AT04)

These issues exist but are **not blockers** for tnh-gen and are addressed in AT04:

1. **No Context Propagation**: Documents processed in isolation, no cross-section context (AT04 Phase 1)
2. **No Strategy Polymorphism**: Single hard-coded sectioning approach (AT04 Phase 2)
3. **No Validation Loops**: No quality gates to catch translation drift (AT04 Phase 3)
4. **No Experimentation Harness**: Cannot compare strategies quantitatively (AT04 Phase 4)
5. **No Cross-Document Coherence**: Multi-document works lack terminology consistency (AT04 Phase 5)

### Scope Constraints

**What This ADR Implements** (1-2 weeks):

- ✅ **Tier 0**: TextObject/NumberedText robustness fixes
- ✅ **Tier 1**: Basic object-service patterns (minimal protocols/adapters for GenAI/Prompts)
- ✅ **Tier 2**: GenAI Service integration (remove direct OpenAI calls)
- ✅ **Tier 3**: Basic prompt system adoption (load from catalog, variable substitution)
- ✅ **Error Handling**: Structured exceptions for tnh-gen CLI

**What This ADR Does NOT Implement** (Deferred to AT04):

- ❌ Task Orchestration Layer (AT04 Phase 1)
- ❌ Context Propagation Graph (AT04 Phase 1)
- ❌ Strategy Catalog & Polymorphism (AT04 Phase 2)
- ❌ Validation Loops (AT04 Phase 3)
- ❌ Experimentation Harness (AT04 Phase 4)
- ❌ Cross-Document Coherence (AT04 Phase 5)

### Design Drivers

1. **Unblock tnh-gen**: Minimal changes to enable CLI release
2. **Foundation for AT04**: Implement prerequisites (TextObject, GenAI, Prompts) that AT04 builds upon
3. **Avoid Over-Engineering**: Keep current sectioning/translation strategies as-is (no strategy catalog)
4. **Testability**: Add basic tests for TextObject validation and GenAI integration
5. **Incremental Migration**: Maintain backwards compatibility during refactor

## Decision

### Tier 0: TextObject/NumberedText Robustness (NEW)

Fix critical bugs in TextObject that cause section boundary errors:

#### 0.1 Section Boundary Validation

Add validation methods to detect and report boundary errors:

```python
# text_object.py
from dataclasses import dataclass

@dataclass
class SectionValidationError:
    """Error found in section boundaries."""
    error_type: str  # 'gap', 'overlap', 'out_of_bounds'
    section_index: int
    expected_start: int
    actual_start: int
    message: str

class NumberedText:
    """Immutable container for numbered text lines."""

    def validate_section_boundaries(self) -> list[SectionValidationError]:
        """Validate section boundaries for gaps, overlaps, out-of-bounds.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not self.sections:
            return errors

        for i, section in enumerate(self.sections):
            # Check start_line is within bounds
            if section.start_line < 1 or section.start_line > len(self.lines):
                errors.append(SectionValidationError(
                    error_type='out_of_bounds',
                    section_index=i,
                    expected_start=1,
                    actual_start=section.start_line,
                    message=f"Section {i} start_line {section.start_line} out of bounds [1, {len(self.lines)}]"
                ))
                continue

            # Calculate implicit end_line
            end_line = (
                self.sections[i + 1].start_line - 1
                if i < len(self.sections) - 1
                else len(self.lines)
            )

            # Check for gaps (expected_start != actual_start)
            if i > 0:
                expected_start = self.sections[i - 1].get_implicit_end_line(self) + 1
                if section.start_line != expected_start:
                    error_type = 'gap' if section.start_line > expected_start else 'overlap'
                    errors.append(SectionValidationError(
                        error_type=error_type,
                        section_index=i,
                        expected_start=expected_start,
                        actual_start=section.start_line,
                        message=f"Section {i} has {error_type}: expected start {expected_start}, got {section.start_line}"
                    ))

        return errors

    def get_coverage_report(self) -> dict[str, Any]:
        """Get coverage statistics for debugging.

        Returns:
            Dict with coverage info: total_lines, covered_lines, gaps, overlaps
        """
        if not self.sections:
            return {
                'total_lines': len(self.lines),
                'covered_lines': 0,
                'coverage_pct': 0.0,
                'gaps': [],
                'overlaps': []
            }

        covered = set()
        gaps = []
        overlaps = []

        for i, section in enumerate(self.sections):
            start = section.start_line
            end = self.sections[i + 1].start_line - 1 if i < len(self.sections) - 1 else len(self.lines)

            section_lines = set(range(start, end + 1))

            # Check for overlaps
            overlap = covered & section_lines
            if overlap:
                overlaps.append({
                    'section_index': i,
                    'lines': sorted(overlap)
                })

            covered.update(section_lines)

        # Check for gaps
        all_lines = set(range(1, len(self.lines) + 1))
        gap_lines = all_lines - covered
        if gap_lines:
            gaps.append(sorted(gap_lines))

        return {
            'total_lines': len(self.lines),
            'covered_lines': len(covered),
            'coverage_pct': len(covered) / len(self.lines) * 100 if self.lines else 0,
            'gaps': gaps,
            'overlaps': overlaps
        }
```

#### 0.2 Metadata Merging Fixes

Fix metadata propagation bugs in `merge_metadata()`:

```python
# text_object.py
class TextObject:
    """Mutable state container for text processing."""

    def merge_metadata(self, other: 'TextObject', strategy: str = 'preserve') -> None:
        """Merge metadata from another TextObject.

        Args:
            other: TextObject to merge metadata from
            strategy: 'preserve' (keep existing), 'update' (overwrite), 'combine' (merge dicts)
        """
        if strategy == 'preserve':
            # Only add keys that don't exist
            for key, value in other.metadata.items():
                self.metadata.setdefault(key, value)

        elif strategy == 'update':
            # Overwrite all keys
            self.metadata.update(other.metadata)

        elif strategy == 'combine':
            # Merge dictionaries deeply
            for key, value in other.metadata.items():
                if key in self.metadata and isinstance(self.metadata[key], dict) and isinstance(value, dict):
                    # Deep merge dicts
                    self.metadata[key] = {**self.metadata[key], **value}
                else:
                    self.metadata[key] = value

        else:
            raise ValueError(f"Invalid merge strategy: {strategy}")
```

### Tier 1: Minimal Object-Service Patterns

**Scope**: Keep it minimal—only what's needed for GenAI/Prompt integration. Avoid full domain modeling.

#### 1.1 Simple Error Hierarchy

Add structured exceptions for tnh-gen CLI exit code mapping:

```python
# exceptions.py
class AITextProcessingError(Exception):
    """Base exception for ai_text_processing module."""
    pass

class SectionBoundaryError(AITextProcessingError):
    """Section boundaries have gaps, overlaps, or out-of-bounds errors."""
    def __init__(self, errors: list[SectionValidationError]):
        self.errors = errors
        message = f"Section boundary validation failed: {len(errors)} errors"
        super().__init__(message)

class PromptRenderError(AITextProcessingError):
    """Failed to render prompt template."""
    pass

class ProcessingError(AITextProcessingError):
    """Generic processing failure (wraps GenAI Service errors)."""
    pass
```

#### 1.2 Minimal Adapter for GenAI Service

Wrap GenAI Service to isolate direct dependency:

```python
# genai_wrapper.py
from tnh_scholar.gen_ai_service.services.genai_service import GenAIService
from tnh_scholar.gen_ai_service.pattern_catalog.adapters.prompts_adapter import PromptsAdapter
from .exceptions import ProcessingError, PromptRenderError

class GenAIWrapper:
    """Minimal wrapper for GenAI Service integration."""

    def __init__(self, genai_service: GenAIService, prompts_adapter: PromptsAdapter):
        self._genai = genai_service
        self._prompts = prompts_adapter

    def render_and_execute(
        self,
        prompt_key: str,
        variables: dict[str, str],
        model: str | None = None
    ) -> tuple[str, dict]:
        """Render prompt and execute via GenAI Service.

        Args:
            prompt_key: Key for prompt in catalog
            variables: Template variables
            model: Optional model override

        Returns:
            Tuple of (result_text, metadata_dict)

        Raises:
            PromptRenderError: Prompt rendering failed
            ProcessingError: GenAI execution failed
        """
        try:
            # Render prompt
            rendered, fingerprint = self._prompts.render(
                RenderRequest(
                    instruction_key=prompt_key,
                    variables=variables,
                    user_input=variables.get("input_text", "")
                )
            )
        except Exception as e:
            raise PromptRenderError(f"Failed to render prompt '{prompt_key}': {e}") from e

        try:
            # Execute via GenAI
            response = self._genai.execute(
                messages=rendered.messages,
                model=model or rendered.model,
                response_format=rendered.response_format
            )
        except Exception as e:
            raise ProcessingError(f"GenAI execution failed: {e}") from e

        # Build metadata
        metadata = {
            'prompt_key': prompt_key,
            'prompt_fingerprint': fingerprint,
            'model': response.model,
            'usage': response.usage._asdict() if response.usage else {},
            'latency_ms': getattr(response, 'latency_ms', None)
        }

        return response.content, metadata
```

### Tier 2: GenAI Service Integration

**Scope**: Replace direct OpenAI SDK calls with GenAI Service. Keep existing processor logic.

#### 2.1 Update Existing Processors

Update `line_translator.py` and other processors to use `GenAIWrapper`:

**Before (current):**

```python
# line_translator.py (CURRENT - uses direct OpenAI)
import openai
from .prompts import TRANSLATION_PROMPT

def translate_section(section_text: str, target_lang: str) -> str:
    """Translate section using OpenAI."""
    prompt = TRANSLATION_PROMPT.format(
        target_language=target_lang,
        input_text=section_text
    )

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
```

**After (refactored):**

```python
# line_translator.py (REFACTORED - uses GenAIWrapper)
from .genai_wrapper import GenAIWrapper
from .exceptions import ProcessingError

def translate_section(
    section_text: str,
    target_lang: str,
    genai: GenAIWrapper,
    model: str | None = None
) -> tuple[str, dict]:
    """Translate section using GenAI Service.

    Args:
        section_text: Text to translate
        target_lang: Target language code
        genai: GenAI wrapper instance
        model: Optional model override

    Returns:
        Tuple of (translated_text, metadata)

    Raises:
        ProcessingError: Translation failed
    """
    variables = {
        'input_text': section_text,
        'target_language': target_lang
    }

    result_text, metadata = genai.render_and_execute(
        prompt_key='translation',
        variables=variables,
        model=model
    )

    return result_text, metadata
```

#### 2.2 Simple Factory Function

Add factory to create configured GenAI wrapper:

```python
# factory.py
from tnh_scholar.gen_ai_service.services.genai_service import GenAIService
from tnh_scholar.gen_ai_service.pattern_catalog.adapters.prompts_adapter import PromptsAdapter
from .genai_wrapper import GenAIWrapper

def create_genai_wrapper() -> GenAIWrapper:
    """Create configured GenAI wrapper.

    Returns:
        GenAIWrapper ready for use
    """
    # Initialize from environment/config
    genai_service = GenAIService.from_env()
    prompts_adapter = PromptsAdapter.from_env()

    return GenAIWrapper(genai_service, prompts_adapter)
```

### Tier 3: Basic Prompt System Integration

**Scope**: Migrate prompts to catalog, use PromptsAdapter for rendering. No complex task mapping.

#### 3.1 Migrate Key Prompts to Catalog

Move prompts from `prompts.py` to prompt catalog:

**Before (current):**

```python
# prompts.py (LEGACY - to be deprecated)
TRANSLATION_PROMPT = """
Translate the following text to {target_language}:

{input_text}
"""
```

**After (in prompt catalog):**

```markdown
<!-- prompts/translation.md -->
---
name: translation
version: 1.0
description: Translate text to target language
required_variables: [input_text, target_language]
default_model: gpt-4o
output_mode: text
tags: [translation, text-processing]
---

Translate the following text to {{target_language}}:

{{input_text}}
```

#### 3.2 Keep Task Mapping Simple

No complex PromptCatalogPort—just pass prompt keys directly:

```python
# Processors call GenAIWrapper with explicit prompt keys
result, metadata = genai.render_and_execute(
    prompt_key='translation',  # Direct key reference
    variables={'input_text': text, 'target_language': 'en'},
    model='gpt-4o'
)
```

**Rationale**: Avoid premature abstraction. AT04 will add strategy catalog later.

### Migration Strategy (1-2 Weeks)

#### Phase 1: TextObject Robustness (Days 1-3)

1. Add `validate_section_boundaries()` to `NumberedText`
2. Add `get_coverage_report()` for debugging
3. Fix `merge_metadata()` bugs in `TextObject`
4. Add unit tests for validation methods
5. **Deliverable**: TextObject tests pass, section validation working

#### Phase 2: GenAI Service Integration (Days 4-6)

1. Create `GenAIWrapper` class with `render_and_execute()`
2. Add `exceptions.py` with error hierarchy
3. Create `factory.py` with `create_genai_wrapper()`
4. Update `line_translator.py` to use wrapper (keep function signature compatible)
5. Remove direct OpenAI imports
6. **Deliverable**: No direct OpenAI SDK calls, provenance metadata captured

#### Phase 3: Prompt Migration (Days 7-9)

1. Migrate 3-5 key prompts to catalog (`translation`, `sectioning`, `summarization`)
2. Update processors to use prompt keys instead of `prompts.py` strings
3. Add deprecation warning to `prompts.py`
4. Test prompt rendering with PromptsAdapter
5. **Deliverable**: Key prompts loaded from catalog

#### Phase 4: Integration & Testing (Days 10-12)

1. Integration tests for full workflows (sectioning → translation)
2. Test tnh-gen CLI with refactored module
3. Verify error handling maps to CLI exit codes
4. Documentation updates (migration guide for consumers)
5. **Deliverable**: tnh-gen CLI functional with robust ai_text_processing

## Consequences

### Positive

- **Unblocks tnh-gen**: Enables CLI release in 1-2 weeks instead of waiting 13-17 weeks for AT04
- **Foundation for AT04**: TextObject robustness, GenAI integration, and prompt adoption are AT04 prerequisites
- **Provenance Tracking**: Response fingerprinting from GenAI Service supports audit trails
- **Structured Errors**: Exception hierarchy maps to tnh-gen CLI exit codes for better UX
- **Reduced Technical Debt**: Removes direct OpenAI SDK dependencies
- **Testability**: GenAIWrapper enables mocking for unit tests
- **Prompt Versioning**: Basic prompt catalog integration enables future strategy work

### Negative

- **Minimal Abstraction**: No full object-service patterns (ports/adapters) to avoid over-engineering
- **Limited Scope**: Does not solve context fragmentation, strategy polymorphism, or validation loops (deferred to AT04)
- **Function Signature Changes**: Processors now require GenAIWrapper parameter (breaking change)
- **Incomplete Migration**: Some prompts may remain in `prompts.py` temporarily

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Scope creep** | Refactor takes longer than 2 weeks | Strict scope: only TextObject, GenAI, and basic prompts. No strategy catalog. |
| **Breaking changes** | Consumers of ai_text_processing break | Keep backwards-compatible wrappers for key functions during transition. |
| **Technical debt** | Minimal patterns accumulate debt | Document relationship to AT04; plan full migration path. |
| **Testing gaps** | Bugs slip through | Add unit tests for TextObject validation, GenAIWrapper integration. |

## Alternatives Considered

### Alternative 1: Wait for AT04 Full Platform

**Approach**: Block tnh-gen release until AT04's complete platform (13-17 weeks) is ready.

**Rejected**: Delays tnh-gen release significantly. AT04's Task Orchestration, Context Graph, and Strategy Catalog are not needed for basic CLI functionality.

### Alternative 2: Skip Refactor, Ship Current Code

**Approach**: Ship tnh-gen with current ai_text_processing (direct OpenAI calls, hard-coded prompts).

**Rejected**: TextObject brittleness causes section boundary errors. No provenance tracking. Would accumulate more technical debt.

### Alternative 3: Minimal Patch Only (No GenAI Integration)

**Approach**: Fix only TextObject bugs, defer GenAI and Prompt integration.

**Rejected**: Misses opportunity to remove OpenAI dependencies and enable provenance. GenAI integration is straightforward and valuable.

## Relationship to ADR-AT04

This ADR implements **Phase 0.5** of the AT04 roadmap:

```text
ADR-AT03 (this doc)          →  ADR-AT04 Full Platform
─────────────────────────────────────────────────────────
✅ TextObject robustness      →  Context Propagation Graph
✅ GenAI Service integration  →  Task Orchestration Layer
✅ Basic prompt adoption      →  Strategy Catalog & Polymorphism
✅ Error handling             →  Validation Loops
                              →  Experimentation Harness
                              →  Cross-Document Coherence
```

**AT03 is not wasted work**—it's the foundation AT04 builds on (as stated in AT04 §5 "Migration from AT03").

**Key Differences**:

- **AT03**: Minimal changes to unblock tnh-gen (1-2 weeks)
- **AT04**: Comprehensive platform for strategy experimentation, context fidelity, evaluation (13-17 weeks)

**Migration Path**: After tnh-gen release, AT04 implementation can proceed incrementally without disrupting the CLI.

## Success Criteria

This ADR succeeds if:

1. **tnh-gen CLI functional**: Can execute prompts from catalog with provenance
2. **Section validation working**: `validate_section_boundaries()` catches gaps/overlaps
3. **No direct OpenAI calls**: All AI requests go through GenAI Service
4. **Structured errors**: Exceptions map to tnh-gen exit codes (PolicyError, TransportError, etc.)
5. **Timeline met**: Deliverables completed in 10-12 working days
6. **Tests pass**: Unit tests for TextObject validation, GenAIWrapper integration
7. **AT04-ready**: Foundation in place for Task Orchestration, Context Graph, Strategy Catalog

## References

### Related ADRs

- **[ADR-AT04: AI Text Processing Strategy](/architecture/ai-text-processing/adr/adr-at04-ai-text-processing-platform-strat.md)** - Full platform architecture (builds on AT03)
- **[ADR-TG01: CLI Architecture](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md)** - tnh-gen CLI (primary consumer)
- **[ADR-TG02: Prompt Integration](/architecture/tnh-gen/adr/adr-tg02-prompt-integration.md)** - CLI ↔ prompt system integration
- **[ADR-A13: GenAI Service](/architecture/gen-ai-service/adr/adr-a13-migrate-openai-to-genaiservice.md)** - GenAI service architecture
- **[ADR-PT04: Prompt System Refactor](/architecture/prompt-system/adr/adr-pt04-prompt-system-refactor.md)** - Prompt system architecture
- **[ADR-AT01: AI Text Processing Pipeline](/architecture/ai-text-processing/adr/adr-at01-ai-text-processing.md)** - Original text processing design
- **[ADR-AT02: TextObject Architecture](/architecture/ai-text-processing/adr/adr-at02-sectioning-textobject.md)** - TextObject historical context

### External Resources

- [GenAI Service Documentation](https://github.com/anthropics/tnh-scholar) - Integration guide
- [Prompt System Documentation](https://github.com/anthropics/tnh-scholar) - Catalog structure

---

**Approval Path**: Architecture review → Implementation → Testing → tnh-gen Release

*This ADR defines the minimal viable refactor that enables tnh-gen CLI release while establishing the foundation for ADR-AT04's comprehensive platform architecture.*
