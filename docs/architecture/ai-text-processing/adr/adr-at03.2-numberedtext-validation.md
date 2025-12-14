---
title: "ADR-AT03.2: NumberedText Section Boundary Validation"
description: "Adds robust validation, coverage reporting, and gap/overlap detection to NumberedText to support reliable sectioning in ai_text_processing"
type: "design-detail"
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Sonnet 4.5"
status: accepted
created: "2025-12-12"
parent_adr: "adr-at03-object-service-refactor.md"
related_adrs: ["adr-at03.3-textobject-robustness.md", "adr-at03.1-transition-plan.md"]
---

# ADR-AT03.2: NumberedText Section Boundary Validation

Adds comprehensive section boundary validation, coverage reporting, and diagnostic capabilities to NumberedText to eliminate off-by-one errors and section gaps that currently block reliable text sectioning.

- **Status**: Accepted
- **Type**: Design Detail
- **Date**: 2025-12-12
- **Owner**: aaronksolomon
- **Author**: Aaron Solomon, Claude Sonnet 4.5
- **Parent ADR**: [ADR-AT03: Minimal AI Text Processing Refactor for tnh-gen](/architecture/ai-text-processing/adr/adr-at03-object-service-refactor.md)
- **Related ADRs**: [ADR-AT03.3: TextObject Robustness](/architecture/ai-text-processing/adr/adr-at03.3-textobject-robustness.md), [ADR-AT03.1: Transition Plan](/architecture/ai-text-processing/adr/adr-at03.1-transition-plan.md)

---

## Context

### The Problem

NumberedText is a foundational component in `src/tnh_scholar/text_processing/numbered_text.py` that provides line-numbered text handling with segment iteration capabilities. It's used extensively by TextObject (in `ai_text_processing` module) to manage section boundaries via `LogicalSection.start_line`.

**Current Pain Points**:

1. **Implicit End-Line Calculation**: Sections define only `start_line`, with end lines calculated implicitly as "next section's start - 1". This produces **off-by-one errors** when sections don't align properly.

2. **No Boundary Validation**: NumberedText has no built-in validation to detect:
   - **Gaps**: Uncovered lines between sections
   - **Overlaps**: Lines claimed by multiple sections
   - **Out-of-bounds**: Sections starting/ending outside valid line ranges

3. **Silent Failures**: When TextObject creates sections from AI responses, invalid boundaries pass through undetected until content retrieval fails with cryptic `IndexError` exceptions.

4. **Debugging Difficulties**: No diagnostic tools to visualize section coverage or identify problematic boundaries.

### Current Implementation

From `numbered_text.py:279-287`:

```python
def get_segment(self, start: int, end: int) -> str:
    """Return the segment from start line (inclusive) up to end line (inclusive)."""
    if start < self.start:
        raise IndexError(f"Start index {start} is before first line {self.start}")
    if end > self.end:
        raise IndexError(f"End index {end} is past last line {self.end}")
    if start > end:
        raise IndexError(f"Start index {start} must be less than or equal to end index {end}")
    return "\n".join(self.get_lines_exclusive(start, end + 1))
```

**Limitations**:

- Only validates individual segment requests
- No holistic validation of section coverage
- No reporting of gaps or overlaps
- Error messages lack context about section relationships

### Design Drivers

1. **Reliability First**: Eliminate silent failures in section boundary management
2. **Clear Diagnostics**: Provide actionable error messages with specific line numbers
3. **Non-Breaking**: Add validation capabilities without changing existing API contracts
4. **Foundation for AT03**: Enable TextObject robustness improvements (ADR-AT03.3)
5. **Debugging Support**: Provide tools for investigating section coverage issues

---

## Decision

### 1. Section Boundary Validation API

Add a new validation method to NumberedText that accepts a list of section start lines and validates complete coverage:

```python
# numbered_text.py

@dataclass
class SectionValidationError:
    """Error found in section boundaries."""
    error_type: str  # 'gap', 'overlap', 'out_of_bounds'
    section_index: int  # position in sorted order
    section_input_index: int  # original caller order
    expected_start: int
    actual_start: int
    message: str

class NumberedText:
    """Immutable container for numbered text lines."""

    def validate_section_boundaries(
        self,
        section_start_lines: List[int]
    ) -> List[SectionValidationError]:
        """Validate section boundaries for gaps, overlaps, out-of-bounds.

        Validates that sections defined by start lines provide complete,
        non-overlapping coverage of the text. End lines are implicit:
        each section ends at (next_section.start - 1), with the final
        section ending at the last line.

        Args:
            section_start_lines: List of section start line numbers (1-based)

        Returns:
            List of validation errors (empty if valid)

        Example:
            >>> text = NumberedText("line1\\nline2\\nline3\\nline4\\nline5")
            >>> # Valid: sections cover lines 1-3, 4-5
            >>> errors = text.validate_section_boundaries([1, 4])
            >>> len(errors)
            0

            >>> # Invalid: initial gap (first section starts at line 2)
            >>> errors = text.validate_section_boundaries([2, 5])
            >>> errors[0].error_type
            'gap'
        """
        errors = []

        if not section_start_lines:
            if self.size > 0:
                errors.append(SectionValidationError(
                    error_type='gap',
                    section_index=0,
                    section_input_index=-1,
                    expected_start=1,
                    actual_start=0,
                    message="No sections provided; expected first section at line 1"
                ))
            return errors

        # Sort but retain caller order for diagnostics
        sorted_with_idx = sorted(enumerate(section_start_lines), key=lambda t: t[1])

        # Verify first section starts at line 1
        first_idx, first_start = sorted_with_idx[0]
        if first_start != 1:
            errors.append(SectionValidationError(
                error_type='gap',
                section_index=0,
                section_input_index=first_idx,
                expected_start=1,
                actual_start=first_start,
                message=f"First section starts at {first_start}, "
                        f"leaving gap at lines 1-{first_start-1}"
            ))

        prev_start = first_start

        for i, (input_idx, start_line) in enumerate(sorted_with_idx):
            # Check out-of-bounds
            if start_line < 1 or start_line > self.size:
                errors.append(SectionValidationError(
                    error_type='out_of_bounds',
                    section_index=i,
                    section_input_index=input_idx,
                    expected_start=1 if start_line < 1 else self.size,
                    actual_start=start_line,
                    message=f"Section {i} start_line {start_line} "
                            f"out of bounds [1, {self.size}]"
                ))
                continue

            # Check for gaps/overlaps with previous section
            if i > 0:
                if start_line <= prev_start:
                    error_type = 'overlap'
                    errors.append(SectionValidationError(
                        error_type=error_type,
                        section_index=i,
                        section_input_index=input_idx,
                        expected_start=prev_start + 1,
                        actual_start=start_line,
                        message=f"Section {i} has {error_type}: "
                                f"expected start > {prev_start}, got {start_line}"
                    ))
                elif start_line > prev_start + 1:
                    error_type = 'gap'
                    errors.append(SectionValidationError(
                        error_type=error_type,
                        section_index=i,
                        section_input_index=input_idx,
                        expected_start=prev_start + 1,
                        actual_start=start_line,
                        message=f"Section {i} has {error_type}: "
                                f"expected start {prev_start + 1}, got {start_line}"
                    ))
                prev_start = start_line

        # Verify tail coverage reaches end of text
        last_start = sorted_with_idx[-1][1]
        if last_start > self.size:
            errors.append(SectionValidationError(
                error_type='out_of_bounds',
                section_index=len(sorted_with_idx) - 1,
                section_input_index=sorted_with_idx[-1][0],
                expected_start=self.size,
                actual_start=last_start,
                message=f"Final section starts at {last_start}, past last line {self.size}"
            ))

        return errors
```

**Design Notes**:

- **Accepts start lines only**: Matches TextObject's `LogicalSection` model (only `start_line` field)
- **Returns structured errors**: Enables programmatic error handling and detailed diagnostics
- **Non-throwing**: Returns error list instead of raising exceptions (allows batch validation)
- **1-based indexing**: Consistent with NumberedText's existing API
- **Full coverage required**: Enforces start at line 1 and rejects empty section lists for non-empty text
- **Caller-order diagnostics**: `section_input_index` preserves the original ordering for clearer error reporting

### 2. Coverage Reporting

Add a coverage report method for debugging and visualization:

```python
# numbered_text.py

class NumberedText:

    def get_coverage_report(
        self,
        section_start_lines: List[int]
    ) -> dict[str, Any]:
        """Get coverage statistics for section boundaries.

        Analyzes how sections (defined by start lines) cover the text,
        identifying gaps, overlaps, and coverage percentage.

        Args:
            section_start_lines: List of section start line numbers

        Returns:
            Dict with coverage info:
                - total_lines: Total line count
                - covered_lines: Number of lines in sections
                - coverage_pct: Percentage of lines covered
                - gaps: List of uncovered line ranges
                - overlaps: List of multiply-covered line ranges

        Example:
            >>> text = NumberedText("\\n".join(f"line{i}" for i in range(1, 11)))
            >>> report = text.get_coverage_report([1, 5])
            >>> report['coverage_pct']
            100.0
            >>> report['gaps']
            []
        """
        if not section_start_lines:
            return {
                'total_lines': self.size,
                'covered_lines': 0,
                'coverage_pct': 0.0,
                'gaps': [],
                'overlaps': []
            }

        sorted_starts = sorted(section_start_lines)
        covered = set()
        gaps = []
        overlaps = []

        # Build coverage from sections
        for i, start in enumerate(sorted_starts):
            # Calculate implicit end
            end = sorted_starts[i + 1] - 1 if i < len(sorted_starts) - 1 else self.size

            # Validate bounds
            if start < 1 or start > self.size:
                continue

            section_lines = set(range(start, min(end + 1, self.size + 1)))

            # Check for overlaps
            overlap = covered & section_lines
            if overlap:
                overlaps.append({
                    'section_index': i,
                    'lines': sorted(overlap)
                })

            covered.update(section_lines)

        # Find gaps
        all_lines = set(range(1, self.size + 1))
        gap_lines = all_lines - covered

        if gap_lines:
            # Group consecutive gaps into ranges
            sorted_gaps = sorted(gap_lines)
            current_gap_start = sorted_gaps[0]
            current_gap_end = sorted_gaps[0]

            for line in sorted_gaps[1:]:
                if line == current_gap_end + 1:
                    current_gap_end = line
                else:
                    gaps.append((current_gap_start, current_gap_end))
                    current_gap_start = line
                    current_gap_end = line

            # Add final gap
            gaps.append((current_gap_start, current_gap_end))

        return {
            'total_lines': self.size,
            'covered_lines': len(covered),
            'coverage_pct': len(covered) / self.size * 100 if self.size else 0,
            'gaps': gaps,
            'overlaps': overlaps
        }
```

**Design Notes**:

- **Debugging tool**: Provides human-readable coverage summary
- **Identifies gap ranges**: Groups consecutive uncovered lines
- **Overlap detection**: Shows which lines are claimed by multiple sections
- **JSON-serializable**: Dict output enables logging and reporting
- **Inclusive semantics**: Final section is assumed to run through `self.size`; gaps appear when start lines skip coverage or when no sections are provided for non-empty text

### 3. Integration with TextObject

TextObject will use these new methods during section validation (see ADR-AT03.3):

```python
# text_object.py (future state from ADR-AT03.3)

class TextObject:

    def validate_sections(self) -> None:
        """Enhanced validation using NumberedText boundary checking."""
        if not self._sections:
            raise ValueError("No sections set.")

        # Extract start lines from sections
        start_lines = [section.section_range.start for section in self._sections]

        # Validate boundaries using NumberedText
        errors = self.num_text.validate_section_boundaries(start_lines)

        if errors:
            # Build detailed error message
            error_msgs = [e.message for e in errors]

            # Get coverage report for debugging
            report = self.num_text.get_coverage_report(start_lines)

            raise SectionBoundaryError(
                f"Section validation failed with {len(errors)} errors:\\n" +
                "\\n".join(error_msgs) +
                f"\\n\\nCoverage: {report['coverage_pct']:.1f}% " +
                f"({report['covered_lines']}/{report['total_lines']} lines)"
            )
```

### 4. Compatibility

- New methods are **additive** (don't modify existing API surface)
- TextObject validation is **opt-in** (called explicitly in `validate_sections()`)
- **Breaking change**: `get_segment()` moves to inclusive end semantics to align with Monaco; callers must adjust (see Monaco alignment below).

**Migration Path**:

1. Add validation methods to NumberedText (this ADR)
2. Update TextObject to use validation (ADR-AT03.3)
3. Gradually adopt in other consumers (e.g., `ai_text_processing.py`)

---

## Object-Service Conformance

### Alignment with ADR-OS01

This ADR aligns NumberedText with TNH Scholar's [Object-Service Architecture (ADR-OS01)](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md) principles, specifically as a **domain model** component:

#### Domain Model Classification

**NumberedText as a Domain Model**:

From ADR-OS01 §3.1 Layer Structure:

| Layer | NumberedText's Role |
|-------|---------------------|
| **Domain Models** | ✅ Pure business object for line-numbered text |
| Allowed Dependencies | ✅ Nothing (pure data + validation logic) |
| Responsibility | ✅ Typed business objects with validation |

**Key Conformance Points**:

1. **Strong Typing** (OS01 §1.1): All methods use dataclasses (`SectionValidationError`) and typed returns
2. **No Side Effects** (OS01 §14 Rule 10): Validation methods are pure (no I/O, no state mutation)
3. **Explicit Errors** (OS01 §8.7): Returns structured `SectionValidationError` instead of raising exceptions
4. **Self-Contained** (OS01 §3.2): No dependencies on infrastructure or external services

#### Validation as Domain Logic

The validation methods (`validate_section_boundaries`, `get_coverage_report`) implement **domain invariants**:

- **Invariant**: Section boundaries must be contiguous and within bounds
- **Pure Functions**: No side effects, deterministic, testable in isolation
- **Structured Output**: Returns `List[SectionValidationError]` (not exceptions) for composability

This aligns with OS01's principle of "domain logic independent of infrastructure" (§3.2).

#### Integration with Object-Service Patterns

**NumberedText in the Service Stack**:

```text
TextObject (Domain Service - ADR-AT03.3)
  └─ Uses: NumberedText.validate_section_boundaries()  [Domain Model]
     └─ Returns: List[SectionValidationError]         [Domain Type]

GenAI Service (Service Layer - AT03 Tier 2)
  └─ Processes: TextObject with validated sections
     └─ Depends on: NumberedText invariants holding
```

**Conformance Notes**:

- ✅ **Config at init**: N/A (pure data model, no runtime config)
- ✅ **Params per call**: Validation methods accept `section_start_lines` per call
- ✅ **No literals**: All validation logic uses typed structures
- ✅ **Type safety**: All inputs/outputs strongly typed (Pydantic/dataclass)
- ✅ **Pure domain**: No transport, no adapters, no external dependencies

#### Future Object-Service Integration

When TextObject becomes a full **service orchestrator** (potential future ADR):

1. **NumberedText remains pure**: Continue as domain model with no infrastructure
2. **Validation as port**: TextObject could define `SectionValidator` protocol
3. **Adapter pattern**: Could support alternative validation strategies (strict vs lenient)
4. **Provenance**: Validation results could feed into `Envelope.diagnostics`

**Example Service Integration** (future):

```python
# Future: TextObject as Service Orchestrator
class TextObjectService:
    def __init__(
        self,
        validator: SectionValidator = NumberedTextValidator(),  # Adapter
        metadata_policy: MetadataPolicy = MetadataPolicy()
    ):
        self._validator = validator
        self._policy = metadata_policy

    def create_from_ai_response(self, response: AIResponse) -> Envelope:
        """Create TextObject with validation."""
        # Extract sections
        num_text = NumberedText(response.content)
        start_lines = [s.start_line for s in response.sections]

        # Validate (uses NumberedText domain logic)
        errors = num_text.validate_section_boundaries(start_lines)

        if errors:
            return Envelope(
                status="failed",
                error="Section validation failed",
                diagnostics={"validation_errors": errors},
                provenance=Provenance(backend="ai_text_processing")
            )

        # Success: create TextObject
        text_obj = TextObject(num_text, sections=...)
        return Envelope(
            status="succeeded",
            result=text_obj,
            provenance=Provenance(backend="ai_text_processing")
        )
```

### TODO Reference

This work addresses **TODO.md Item #11** ("Improve NumberedText Ergonomics") and lays the groundwork for full object-service conformance noted in **TODO.md line 495-500**.

---

## Monaco Editor Alignment

### VS Code UI Platform Integration

Per **[ADR-VSC01: VS Code Integration Strategy](/architecture/ui-ux/vs-code-integration/adr-vsc01-vscode-integration-strategy.md)**, TNH Scholar's future UI is built on VS Code extensions using Monaco Editor. NumberedText's range semantics are designed for **zero-translation compatibility** with Monaco's `IRange` interface.

#### Monaco Editor Range Semantics

Monaco Editor (VS Code's text editor engine) uses **1-based, inclusive ranges**:

```typescript
// Monaco Editor: microsoft/monaco-editor
interface IRange {
  startLineNumber: number;  // 1-based, inclusive
  startColumn: number;      // 1-based, inclusive
  endLineNumber: number;    // 1-based, INCLUSIVE
  endColumn: number;        // 1-based, inclusive
}
```

**Source**: [Monaco Editor IRange API](https://microsoft.github.io/monaco-editor/typedoc/interfaces/editor.IRange.html)

#### SectionRange Design (Monaco-Compatible)

```python
@dataclass(frozen=True)
class SectionRange:
    """Line range with inclusive start and end (Monaco Editor compatible).

    Designed for zero-translation compatibility with Monaco Editor's IRange.
    Both start_line and end_line are 1-based and INCLUSIVE, matching
    text editor semantics used in VS Code.

    Example:
        SectionRange(start_line=1, end_line=5)
        → Covers lines 1, 2, 3, 4, 5 (all inclusive)
        → Maps directly to Monaco { startLineNumber: 1, endLineNumber: 5 }

    Rationale:
        - Zero-copy mapping to VS Code extension (ADR-VSC01)
        - Matches text editor user mental model
        - Eliminates off-by-one errors in UI integration
        - Enables JVB Viewer V2 webview with Monaco editor
    """
    start_line: int  # 1-based, inclusive
    end_line: int    # 1-based, INCLUSIVE (Monaco Editor compatible)
```

#### VS Code Extension Integration (Zero Translation)

```typescript
// VS Code Extension: Direct mapping (no conversion needed!)
import * as monaco from 'monaco-editor';

interface PythonSection {
  range: { start_line: number; end_line: number };
  title: string;
}

function toMonacoRange(section: PythonSection): monaco.IRange {
  return {
    startLineNumber: section.range.start_line,  // Direct copy
    startColumn: 1,
    endLineNumber: section.range.end_line,      // Direct copy
    endColumn: Number.MAX_VALUE                  // Full line
  };
}

// Highlight section in VS Code editor
function highlightSection(
  editor: monaco.editor.IStandaloneCodeEditor,
  section: PythonSection
) {
  editor.createDecorationsCollection([{
    range: toMonacoRange(section),
    options: {
      isWholeLine: true,
      className: 'tnh-section-highlight',
      hoverMessage: { value: section.title }
    }
  }]);
}
```

#### Internal Python Range Conversion

For internal iteration, convert inclusive range to Python's exclusive range:

```python
# numbered_text.py (internal implementation)
def get_segment(self, start_line: int, end_line: int) -> str:
    """Get text segment with inclusive end (Monaco-compatible).

    Args:
        start_line: 1-based start (inclusive)
        end_line: 1-based end (INCLUSIVE)

    Returns:
        Text segment as string

    Note:
        Internally converts to Python's exclusive range semantics.
    """
    if start_line < 1 or start_line > self.size:
        raise IndexError(f"start_line {start_line} out of bounds [1, {self.size}]")
    if end_line < start_line or end_line > self.size:
        raise IndexError(f"end_line {end_line} invalid (must be in [{start_line}, {self.size}])")

    # Convert inclusive end to Python range (exclusive upper bound)
    return "\n".join(self.get_lines_exclusive(start_line, end_line + 1))
```

#### Validation Logic Adjustment

Gap detection accounts for inclusive semantics:

```python
def validate_section_boundaries(
    self,
    section_start_lines: List[int]
) -> List[SectionValidationError]:
    """Validate section boundaries (inclusive end semantics).

    With inclusive end lines, contiguous sections satisfy:
        section[i].end_line + 1 == section[i+1].start_line
    """
    errors = []
    sorted_starts = sorted(section_start_lines)

    for i in range(1, len(sorted_starts)):
        # Calculate previous section's implicit end (next start - 1)
        prev_end = sorted_starts[i] - 1

        # Expected next start is prev_end + 1
        expected_start = prev_end + 1
        actual_start = sorted_starts[i]

        if actual_start != expected_start:
            # Gap or overlap detected
            error_type = 'gap' if actual_start > expected_start else 'overlap'
            errors.append(SectionValidationError(
                error_type=error_type,
                section_index=i,
                expected_start=expected_start,
                actual_start=actual_start,
                message=f"Section {i} {error_type}: expected {expected_start}, got {actual_start}"
            ))

    return errors
```

### Benefits of Monaco Alignment

1. **Zero-Copy UI Integration**: No range translation in VS Code extension
2. **Reduced Bug Surface**: Eliminates off-by-one errors in UI layer
3. **User Mental Model**: Matches text editor paradigm (line 5 means "line 5", not "up to line 5")
4. **Future-Proof**: Compatible with Monaco updates (stable API since 2016)
5. **Cross-Platform**: Enables custom webviews (JVB Viewer) and VS Code extensions

### Implementation Impact

**Files Modified**:

- `numbered_text.py`: Update `get_segment()` to accept inclusive end and enforce full coverage to end-of-text
- `text_object.py`: Update `SectionRange` to use inclusive `end_line`
- Validation logic: Adjust contiguity checks for inclusive semantics

**Migration**: Minimal - `SectionRange` is internal to ai_text_processing module.

---

## Consequences

### Positive

- **Early Error Detection**: Section boundary errors caught at validation time, not during content retrieval
- **Clear Diagnostics**: Structured error messages with specific line numbers and error types
- **Debugging Support**: Coverage reports help investigate complex sectioning issues
- **Foundation for Robustness**: Enables TextObject to guarantee valid section boundaries
- **Non-Breaking**: Existing code continues to work unchanged
- **Testable**: Validation logic is pure (no side effects), easy to unit test

### Negative

- **Performance Overhead**: Validation requires O(n) iteration over sections (acceptable for typical use)
- **Memory Allocation**: Coverage reporting builds sets of line numbers (negligible for documents <100K lines)
- **API Surface Growth**: Adds two new public methods to NumberedText

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Performance regression** | Validation slows down large documents | Only validate when explicitly called; add benchmarks |
| **Incomplete validation** | Edge cases slip through | Comprehensive unit tests with boundary cases |
| **API confusion** | Users unsure when to validate | Clear docstrings with examples; integration guide |

---

## Alternatives Considered

### Alternative 1: Validate in get_segment() Only

**Approach**: Add gap/overlap detection to existing `get_segment()` method.

**Rejected**:

- Can't detect gaps until they're accessed (fails late)
- No holistic view of section coverage
- Harder to provide actionable diagnostics

### Alternative 2: Explicit End Lines

**Approach**: Change `LogicalSection` to include explicit `end_line` field.

**Rejected**:

- Breaking change to existing data model
- Increases complexity (must validate end > start for every section)
- Doesn't solve the root problem (still need boundary validation)
- Deferred to potential future ADR-AT02 revisit

### Alternative 3: Custom Section Class in NumberedText

**Approach**: Create a `Section` class in NumberedText that encapsulates start/end.

**Rejected**:

- Couples NumberedText to sectioning concept (reduces reusability)
- Duplicates `LogicalSection` from TextObject
- Over-engineers for current needs

---

## Implementation Notes

### Phase 1: Core Validation (Days 1-2)

1. Add `SectionValidationError` dataclass
2. Implement `validate_section_boundaries()`
3. Add unit tests for validation:
   - Valid contiguous sections
   - Gaps (start > 1, gaps between sections)
   - Overlaps (sections with same start, overlapping ranges)
   - Out-of-bounds (start < 1, start > size)

### Phase 2: Coverage Reporting (Day 3)

1. Implement `get_coverage_report()`
2. Add unit tests for coverage:
   - Full coverage (100%)
   - Partial coverage with gaps
   - Multiple overlapping sections
   - Empty section list

### Phase 3: Integration (Day 4)

1. Update TextObject.validate_sections() to use new methods (see ADR-AT03.3)
2. Integration tests with realistic AI-generated section boundaries
3. Update documentation with validation examples

### Testing Strategy

**Unit Tests** (`tests/text_processing/test_numbered_text_validation.py`):

```python
def test_validate_section_boundaries_valid_contiguous():
    """Validate contiguous sections covering all lines."""
    text = NumberedText("\\n".join(f"line{i}" for i in range(1, 11)))
    errors = text.validate_section_boundaries([1, 5, 8])
    assert len(errors) == 0

def test_validate_section_boundaries_gap():
    """Detect gap between sections."""
    text = NumberedText("\\n".join(f"line{i}" for i in range(1, 11)))
    errors = text.validate_section_boundaries([1, 5, 9])  # Gap at line 8
    assert len(errors) == 1
    assert errors[0].error_type == 'gap'
    assert errors[0].section_index == 2
    assert errors[0].expected_start == 8

def test_coverage_report_full():
    """Coverage report for complete section coverage."""
    text = NumberedText("\\n".join(f"line{i}" for i in range(1, 11)))
    report = text.get_coverage_report([1, 6])
    assert report['coverage_pct'] == 100.0
    assert len(report['gaps']) == 0
```

**Integration Tests** (in ADR-AT03.3):

- TextObject creation from AIResponse with invalid sections
- Validation error messages for debugging
- Coverage reports logged during development

---

## Success Criteria

This ADR succeeds if:

1. **Validation catches all error types**: Gap, overlap, out-of-bounds errors detected
2. **Clear error messages**: Developers can identify and fix boundary issues from error output
3. **No performance regression**: Validation completes in <10ms for 10K line documents
4. **Tests pass**: >95% code coverage for validation methods
5. **Integration ready**: TextObject can adopt validation without breaking changes (ADR-AT03.3)
6. **Documentation clear**: Examples in docstrings enable developers to use validation effectively

---

## References

### Related ADRs

- **[ADR-AT03: Minimal AI Text Processing Refactor](/architecture/ai-text-processing/adr/adr-at03-object-service-refactor.md)** - Parent ADR (Tier 0: NumberedText robustness)
- **[ADR-AT03.3: TextObject Robustness](/architecture/ai-text-processing/adr/adr-at03.3-textobject-robustness.md)** - Sibling ADR (uses these validation methods)
- **[ADR-AT03.1: Transition Plan](/architecture/ai-text-processing/adr/adr-at03.1-transition-plan.md)** - Implementation timeline
- **[ADR-AT02: TextObject Architecture](/architecture/ai-text-processing/adr/adr-at02-sectioning-textobject.md)** - Historical context on section design

### Implementation Files

- **Current**: `src/tnh_scholar/text_processing/numbered_text.py` - `get_segment()` implementation
- **Consumer**: `src/tnh_scholar/ai_text_processing/text_object.py` - `validate_sections()`

---

**Approval Path**: Architecture review → Implementation → Unit tests → Integration with ADR-AT03.3

*This ADR provides the foundational validation capabilities that enable TextObject robustness (ADR-AT03.3) and support reliable sectioning in the ai_text_processing module.*

---

## Addendum 2025-12-13: Validation Contract Clarification

### Background Context

During implementation review, a question arose about whether `validate_section_boundaries` should detect "trailing gaps" - cases where the final section might not reach `self.end`.

### Analysis and Decision

After reviewing the design specification (lines 364-370) and implementation (`numbered_text.py:384-422`), we confirmed that **no trailing gap detection is needed** because:

**By design**: The final section always implicitly ends at `self.end`. From the original decision (§2.1):

> "the end of each section is implicit: it ends at the line before the next section starts, **with the final section ending at the last line of the text**"

This means the last section's end is **defined** as `self.end`, not calculated from boundaries. Therefore, "trailing gaps" cannot exist under the current design contract.

**What the validator guarantees**:

1. First section starts at `self.start` (no initial gap)
2. Each section starts exactly one line after the previous section's implicit end (no inter-section gaps)
3. No sections overlap
4. All sections are within bounds

Together, these rules ensure complete contiguous coverage from `self.start` to `self.end`.

**Example validating full coverage**:

```python
text = NumberedText("line1\nline2\nline3\nline4\nline5")  # 5 lines, self.end = 5
errors = text.validate_section_boundaries([1, 4])
# Section 1: lines 1-3 (implicit end = 4-1 = 3)
# Section 2: lines 4-5 (implicit end = self.end = 5)
# No gaps → validation passes ✓
```

### Implementation Status

**No code changes required**. The current implementation correctly enforces the validation contract as designed.

### Related Artifacts

- **GitHub Issue**: [#20 - NumberedText.validate_section_boundaries misses trailing coverage gaps](https://github.com/aaronksolomon/tnh-scholar/issues/20)
  - Resolution: Closed as "working as designed" with contract clarification
- **Original Design**: Section §2.1 (lines 105-111, 364-370)
- **Implementation**: `src/tnh_scholar/text_processing/numbered_text.py:384-422`
