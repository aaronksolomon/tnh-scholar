---
title: "ADR-AT03.3: TextObject Robustness and Metadata Management"
description: "Fixes metadata propagation bugs, enhances section validation, and adds merge strategies to TextObject for reliable ai_text_processing workflows"
type: "design-detail"
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Sonnet 4.5"
status: proposed
created: "2025-12-12"
parent_adr: "adr-at03-object-service-refactor.md"
related_adrs: ["adr-at03.2-numberedtext-validation.md", "adr-at03.1-transition-plan.md"]
---

# ADR-AT03.3: TextObject Robustness and Metadata Management

Fixes critical metadata propagation bugs, enhances section validation using NumberedText capabilities (ADR-AT03.2), and adds explicit merge strategies to TextObject for reliable text processing workflows.

- **Status**: Proposed
- **Type**: Design Detail
- **Date**: 2025-12-12
- **Owner**: aaronksolomon
- **Author**: Aaron Solomon, Claude Sonnet 4.5
- **Parent ADR**: [ADR-AT03: Minimal AI Text Processing Refactor for tnh-gen](/architecture/ai-text-processing/adr/adr-at03-object-service-refactor.md)
- **Related ADRs**: [ADR-AT03.2: NumberedText Validation](/architecture/ai-text-processing/adr/adr-at03.2-numberedtext-validation.md), [ADR-AT03.1: Transition Plan](/architecture/ai-text-processing/adr/adr-at03.1-transition-plan.md)

---

## Context

### The Problem

TextObject (in `src/tnh_scholar/ai_text_processing/text_object.py`) is the primary container for text content with section organization and metadata tracking. It's used throughout the `ai_text_processing` module for translation, summarization, and other AI-powered workflows.

**Current Pain Points**:

1. **Weak Section Validation**: `validate_sections()` (lines 359-372) only logs warnings and doesn't leverage NumberedText's boundary checking capabilities.

2. **Metadata Merge Ambiguity**: `merge_metadata()` (lines 324-352) has an `override` parameter but the semantics are confusing:
   ```python
   if override:
       self._metadata |= new_metadata  # new overrides existing
   else:
       self._metadata = new_metadata | self._metadata  # existing preserved
   ```
   - Which values win in nested dicts?
   - How are lists merged?
   - When should you use `override=True` vs `override=False`?

3. **Silent Metadata Loss**: No clear strategy for merging complex metadata structures (nested dicts, lists, provenance chains).

4. **No Provenance Chain**: Metadata operations don't track transformation history (who merged what when).

### Current Implementation

From `text_object.py:359-372`:

```python
def validate_sections(self) -> None:
    """Basic validation of section integrity."""
    if not self._sections:
        raise ValueError("No sections set.")

    # Check section ordering and bounds
    for i, section in enumerate(self._sections):
        if section.section_range.start < 1:
            logger.warning(f"Section {i}: start line must be >= 1")
        if section.section_range.start > self.num_text.size:
            logger.warning(f"Section {i}: start line exceeds text length")
        if i > 0 and \
            section.section_range.start <= self._sections[i-1].section_range.start:
            logger.warning(f"Section {i}: non-sequential start line")
```

**Problems**:
- Only logs warnings (doesn't raise exceptions)
- Doesn't check for gaps or overlaps
- Doesn't leverage NumberedText's validation (ADR-AT03.2)

From `text_object.py:324-352`:

```python
def merge_metadata(self, new_metadata: Metadata, override=False) -> None:
    """
    Merge new metadata with existing metadata.

    For now, performs simple dict-like union (|=) but can be extended
    to handle more complex merging logic in the future (e.g., merging
    nested structures, handling conflicts, merging arrays).
    """
    if not new_metadata:
        return

    if override:
        self._metadata |= new_metadata  # new overrides existing
    else:
        self._metadata = new_metadata | self._metadata # existing values preserved
```

**Problems**:
- `override` semantics unclear for nested structures
- No deep merging (nested dicts shallow-merged)
- No strategy for lists (append vs replace?)
- No provenance tracking

### Design Drivers

1. **Fail Fast**: Section validation should raise exceptions, not log warnings
2. **Leverage NumberedText**: Use ADR-AT03.2's validation methods
3. **Clear Merge Semantics**: Explicit strategies for common merge patterns
4. **Metadata Integrity**: Preserve provenance and transformation history
5. **Foundation for GenAI Integration**: Enable reliable metadata from GenAI Service (AT03 Tier 2)

---

## Decision

### 1. Enhanced Section Validation

Replace weak warning-based validation with robust boundary checking using NumberedText (ADR-AT03.2):

```python
# text_object.py

from dataclasses import dataclass

@dataclass
class SectionBoundaryError(Exception):
    """Section boundaries have gaps, overlaps, or out-of-bounds errors."""
    errors: List[Any]  # List of SectionValidationError from NumberedText
    coverage_report: dict[str, Any]

    def __init__(self, errors: List[Any], coverage_report: dict[str, Any]):
        self.errors = errors
        self.coverage_report = coverage_report

        # Build human-readable message
        error_msgs = [e.message for e in errors]
        message = (
            f"Section validation failed with {len(errors)} error(s):\\n" +
            "\\n".join(f"  - {msg}" for msg in error_msgs) +
            f"\\n\\nCoverage: {coverage_report['coverage_pct']:.1f}% " +
            f"({coverage_report['covered_lines']}/{coverage_report['total_lines']} lines)"
        )

        if coverage_report['gaps']:
            gap_ranges = [f"{start}-{end}" for start, end in coverage_report['gaps']]
            message += f"\\nGaps at lines: {', '.join(gap_ranges)}"

        if coverage_report['overlaps']:
            overlap_count = sum(len(o['lines']) for o in coverage_report['overlaps'])
            message += f"\\nOverlapping lines: {overlap_count}"

        super().__init__(message)


class TextObject:

    def validate_sections(self, raise_on_error: bool = True) -> Optional[List[Any]]:
        """Validate section integrity using NumberedText boundary checking.

        Args:
            raise_on_error: If True, raise SectionBoundaryError on validation failure.
                           If False, return error list (empty if valid).

        Returns:
            List of validation errors if raise_on_error=False, None otherwise.

        Raises:
            ValueError: If no sections are set
            SectionBoundaryError: If validation fails and raise_on_error=True

        Example:
            >>> obj = TextObject(num_text, sections=[...])
            >>> obj.validate_sections()  # Raises if invalid

            >>> errors = obj.validate_sections(raise_on_error=False)
            >>> if errors:
            ...     print(f"Found {len(errors)} validation errors")
        """
        if not self._sections:
            raise ValueError("No sections set.")

        # Extract start lines from sections
        start_lines = [section.section_range.start for section in self._sections]

        # Use NumberedText validation (from ADR-AT03.2)
        errors = self.num_text.validate_section_boundaries(start_lines)

        if errors:
            if raise_on_error:
                # Get detailed coverage report for diagnostics
                coverage_report = self.num_text.get_coverage_report(start_lines)
                raise SectionBoundaryError(errors, coverage_report)
            else:
                return errors

        return None if raise_on_error else []
```

**Design Notes**:

- **Leverages ADR-AT03.2**: Uses NumberedText's `validate_section_boundaries()` and `get_coverage_report()`
- **Fail-fast default**: Raises exception by default to catch errors early
- **Opt-in non-throwing**: Can return error list for batch validation scenarios
- **Rich diagnostics**: Exception includes coverage report with gap/overlap details

### 2. Explicit Metadata Merge Strategies

Replace ambiguous `override` parameter with explicit merge strategies:

```python
# text_object.py

from enum import Enum
from typing import Any

class MergeStrategy(Enum):
    """Strategy for merging metadata."""
    PRESERVE = "preserve"  # Keep existing values, ignore conflicts
    UPDATE = "update"      # New values override existing
    DEEP_MERGE = "deep"    # Deep merge nested dicts, append lists
    FAIL_ON_CONFLICT = "fail"  # Raise exception on key conflicts


class TextObject:

    def merge_metadata(
        self,
        new_metadata: Metadata,
        strategy: MergeStrategy = MergeStrategy.PRESERVE
    ) -> None:
        """Merge metadata with explicit strategy.

        Args:
            new_metadata: Metadata to merge
            strategy: Merge strategy (default: PRESERVE)

        Strategies:
            - PRESERVE: Keep existing values, only add new keys
            - UPDATE: New values override existing (shallow)
            - DEEP_MERGE: Recursively merge dicts, append lists
            - FAIL_ON_CONFLICT: Raise exception if keys overlap

        Raises:
            MetadataConflictError: If strategy=FAIL_ON_CONFLICT and keys overlap

        Example:
            >>> obj.merge_metadata(ai_metadata, strategy=MergeStrategy.UPDATE)
            >>> obj.merge_metadata(provenance, strategy=MergeStrategy.DEEP_MERGE)
        """
        if not new_metadata:
            return

        if strategy == MergeStrategy.PRESERVE:
            # Only add keys that don't exist
            for key, value in new_metadata.items():
                if key not in self._metadata:
                    self._metadata[key] = value

        elif strategy == MergeStrategy.UPDATE:
            # Shallow update: new values override existing
            self._metadata.update(new_metadata)

        elif strategy == MergeStrategy.DEEP_MERGE:
            # Deep merge nested structures
            self._metadata = self._deep_merge_metadata(
                self._metadata,
                new_metadata
            )

        elif strategy == MergeStrategy.FAIL_ON_CONFLICT:
            # Check for conflicts first
            conflicts = set(self._metadata.keys()) & set(new_metadata.keys())
            if conflicts:
                raise MetadataConflictError(
                    f"Metadata key conflicts: {conflicts}"
                )
            self._metadata.update(new_metadata)

        logger.debug(
            f"Merged metadata using {strategy.value} strategy: "
            f"{len(new_metadata)} keys"
        )

    @staticmethod
    def _deep_merge_metadata(base: dict, update: dict) -> dict:
        """Recursively merge metadata dictionaries.

        Rules:
            - Nested dicts: Recursively merge
            - Lists: Append update items to base (deduplicate)
            - Scalars: Update value overrides base value

        Args:
            base: Base metadata dict
            update: Update metadata dict

        Returns:
            Merged metadata dict
        """
        result = base.copy()

        for key, value in update.items():
            if key not in result:
                # New key: add directly
                result[key] = value

            elif isinstance(result[key], dict) and isinstance(value, dict):
                # Both dicts: recurse
                result[key] = TextObject._deep_merge_metadata(result[key], value)

            elif isinstance(result[key], list) and isinstance(value, list):
                # Both lists: append and deduplicate
                result[key] = list(dict.fromkeys(result[key] + value))

            else:
                # Scalar or type mismatch: override with update value
                result[key] = value

        return result
```

**Design Notes**:

- **Explicit strategies**: No ambiguity about merge behavior
- **Deep merge support**: Handles nested dicts and list appending
- **Fail-on-conflict option**: Enables strict metadata validation
- **Backward compatible**: Old `merge_metadata(override=True)` → `MergeStrategy.UPDATE`

### 3. Metadata Provenance Tracking

Add provenance chain to track metadata transformations:

```python
# text_object.py

from datetime import datetime
from typing import Optional

class TextObject:

    def merge_metadata(
        self,
        new_metadata: Metadata,
        strategy: MergeStrategy = MergeStrategy.PRESERVE,
        source: Optional[str] = None
    ) -> None:
        """Merge metadata with provenance tracking.

        Args:
            new_metadata: Metadata to merge
            strategy: Merge strategy
            source: Optional source identifier (e.g., 'genai_service', 'translation')
        """
        if not new_metadata:
            return

        # Perform merge (same logic as above)
        # ... (merge logic from section 2)

        # Track provenance
        if source:
            if '_provenance' not in self._metadata:
                self._metadata['_provenance'] = []

            self._metadata['_provenance'].append({
                'timestamp': datetime.utcnow().isoformat(),
                'source': source,
                'strategy': strategy.value,
                'keys_added': list(new_metadata.keys())
            })
```

**Design Notes**:

- **Opt-in provenance**: Only tracked if `source` provided
- **Transformation history**: Captures when, where, how metadata merged
- **Foundation for AT03 Tier 2**: GenAI Service can tag metadata with `source='genai_service'`

### 4. Backward Compatibility Helpers

Maintain compatibility with existing code during transition:

```python
# text_object.py

class TextObject:

    def merge_metadata_legacy(
        self,
        new_metadata: Metadata,
        override: bool = False
    ) -> None:
        """Legacy merge_metadata interface (deprecated).

        DEPRECATED: Use merge_metadata() with explicit MergeStrategy.

        Args:
            new_metadata: Metadata to merge
            override: If True, new values override (UPDATE strategy)
                     If False, existing values preserved (PRESERVE strategy)
        """
        import warnings
        warnings.warn(
            "merge_metadata(override=...) is deprecated. "
            "Use merge_metadata(strategy=MergeStrategy.UPDATE) instead.",
            DeprecationWarning,
            stacklevel=2
        )

        strategy = MergeStrategy.UPDATE if override else MergeStrategy.PRESERVE
        self.merge_metadata(new_metadata, strategy=strategy)
```

---

## Object-Service Conformance

### Alignment with ADR-OS01

This ADR positions TextObject to align with TNH Scholar's [Object-Service Architecture (ADR-OS01)](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md), specifically as a **domain service / orchestrator** component in the ai_text_processing subsystem.

#### Current State: Domain Model with Service Characteristics

**TextObject Today** (hybrid role):

From ADR-OS01 §3.1 Layer Structure:

| Layer | TextObject's Current Role |
|-------|---------------------------|
| **Domain Models** | ✅ Typed container for text + sections + metadata |
| **Service (Orchestrator)** | ⚠️ Partial: Coordinates NumberedText, Metadata, section management |
| Allowed Dependencies | ✅ Domain models only (NumberedText, Metadata) |

**Key Conformance Points (Current)**:

1. **Strong Typing** (OS01 §1.1): Uses Pydantic models (`LogicalSection`, `Metadata`)
2. **Config at init** (OS01 §4): Constructor accepts domain objects (not runtime config yet)
3. **Pure domain logic** (OS01 §3.2): No direct transport or infrastructure dependencies
4. **Explicit errors** (OS01 §8.7): Introduces `SectionBoundaryError`, `MetadataConflictError`

**Partial Conformance Issues**:

- ⚠️ **No Envelope pattern**: Methods return domain objects directly (not `Envelope`)
- ⚠️ **No Provenance**: Metadata tracked but not with OS01's `Provenance` model
- ⚠️ **Mixed concerns**: Contains both data model AND orchestration logic

#### Metadata Management as Internal Mapping

The new `merge_metadata()` strategies align with OS01 §8.8 "Internal Layer Adapters":

**Metadata Merge as Boundary Mapping**:

From OS01 §8.8:
> "Adapters and mappers are not just for translating vendor payloads—they are equally critical for translating between our own internal abstraction layers."

**TextObject's Metadata Merging**:

```python
# Current: Internal mapping between metadata layers
class TextObject:
    def merge_metadata(
        self,
        new_metadata: Metadata,
        strategy: MergeStrategy = MergeStrategy.PRESERVE,
        source: Optional[str] = None  # Provenance tracking!
    ) -> None:
        """Map metadata across processing boundaries."""
        # 1. Perform semantic translation (deep merge, conflict resolution)
        # 2. Track provenance (when, what, source)
        # 3. Maintain invariants (metadata integrity)
```

This follows OS01's principle:
> "Mapping makes these changes explicit... Internal mappers are the right place to inject policy decisions, provenance metadata, or safety checks as data crosses boundaries."

**Conformance**:

- ✅ **Pure mapper logic** (OS01 §8.6): `_deep_merge_metadata()` is pure (no I/O)
- ✅ **Provenance injection** (OS01 §8.8): `source` parameter enables tracking
- ✅ **Policy at boundaries** (OS01 §4.3): `MergeStrategy` is a domain policy

#### Future Evolution: Full Service Orchestrator

**Path to OS01 Compliance** (future ADR):

When TextObject becomes a full **Service Orchestrator** (like GenAIService):

```python
# Future: TextObject as Service Orchestrator (hypothetical)
class TextObjectService:
    """Service for creating and validating text objects."""

    def __init__(
        self,
        settings: Settings,
        validator: SectionValidator | None = None,
        metadata_policy: MetadataPolicy | None = None
    ):
        self.settings = settings
        self._validator = validator or NumberedTextValidator()
        self._policy = metadata_policy or MetadataPolicy()

    def create_from_ai_response(
        self,
        response: AIResponse,
        params: TextObjectParams | None = None
    ) -> Envelope:
        """Create TextObject from AI response with validation.

        Returns:
            Envelope with TextObject result or validation errors
        """
        # 1. Extract numbered text (domain model)
        num_text = NumberedText(response.content)

        # 2. Validate sections (uses ADR-AT03.2)
        start_lines = [s.start_line for s in response.sections]
        errors = num_text.validate_section_boundaries(start_lines)

        if errors:
            return Envelope(
                status="failed",
                error="Section validation failed",
                diagnostics={"validation_errors": [e.message for e in errors]},
                provenance=Provenance(
                    backend="ai_text_processing",
                    params={"response_hash": hash(response)}
                )
            )

        # 3. Build TextObject
        sections = self._build_sections(response.sections, num_text.size)
        text_obj = TextObject(
            num_text=num_text,
            language=response.language,
            sections=sections
        )

        # 4. Merge metadata with policy
        text_obj.merge_metadata(
            Metadata.from_yaml(response.document_metadata),
            strategy=self._policy.merge_strategy,
            source="ai_response"
        )

        # 5. Return envelope
        return Envelope(
            status="succeeded",
            result=text_obj,
            provenance=Provenance(
                backend="ai_text_processing",
                model=response.language,  # Or AI model used
                params={"strategy": self._policy.merge_strategy.value}
            )
        )
```

**Full OS01 Conformance**:

- ✅ **Config at init**: `Settings`, `MetadataPolicy` passed at construction
- ✅ **Params per call**: `params` per request (not global state)
- ✅ **Envelope always**: Returns `Envelope` with provenance
- ✅ **Protocol-based ports**: `SectionValidator` protocol for validation
- ✅ **Internal mapping**: Metadata merging as boundary translation
- ✅ **Provenance tracking**: `_provenance` chain in metadata
- ✅ **Typed errors**: `SectionBoundaryError` → `Envelope(status="failed")`

#### Integration with AT03 Refactor

**TextObject in AT03 Service Stack**:

```text
tnh-gen CLI (Application Layer)
  └─ TextProcessor (Orchestrator - AT03 Tier 1+2)
     └─ GenAIService.generate() → AIResponse
        └─ TextObjectService.create_from_ai_response()  [Future]
           └─ NumberedText.validate_section_boundaries()  [ADR-AT03.2]
           └─ TextObject.merge_metadata()                 [This ADR]

Envelope(
    status="succeeded",
    result=TextObject,
    provenance=Provenance(backend="ai_text_processing", ...)
)
```

**Current AT03 Implementation** (simpler):

For AT03's 1-2 week timeline, TextObject stays as **domain model with enhanced validation**:

- ✅ Enhanced validation (uses NumberedText from AT03.2)
- ✅ Explicit merge strategies (this ADR)
- ✅ Provenance tracking in metadata
- ❌ No Envelope wrapping (deferred to full platform)
- ❌ No Service protocol (deferred to AT04)

### TODO Reference

This work addresses **TODO.md Item #11** ("Improve NumberedText Ergonomics") and **TODO.md line 495-500** (object-service conformance for TextObject and NumberedText).

The metadata merge strategies and provenance tracking lay the groundwork for future full OS01 conformance when TextObject becomes a service orchestrator.

---

## Consequences

### Positive

- **Fail-Fast Validation**: Section errors caught immediately with detailed diagnostics
- **Clear Merge Semantics**: No ambiguity about metadata merge behavior
- **Deep Merge Support**: Handles complex nested metadata structures correctly
- **Provenance Tracking**: Metadata transformations traceable for debugging and audit
- **Foundation for GenAI**: Enables reliable metadata from GenAI Service (AT03 Tier 2)
- **Better Error Messages**: SectionBoundaryError includes coverage report with actionable details
- **Backward Compatible**: Legacy code continues working during transition

### Negative

- **Breaking Change**: `validate_sections()` now raises exceptions by default (can opt into old behavior with `raise_on_error=False`)
- **API Complexity**: Multiple merge strategies increase API surface
- **Migration Effort**: Existing calls to `merge_metadata(override=True)` need updating
- **Provenance Overhead**: Tracking adds metadata size (minimal impact)

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Breaking existing code** | Code relying on warning-only validation breaks | Gradual rollout; legacy helper methods |
| **Merge strategy confusion** | Users pick wrong strategy | Clear docstrings with examples; default to PRESERVE |
| **Performance regression** | Deep merge slower than shallow | Benchmark; optimize if needed (unlikely bottleneck) |
| **Provenance bloat** | Large provenance chains | Make provenance opt-in; add truncation after N entries |

---

## Alternatives Considered

### Alternative 1: Keep Warning-Only Validation

**Approach**: Leave `validate_sections()` as warnings, don't integrate NumberedText validation.

**Rejected**:
- Fails late (during content retrieval instead of validation)
- Doesn't leverage ADR-AT03.2's robust boundary checking
- Accumulates technical debt

### Alternative 2: Single "Smart" Merge Strategy

**Approach**: Auto-detect merge strategy based on metadata content.

**Rejected**:
- Magic behavior hard to debug
- Users lose explicit control
- Ambiguous in edge cases (what if metadata has both dicts and scalars?)

### Alternative 3: Immutable Metadata

**Approach**: Make Metadata immutable, return new instance on merge.

**Rejected**:
- Breaking change to existing code
- Performance overhead (copying large metadata)
- Doesn't align with current Metadata class design
- Can revisit in future ADR if needed

---

## Implementation Notes

### Phase 1: Section Validation Enhancement (Days 1-2)

1. Add `SectionBoundaryError` exception class
2. Update `validate_sections()` to use NumberedText validation
3. Add `raise_on_error` parameter for gradual migration
4. Unit tests:
   - Valid sections (no errors)
   - Invalid sections (gaps, overlaps, out-of-bounds)
   - Error message formatting
   - Non-throwing mode

### Phase 2: Metadata Merge Strategies (Days 3-4)

1. Add `MergeStrategy` enum
2. Implement new `merge_metadata()` with strategy parameter
3. Implement `_deep_merge_metadata()` helper
4. Add `merge_metadata_legacy()` for backward compatibility
5. Unit tests:
   - Each strategy with various metadata structures
   - Deep merge with nested dicts and lists
   - Conflict detection (FAIL_ON_CONFLICT)
   - Provenance tracking

### Phase 3: Integration (Day 5)

1. Update `from_response()` to use new validation (lines 292-322)
2. Update `from_info()` to validate sections (lines 399-415)
3. Integration tests:
   - AI-generated sections with validation
   - Metadata merging in realistic workflows
   - Provenance chains through multi-step processing

### Testing Strategy

**Unit Tests** (`tests/ai_text_processing/test_text_object_robustness.py`):

```python
def test_validate_sections_raises_on_gap():
    """validate_sections raises SectionBoundaryError on gaps."""
    num_text = NumberedText("\\n".join(f"line{i}" for i in range(1, 11)))
    sections = [
        SectionObject("Section 1", SectionRange(1, 5), None),
        SectionObject("Section 2", SectionRange(7, 11), None),  # Gap at line 6
    ]
    obj = TextObject(num_text, sections=sections)

    with pytest.raises(SectionBoundaryError) as exc_info:
        obj.validate_sections()

    assert "gap" in str(exc_info.value).lower()
    assert "line 6" in str(exc_info.value) or "lines 5-6" in str(exc_info.value)


def test_merge_metadata_deep_merge_nested_dicts():
    """Deep merge strategy merges nested dicts."""
    obj = TextObject(num_text, metadata=Metadata({
        'processing': {'stage': 'translation', 'model': 'gpt-4'},
        'tags': ['dharma']
    }))

    obj.merge_metadata(
        Metadata({
            'processing': {'version': '1.0'},
            'tags': ['teaching']
        }),
        strategy=MergeStrategy.DEEP_MERGE
    )

    assert obj.metadata['processing'] == {
        'stage': 'translation',
        'model': 'gpt-4',
        'version': '1.0'
    }
    assert set(obj.metadata['tags']) == {'dharma', 'teaching'}


def test_merge_metadata_provenance_tracking():
    """Provenance tracked when source provided."""
    obj = TextObject(num_text)
    obj.merge_metadata(
        Metadata({'model': 'gpt-4'}),
        source='genai_service'
    )

    assert '_provenance' in obj.metadata
    assert len(obj.metadata['_provenance']) == 1
    assert obj.metadata['_provenance'][0]['source'] == 'genai_service'
```

**Integration Tests**:

- TextObject creation from AIResponse with section validation
- Multi-step metadata merging (provenance chain)
- Error handling in realistic workflows

---

## Migration Path

### Phase 1: Add New APIs (Backward Compatible)

- Add new `merge_metadata()` with `strategy` parameter
- Keep old `merge_metadata()` signature working via deprecation wrapper
- Update `validate_sections()` but default to non-throwing mode

### Phase 2: Gradual Adoption

- Update internal `ai_text_processing` code to use new APIs
- Update tests to expect new behavior
- Add deprecation warnings to old methods

### Phase 3: Remove Legacy (Future)

- Remove `merge_metadata_legacy()` after 2-3 releases
- Switch `validate_sections()` to throwing by default

---

## Success Criteria

This ADR succeeds if:

1. **Validation robustness**: Section boundary errors caught with actionable diagnostics
2. **Merge clarity**: Developers understand which strategy to use for their use case
3. **Deep merge correctness**: Nested structures merged without data loss
4. **Provenance working**: GenAI Service integration can track metadata sources (AT03 Tier 2)
5. **Tests pass**: >95% code coverage for new validation and merge logic
6. **No regressions**: Existing workflows continue working during migration

---

## References

### Related ADRs

- **[ADR-AT03: Minimal AI Text Processing Refactor](/architecture/ai-text-processing/adr/adr-at03-object-service-refactor.md)** - Parent ADR (Tier 0: TextObject robustness)
- **[ADR-AT03.2: NumberedText Validation](/architecture/ai-text-processing/adr/adr-at03.2-numberedtext-validation.md)** - Sibling ADR (validation methods used here)
- **[ADR-AT03.1: Transition Plan](/architecture/ai-text-processing/adr/adr-at03.1-transition-plan.md)** - Implementation timeline
- **[ADR-AT02: TextObject Architecture](/architecture/ai-text-processing/adr/adr-at02-sectioning-textobject.md)** - Historical context

### Implementation Files

- **Current**: `src/tnh_scholar/ai_text_processing/text_object.py` - `merge_metadata()` and `validate_sections()` implementations
- **Dependency**: `src/tnh_scholar/text_processing/numbered_text.py` - NumberedText implementation

---

**Approval Path**: Architecture review → Implementation → Unit tests → Integration with ADR-AT03.2

*This ADR completes the TextObject robustness improvements (AT03 Tier 0) and establishes the foundation for GenAI Service integration (AT03 Tier 2) and prompt system adoption (AT03 Tier 3).*
