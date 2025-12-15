---
title: "TNH Scholar Design Principles"
description: "Architectural patterns, design philosophy, and system organization principles for TNH Scholar development."
owner: ""
author: ""
status: current
created: "2025-11-29"
---
# TNH Scholar Design Principles

Architectural patterns, design philosophy, and system organization principles for TNH Scholar development.

## Overview

This document establishes design principles for the TNH Scholar project. While the project is currently in a rapid prototyping phase, these guidelines aim to maintain architectural quality and consistency throughout development. The guide distinguishes between immediate prototyping requirements and standards for later production phases where appropriate.

For code formatting and naming conventions, see [Style Guide](/development/style-guide.md). For high-level project philosophy and vision, see [Project Principles](/project/principles.md) and [Conceptual Architecture](/project/conceptual-architecture.md).

## Core Design Philosophy

The TNH Scholar system embraces several key philosophical principles:

- **Evolutionary improvement** through self-generated training data
- **Modular design** enabling flexible pipeline construction
- **Balance of rapid prototyping with extensible architecture**
- **Focus on AI-enhanced content processing and transformation**

See [Project Philosophy](/project/philosophy.md) for deeper context.

## Fundamental Principles

### Single Responsibility

Code should adhere to the **principle of single responsibility**, with functions and classes focused on one clear task:

- Functions perform one logical operation
- Classes manage related state or behavior
- Modules encapsulate coherent functionality
- Services handle one domain concern

### Composition Over Inheritance

**Favor composition over inheritance** to build complex behavior from simple, reusable components:

```python
# ✅ Preferred: Composition
class TextPipeline:
    def __init__(
        self,
        punctuator: PunctuationService,
        translator: TranslationService,
        sectioner: SectioningService
    ):
        self.punctuator = punctuator
        self.translator = translator
        self.sectioner = sectioner

# 🚫 Avoid: Deep inheritance hierarchies
class TranslatingPunctuatingSectioningProcessor(
    PunctuationProcessor,
    TranslationProcessor,
    SectioningProcessor
):
    pass
```

### Separation of Concerns

**Validation logic should be distinct from mutation or side effects** to ensure maintainability:

```python
# ✅ Preferred: Separate concerns
def validate_text_input(text: str) -> None:
    """Validate input only."""
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

def process_text(text: str) -> ProcessedText:
    """Process after validation."""
    validate_text_input(text)
    return apply_processing(text)

# 🚫 Avoid: Mixed concerns
def process_text(text: str) -> ProcessedText:
    """Validation, mutation, and I/O all mixed."""
    if not text:
        raise ValueError("Empty")
    result = apply_processing(text)
    save_to_database(result)  # Side effect mixed with processing
    return result
```

## Modularity Principles

### Design for Modularity

Each module, class, and function should have a **single, well-defined responsibility**.

**Guidelines:**

- **Encapsulate related functionality**: Group related functions and classes into modules and packages to promote reuse and clarity
- **Minimize coupling**: Modules should interact through well-defined interfaces, minimizing dependencies and side effects
- **Limit module size**: Aim for modules that are small enough to be easily understood (generally < 300 lines), but large enough to encapsulate a coherent set of functionality
- **Explicit module exports**: Use `__all__` to define public API of modules where appropriate

### Helpers Should Be Small and Composable

Helpers should be small (target **10 lines**) and composable, enabling reuse and clarity:

```python
# ✅ Preferred: Small, composable helpers
def extract_language_code(text_object: TextObject) -> str:
    """Extract language code from text object."""
    return text_object.metadata.get("language", "en")

def validate_language_code(code: str) -> None:
    """Validate ISO 639-1 language code."""
    if len(code) != 2 or not code.isalpha():
        raise ValueError(f"Invalid language code: {code}")

def get_validated_language(text_object: TextObject) -> str:
    """Get and validate language code."""
    code = extract_language_code(text_object)
    validate_language_code(code)
    return code

# 🚫 Avoid: Large, monolithic helpers
def process_and_validate_language_with_fallback_and_logging(
    text_object: TextObject,
    default: str = "en"
) -> str:
    """Do everything in one place (50+ lines)."""
    # ... lots of mixed logic
```

### Stateful Iteration Loops Use Classes

**When iteration logic requires complex state management, use a dedicated class** to encapsulate state and dispatch to methods:

```python
# ✅ Preferred: Stateful validation as a class
class _SectionBoundaryValidator:
    """Stateful validator for clean, readable loop logic."""

    def __init__(self, owner: "NumberedText", section_start_lines: List[int]) -> None:
        self.owner = owner
        self.section_start_lines = section_start_lines
        self.errors: List[SectionValidationError] = []
        self.prev_start: Optional[int] = None
        self.first_valid_seen = False

    def run(self) -> List[SectionValidationError]:
        """Main loop stays simple by dispatching to focused methods."""
        if not self.section_start_lines:
            return self.owner._errors_for_no_sections()

        sorted_with_idx = sorted(enumerate(self.section_start_lines), key=lambda t: t[1])

        for section_index, (input_idx, start_line) in enumerate(sorted_with_idx):
            if self.owner._is_out_of_bounds(start_line):
                self.errors.append(
                    self.owner._error_out_of_bounds(section_index, input_idx, start_line)
                )
                continue

            if not self.first_valid_seen:
                self._handle_first(section_index, input_idx, start_line)
                continue

            self._handle_body(section_index, input_idx, start_line)

        return self.errors

    def _handle_first(self, section_index: int, input_idx: int, start_line: int) -> None:
        """Handle first valid section."""
        self.errors.extend(
            self.owner._errors_for_first_section(section_index, input_idx, start_line)
        )
        self.first_valid_seen = True
        self.prev_start = start_line

    def _handle_body(self, section_index: int, input_idx: int, start_line: int) -> None:
        """Handle subsequent sections."""
        assert self.prev_start is not None
        if start_line <= self.prev_start:
            self.errors.append(
                self.owner._error_overlap(section_index, input_idx, self.prev_start, start_line)
            )
        elif start_line > self.prev_start + 1:
            self.errors.append(
                self.owner._error_gap(section_index, input_idx, self.prev_start, start_line)
            )
        self.prev_start = start_line

# Public API stays clean:
def validate_section_boundaries(
    self, section_start_lines: List[int]
) -> List[SectionValidationError]:
    """Validate section boundaries for gaps, overlaps, and out-of-bounds errors."""
    return self._SectionBoundaryValidator(self, section_start_lines).run()

# 🚫 Avoid: Complex state in procedural loop
def validate_section_boundaries(
    self, section_start_lines: List[int]
) -> List[SectionValidationError]:
    """Procedural loop with hard-to-follow state management."""
    errors = []
    prev_start = None
    first_valid_seen = False

    # 50+ lines of nested conditionals, state mutations, and edge cases
    # Hard to test individual logic branches
    # Difficult to understand control flow
    for section_index, (input_idx, start_line) in enumerate(sorted_with_idx):
        if out_of_bounds:
            # complex logic here
            pass
        elif not first_valid_seen:
            # complex logic here
            first_valid_seen = True
            prev_start = start_line
        else:
            # more complex logic here
            prev_start = start_line

    return errors
```

**Benefits:**

- **Readability**: Main loop logic is clean and straightforward
- **Testability**: Each method can be tested independently
- **Maintainability**: State is explicit and localized
- **Debuggability**: Clear method boundaries for breakpoints and logging

**When to use:**

- Validation loops with complex state tracking
- Multi-pass parsers with lookahead/lookbehind
- State machines with transitions
- Iterative algorithms that accumulate results based on conditions

**Implementation notes:**

- Use private nested classes (`_ValidatorClass`) for internal-only validators
- Keep the main loop in a `run()` method for clear entry point
- Dispatch to focused helper methods (`_handle_first`, `_handle_body`, etc.)
- Initialize all state in `__init__` for explicitness

## Interface Design

### Abstract Base Classes and Protocols

**All system interfaces must be defined via abstract base classes:**

- Use **`Protocol`** for structural typing and interface contracts (no inheritance required)
- Use **`ABC`** only when enforcing init-time invariants or providing shared mixin behavior

**Example with Protocol:**

```python
from typing import Protocol

class PromptProvider(Protocol):
    """Protocol for prompt providers."""

    def get_prompt(self, name: str) -> Prompt:
        """Retrieve prompt by name."""
        ...

    def list_prompts(self) -> list[str]:
        """List available prompt names."""
        ...
```

**Example with ABC:**

```python
from abc import ABC, abstractmethod

class BaseProcessor(ABC):
    """Base processor with shared initialization."""

    def __init__(self, config: ProcessorConfig):
        self.config = config
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate configuration at init time."""
        pass

    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """Process input data."""
        pass
```

### Dependency Injection

**Prefer dependency injection over global state:**

```python
# ✅ Preferred: Dependency injection
class TextProcessor:
    def __init__(
        self,
        prompt_catalog: PromptCatalog,
        ai_service: GenAIService
    ):
        self.prompt_catalog = prompt_catalog
        self.ai_service = ai_service

# 🚫 Avoid: Global singleton access
class TextProcessor:
    def process(self, text: str) -> str:
        prompt = LocalPromptManager().get_prompt("default")  # Global access
        return global_ai_service.process(text, prompt)  # Global access
```

**Note**: During prototyping, singleton access (like `LocalPromptManager`) is acceptable for rapid development. Plan transition to dependency injection for production (see ADR-PT01 in Historical References below).

## Data Architecture

### Immutability by Default

**Keep data models immutable** when possible for safer concurrent code:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ProcessingResult:
    """Immutable processing result."""
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
```

### Strong Type Boundaries

**Critical**: No literals or untyped structures in application logic:

- Configuration values come from `Settings` (pydantic BaseSettings)
- **Dicts are not used in app layers**; prefer Pydantic models or dataclasses
- Enums replace string literals for identifiers
- Adapters handle dict conversions **only at API transport boundaries**

See [Style Guide: Strong Typing Standards](/development/style-guide.md) for details.

### Choosing Between Pydantic Models and Plain Python Classes

**Default to Pydantic v2 `BaseModel` for domain models**, but use plain Python classes when Pydantic introduces significant friction.

#### When to Use Pydantic BaseModel

**Pydantic excels at:**

- **Data Transfer Objects (DTOs)**: Serialization/deserialization for APIs, JSON persistence, configuration
- **Simple domain models**: Data containers with straightforward validation
- **Transport layer models**: API requests/responses, file format schemas
- **Configuration models**: Settings with validation and environment variable parsing

**Example - Ideal Pydantic usage:**

```python
from pydantic import BaseModel, Field, ConfigDict

class TextObjectInfo(BaseModel):
    """Serializable DTO for TextObject persistence."""
    model_config = ConfigDict(frozen=True)

    source_file: Path | None = None
    language: str
    sections: list[SectionObject]
    metadata: Metadata

    # Clean serialization:
    # info.model_dump_json() → JSON file
    # TextObjectInfo.model_validate_json(json_str) → instance
```

#### When NOT to Use Pydantic BaseModel

**Use plain Python classes when the domain model has:**

1. **Custom iteration semantics that conflict with Pydantic's `__iter__`**
   - Pydantic's `BaseModel.__iter__` yields `(field_name, value)` for dict-like iteration
   - Domain-specific iteration (e.g., iterating over sections, lines, entries) requires `# type: ignore[override]`
   - This signals a semantic mismatch

2. **Core dependencies that are non-Pydantic types**
   - When using `arbitrary_types_allowed=True` for most fields
   - Defeats Pydantic's validation benefits
   - Example: Model wrapping `NumberedText` (plain class) and `Metadata` (MutableMapping)

3. **Complex initialization requiring multiple validation hooks**
   - Needing both `@model_validator(mode="before")` AND `model_post_init`
   - Suggests Pydantic's lifecycle doesn't match domain needs
   - Plain class with explicit `__init__` is clearer

4. **Rich domain behavior beyond data validation**
   - Complex stateful operations
   - Multiple internal state transitions
   - Custom protocols that don't align with Pydantic's model lifecycle

**Example - When plain class is better:**

```python
# ✅ Preferred: Plain Python class for rich domain model
class TextObject:
    """Rich domain model with complex behavior (NOT a Pydantic model)."""

    def __init__(
        self,
        num_text: NumberedText,  # Non-Pydantic type
        language: str | None = None,
        sections: list[SectionObject] | None = None,
        metadata: Metadata | None = None,  # MutableMapping, not Pydantic
    ):
        self.num_text = num_text
        self.language = language or get_language_code_from_text(num_text.content)
        self.sections = sections or []
        self.metadata = metadata or Metadata()

        if self.sections:
            self.validate_sections()  # Complex validation

    def __iter__(self) -> Iterator[SectionEntry]:
        """Domain-specific iteration - clean, no type: ignore needed."""
        for i, section in enumerate(self.sections):
            content = self.num_text.get_segment(section.section_range.start, section.section_range.end)
            yield SectionEntry(number=i + 1, title=section.title, content=content)

    def export_info(self) -> TextObjectInfo:
        """Convert to Pydantic DTO for serialization."""
        return TextObjectInfo(
            source_file=self.source_file,
            language=self.language,
            sections=self.sections,
            metadata=self.metadata
        )

    @classmethod
    def from_info(cls, info: TextObjectInfo, num_text: NumberedText) -> "TextObject":
        """Create from Pydantic DTO."""
        return cls(
            num_text=num_text,
            language=info.language,
            sections=info.sections,
            metadata=info.metadata
        )

# 🚫 Avoid: Forcing Pydantic when it doesn't fit
class TextObject(BaseModel):
    """Pydantic model with significant friction."""
    model_config = ConfigDict(arbitrary_types_allowed=True)  # Red flag

    num_text: NumberedText  # Requires arbitrary_types_allowed
    metadata: Metadata  # Requires coercion in @model_validator + model_post_init

    @model_validator(mode="before")
    @classmethod
    def _coerce_metadata(cls, data: Any) -> Any:
        """Complex pre-validation coercion needed."""
        # ... complex logic

    def model_post_init(self, __context: Any) -> None:
        """More complex post-init coercion needed."""
        # ... more complex logic

    def __iter__(self) -> Iterator[SectionEntry]:  # type: ignore[override]
        """Domain iteration conflicts with Pydantic's __iter__."""
        # ... requires type: ignore
```

#### Hybrid Pattern: Separate Domain Model and DTO

**Best of both worlds** - use plain class for domain logic, Pydantic for serialization:

```python
# Domain model: Plain Python class
class TextObject:
    """Rich domain model with complex behavior."""

    def __init__(self, num_text: NumberedText, ...):
        # ... domain logic

    def __iter__(self) -> Iterator[SectionEntry]:
        # Clean domain-specific iteration
        ...

    def export_info(self) -> TextObjectInfo:
        """Convert to DTO for persistence."""
        return TextObjectInfo(...)

# DTO: Pydantic model for serialization
class TextObjectInfo(BaseModel):
    """Serializable snapshot of TextObject state."""
    source_file: Path | None
    language: str
    sections: list[SectionObject]
    metadata: Metadata
```

**Benefits:**

- **Separation of concerns**: Domain logic separate from serialization
- **Type safety**: Pydantic validates DTOs, domain model handles business logic
- **Clean APIs**: Each class has a clear, focused purpose
- **No friction**: No `# type: ignore`, no `arbitrary_types_allowed`, no dual validators

#### Decision Checklist

**Use Pydantic BaseModel if:**

- ✅ Primary purpose is data validation or serialization
- ✅ Simple field-based model without complex initialization
- ✅ All fields are Pydantic-compatible types
- ✅ No custom iteration semantics needed

**Use plain Python class if:**

- ✅ Model has rich domain behavior beyond data validation
- ✅ Custom `__iter__` conflicts with Pydantic's field iteration
- ✅ Core fields require `arbitrary_types_allowed`
- ✅ Initialization needs complex multi-step validation
- ✅ Model wraps non-Pydantic core types (NumberedText, custom collections)

**Consider hybrid pattern if:**

- ✅ Domain model is complex BUT needs serialization
- ✅ Want clean separation between domain logic and persistence
- ✅ Multiple serialization formats needed (JSON, YAML, database)

**See also:**

- **[ADR-AT03.3 Addendum 2025-12-14](/architecture/ai-text-processing/adr/adr-at03.3-textobject-robustness.md)**: Real-world example of reverting Pydantic adoption after identifying friction
- **Examples in codebase:**
  - Plain classes: [NumberedText](../../src/tnh_scholar/text_processing/numbered_text.py), [Metadata](../../src/tnh_scholar/metadata/metadata.py), TextObject (after ADR-AT03.3 revision)
  - Pydantic DTOs: [TextObjectInfo](../../src/tnh_scholar/ai_text_processing/text_object.py), [LogicalSection](../../src/tnh_scholar/ai_text_processing/text_object.py)
  - Pydantic domain models: [AIResponse](../../src/tnh_scholar/ai_text_processing/text_object.py), [CompletionResult](../../src/tnh_scholar/gen_ai_service/models/domain.py)

### Separation of Data and Logic

**Separate data representation from business logic** where appropriate:

```python
# ✅ Preferred: Data models separate from services
@dataclass
class PromptMetadata:
    """Data model."""
    name: str
    version: str
    variables: list[str]

class PromptService:
    """Business logic."""
    def render_prompt(self, metadata: PromptMetadata, context: Dict) -> str:
        ...

# 🚫 Avoid: Mixed data and complex logic
class Prompt:
    def __init__(self, name: str):
        self.name = name
        # ... lots of fields

    def render_with_ai_fallback_and_caching(self, context: Dict) -> str:
        # ... 100 lines of business logic in data class
```

## Error Handling Philosophy

### Explicit Over Implicit

**Handle warnings and errors thoughtfully**, distinguishing recoverable conditions from critical failures:

- Use specific exception types (not `Exception`)
- Let unknown exceptions propagate
- Document expected exceptions in docstrings
- Use custom exceptions for domain-specific errors

### Error Classes: Exceptions vs Error Metadata

TNH Scholar uses two distinct patterns for error handling:

**1. Exception Classes** - For errors that interrupt control flow:

```python
# ✅ Exception classes inherit from TnhScholarError
from tnh_scholar.exceptions import TnhScholarError

class ValidationError(TnhScholarError):
    """Raised when input validation fails."""
    pass

class ConfigurationError(TnhScholarError):
    """Raised when configuration is invalid."""
    pass
```

**2. Error Metadata Classes** - For structured error information returned as data:

```python
# ✅ Error metadata classes use Pydantic BaseModel
from pydantic import BaseModel, ConfigDict

class ErrorInfo(BaseModel):
    """Error information returned from validation or processing.

    Not raised as exception - returned as structured data for
    programmatic handling, serialization, and reporting.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    error_type: str
    message: str
    context: dict[str, Any] | None = None

# ✅ Example: Validation returns error metadata
def validate_sections(sections: List[Section]) -> List[SectionValidationError]:
    """Returns list of errors found (does not raise exception)."""
    errors = []
    # ... validation logic that appends SectionValidationError instances
    return errors
```

**When to use each pattern:**

| Pattern | Use Case | Example |
|---------|----------|---------|
| **Exception class** (inherits `TnhScholarError`) | Fatal errors requiring immediate control flow change | `raise ConfigurationError("Missing API key")` |
| **Error metadata class** (Pydantic `BaseModel`) | Validation results, batch error reporting, API responses | `return [ErrorInfo(type="gap", message="...")]` |

**Key requirements for error metadata classes:**

```python
from pydantic import BaseModel, ConfigDict

class MyErrorInfo(BaseModel):
    """Always include these for error metadata classes."""
    model_config = ConfigDict(
        frozen=True,      # Immutability
        extra="forbid"    # Reject unexpected fields
    )

    # Strongly typed fields (no raw dicts/strings)
    error_type: str
    message: str
```

**Benefits:**

- **Serialization**: Pydantic models serialize to JSON for APIs and logging
- **Validation**: Type checking and field validation at construction
- **Immutability**: `frozen=True` prevents accidental mutation
- **Strict schema**: `extra="forbid"` catches schema mismatches

**Examples in the codebase:**

- Exception classes: [src/tnh_scholar/exceptions.py](../../src/tnh_scholar/exceptions.py)
- Error metadata: [src/tnh_scholar/gen_ai_service/models/transport.py](../../src/tnh_scholar/gen_ai_service/models/transport.py) (`ErrorInfo`)
- Error metadata: [src/tnh_scholar/text_processing/numbered_text.py](../../src/tnh_scholar/text_processing/numbered_text.py) (`SectionValidationError`)

### Fail Fast

During prototyping, **fail fast** to identify issues early:

- Don't mask exceptions with catch-all handlers
- Let stack traces propagate for debugging
- Add TODO comments for future error handling

See [Style Guide: Error Handling](/development/style-guide.md) for implementation details.

## Processing Architecture

### Pipeline Design

**Pipelines compose processors into workflows:**

- Each processor has a single, well-defined transformation
- Processors are independent and reusable
- Pipeline orchestration is separate from processing logic
- Results flow through immutable data structures

**Example:**

```python
class ProcessingPipeline:
    """Orchestrates content processing workflow."""

    def __init__(
        self,
        processors: list[ContentProcessor],
        training_collector: Optional[TrainingCollector] = None
    ):
        self.processors = processors
        self.collector = training_collector

    def execute(
        self,
        source: ContentSource
    ) -> tuple[ProcessedContent, Optional[TrainingData]]:
        """Execute pipeline with optional training data collection."""
        content = source.load()

        for processor in self.processors:
            content = processor.process(content)

            if self.collector:
                self.collector.collect(processor, content)

        training_data = self.collector.finalize() if self.collector else None
        return content, training_data
```

### Dispatch Patterns

**Employ dispatch patterns** (prefer `match`/`case` when possible) to cleanly separate concerns and improve extensibility:

```python
# ✅ Preferred: Pattern matching for dispatch
def route_processing(task: ProcessingTask) -> ProcessedContent:
    match task.type:
        case TaskType.PUNCTUATE:
            return punctuate_processor.process(task.content)
        case TaskType.TRANSLATE:
            return translation_processor.process(task.content)
        case TaskType.SECTION:
            return sectioning_processor.process(task.content)
        case _:
            raise ValueError(f"Unknown task type: {task.type}")
```

## Text Processing Principles

### Explicit Text Handling

**Text handling should be explicit and consistent**, favoring clarity in encoding and processing:

- Always specify encoding (UTF-8 default)
- Handle normalization explicitly (NFC, NFKC, etc.)
- Document text format assumptions
- Preserve provenance and metadata

### Metadata Preservation

Throughout processing pipelines:

- Maintain document structure
- Preserve metadata across transformations
- Track provenance and processing history
- Support metadata enrichment

## Testing Architecture

### Test Organization

Tests follow this structure even during prototyping:

```plaintext
tests/
├── unit/              # Fast, isolated tests
│   ├── test_text_processing.py
│   └── test_prompt_catalog.py
├── integration/       # Multi-component tests
│   └── test_full_pipeline.py
└── conftest.py        # Shared fixtures
```

### Test Requirements by Phase

**Prototyping Phase:**

- Basic unit tests for core functionality
- Critical path testing
- Basic integration tests

**Production Phase:**

- Comprehensive unit test coverage (>80%)
- Full integration test suite
- Performance testing
- Edge case handling
- Mock external services

## Performance Principles

### Resource Management

Basic guidelines apply across phases:

**Memory Management:**

- Stream large files (don't load entirely into memory)
- Clean up temporary files
- Monitor memory usage in processing pipelines

**Processing Optimization:**

- Batch operations where possible
- Cache frequently used data (prompts, configurations)
- Monitor API usage and costs
- Use async/await for I/O-bound operations

### Lazy Evaluation

Defer expensive computations until needed:

```python
# ✅ Preferred: Lazy evaluation
class PromptCatalog:
    def __init__(self, directory: Path):
        self.directory = directory
        self._cache: Dict[str, Prompt] = {}

    def get_prompt(self, name: str) -> Prompt:
        """Load prompt on demand."""
        if name not in self._cache:
            self._cache[name] = self._load_prompt(name)
        return self._cache[name]

# 🚫 Avoid: Eager loading of everything
class PromptCatalog:
    def __init__(self, directory: Path):
        self.prompts = {
            p.name: p for p in self._load_all_prompts(directory)
        }  # Loads hundreds of prompts at startup
```

## Refactoring Triggers

**Refactor when:**

- Code becomes difficult to follow
- Duplication arises (DRY principle)
- New requirements suggest clearer abstractions
- Function/module exceeds complexity limits
- Tests become difficult to write or maintain

## Development Phase Considerations

### Prototyping Phase Priorities

During prototyping, prioritize:

- Rapid iteration and experimentation
- Core functionality over comprehensive error handling
- Simple pipeline construction
- Clear component boundaries
- Basic testing and documentation

### Production Phase Requirements

For production, add:

- Comprehensive error handling
- Performance optimization
- Security hardening
- Full test coverage
- Complete documentation
- Monitoring and observability

## Future Architecture Considerations

Areas marked for future development:

- Plugin system architecture
- Enhanced configuration management
- Rebuild of `ai_text_processing` suite with modern patterns
- Extended API integration (batch processing, alternate model services)
- Enhanced security features
- Performance optimization and async processing
- Extended prompt capabilities
- Model training and fine-tuning tools

See [Future Directions](/project/future-directions.md) for long-term vision.

## Related Documentation

- [Style Guide](/development/style-guide.md) - Code formatting and naming conventions
- [Object-Service Design Blueprint](/architecture/object-service/object-service-design-overview.md) - Detailed architecture patterns
- [System Design](/development/system-design.md) - High-level system architecture
- [Project Principles](/project/principles.md) - High-level project principles
- [Conceptual Architecture](/project/conceptual-architecture.md) - Conceptual system model
- [Contributing Guide](/development/contributing-prototype-phase.md) - Contribution workflow

## Historical References

<details>
<summary>📚 View superseded design documents (maintainers/contributors)</summary>

**Note**: These documents are archived and excluded from the published documentation. They provide historical context for the prompt system architecture and terminology migration.

- **[ADR-PT01: Pattern Access Strategy](/architecture/prompt-system/archive/adr/adr-pt01-pattern-access-strategy.md)** (2024)
  *Status*: Superseded by prompt system ADR series (ADR-PT03/ADR-PT04)
- **[Core Pattern Architecture](/architecture/prompt-system/archive/core-pattern-architecture.md)** (2024)
  *Status*: Historical prompt/pattern architecture exploration

</details>

## References

- Core Pattern Architecture (see Historical References) - Legacy prompt/pattern design notes
- [Object-Service Design Blueprint](/architecture/object-service/object-service-design-overview.md) - Layer architecture and design patterns
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) - Robert C. Martin
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html) - Eric Evans via Martin Fowler
