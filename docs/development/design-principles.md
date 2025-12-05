---
title: "TNH Scholar Design Principles"
description: "Architectural patterns, design philosophy, and system organization principles for TNH Scholar development."
owner: ""
author: ""
status: processing
created: "2025-11-29"
---
# TNH Scholar Design Principles

Architectural patterns, design philosophy, and system organization principles for TNH Scholar development.

## Overview

This document establishes design principles for the TNH Scholar project. While the project is currently in a rapid prototyping phase, these guidelines aim to maintain architectural quality and consistency throughout development. The guide distinguishes between immediate prototyping requirements and standards for later production phases where appropriate.

For code formatting and naming conventions, see [Style Guide](style-guide.md). For high-level project philosophy and vision, see [Project Principles](/project/principles.md) and [Conceptual Architecture](/project/conceptual-architecture.md).

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

**Note**: During prototyping, singleton access (like `LocalPromptManager`) is acceptable for rapid development. Plan transition to dependency injection for production (see [ADR-PT01](/architecture/prompt-system/archive/adr/adr-pt01-pattern-access-strategy.md)).

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

See [Style Guide: Strong Typing Standards](style-guide.md#strong-typing-standards) for details.

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

### Fail Fast

During prototyping, **fail fast** to identify issues early:

- Don't mask exceptions with catch-all handlers
- Let stack traces propagate for debugging
- Add TODO comments for future error handling

See [Style Guide: Error Handling](style-guide.md#error-handling) for implementation details.

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

- [Style Guide](style-guide.md) - Code formatting and naming conventions
- [Object-Service Design Blueprint](/architecture/object-service/object-service-design-overview.md) - Detailed architecture patterns
- [System Design](system-design.md) - High-level system architecture
- [Project Principles](/project/principles.md) - High-level project principles
- [Conceptual Architecture](/project/conceptual-architecture.md) - Conceptual system model
- [Contributing Guide](contributing-prototype-phase.md) - Contribution workflow

## References

- [Core Pattern Architecture](/architecture/prompt-system/archive/core-pattern-architecture.md) - Legacy prompt/pattern design notes
- [Object-Service Design Blueprint](/architecture/object-service/object-service-design-overview.md) - Layer architecture and design patterns
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) - Robert C. Martin
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html) - Eric Evans via Martin Fowler
