---
title: "TNH Scholar Design Guide"
description: "## Overview"
owner: ""
status: processing
created: "2025-02-01"
---
# TNH Scholar Design Guide

## Overview

This design guide establishes development standards for the TNH Scholar project. While the project is currently in a rapid prototyping phase, these guidelines aim to maintain code quality and consistency throughout development. The guide distinguishes between immediate prototyping requirements and standards for later production phases where appropriate.

## Code Style and Organization

### General Coding Principles

Code should adhere to the principle of single responsibility, with functions and classes focused on one clear task. Helpers should be small (target 10 lines) and composable, enabling reuse and clarity. Method names must be descriptive and scoped appropriately, reflecting their purpose without ambiguity. Use classes when managing related state or behavior, keeping them cohesive and avoiding unnecessary complexity. Employ dispatch patterns (prefer match/case when possible) to cleanly separate concerns and improve extensibility. Validation logic should be distinct from mutation or side effects to ensure maintainability. Handle warnings and errors thoughtfully, distinguishing recoverable conditions from critical failures. Text handling should be explicit and consistent, favoring clarity in encoding and processing. Prioritize naming and readability to make code self-explanatory and accessible. Logging should be purposeful, balancing informational messages with error reporting. Refactor when code becomes difficult to follow, when duplication arises, or when new requirements suggest clearer abstractions.

### Modularity

- **Design for modularity:** Each module, class, and function should have a single, well-defined responsibility.
- **Encapsulate related functionality:** Group related functions and classes into modules and packages to promote reuse and clarity.
- **Minimize coupling:** Modules should interact through well-defined interfaces, minimizing dependencies and side effects.
- **Favor composition over inheritance:** Use composition to build complex behavior from simple, reusable components.
- **Limit module size:** Aim for modules that are small enough to be easily understood (generally < 300 lines), but large enough to encapsulate a coherent set of functionality.
- **Explicit module exports:** Use `__all__` to define public API of modules where appropriate.

### Python Standards

The project follows PEP 8 with some specific adaptations. All Python code should adhere to these standards regardless of development phase:

The project uses Python 3.12.4 exclusively, taking advantage of modern Python features including strict typing. This version requirement ensures consistency across all components and enables use of the latest language features.

#### Import Conventions

Import organization follows this pattern:

1. Standard library imports
2. External package imports
3. Internal package imports
4. Relative imports

For example:

```python
from pathlib import Path
from typing import Optional, Dict

import click
from pydantic import BaseModel

from tnh_scholar.utils import ensure_directory_exists
from .environment import check_env
```

Use absolute imports from the top-level package (tnh_scholar.) for all intra-project references.

Rationale: Maintains explicit architectural boundaries, avoids ambiguity in layered modules, and ensures IDE/refactor tooling compatibility.

Example:

```python
# ✅ Preferred
from tnh_scholar.gen_ai_service.models.domain import Message

# 🚫 Avoid
from ..models.domain import Message
```

Exception:

Relative imports may be used only for very local module groups (e.g., sibling adapters or mappers within the same provider directory) when the reference is clearly confined to that module cluster and no cross-layer boundary is crossed.

### Strong Typing and Abstraction Preferences

- Always use typed classes, enums, and dataclasses; avoid literal strings and numbers in app logic.  
- Configuration values come from `Settings` (pydantic BaseSettings), policies, or pattern metadata — never hardcoded.  
- Dicts are not used in app layers; prefer Pydantic models or dataclasses for structured data.  
- Enums replace string literals for identifiers (e.g., provider names, roles, intent types).  
- Adapters may handle dict conversions only at API transport boundaries.  
- Abstract base classes (`Protocol` or ABC) define all system interfaces; adapters implement them.  
  - Use Protocol for structural typing and interface contracts (no inheritance required).
  - Use ABC only when enforcing init-time invariants or providing shared mixin behavior that all implementers should inherit.
- Settings and policy modules hold all runtime defaults; code must read from them instead of embedding constants.  
- Favor immutability and declarative structure — objects represent data, services perform work.  
- Typed objects are preferred even during prototyping for consistency and clarity.  
- The goal: zero literals, zero dicts, clear typing, explicit configuration — ensuring predictable behavior and strong IDE/type support.

### File and Directory Naming

File naming conventions apply across all project phases:

All Python files use lowercase with underscores, for example: `audio_processing.py`.

Directory names follow the same lowercase with underscores pattern: `text_processing/`.

Exception cases follow traditional conventions:

- README.md
- LICENSE
- CONTRIBUTING.md
- Requirements files (requirements.txt, dev-requirements.txt)

### Module Structure

Each module should maintain this general structure:

```python
"""Module docstring providing overview and purpose."""

# Standard imports
# External imports
# Internal imports

# Module-level constants
DEFAULT_CHUNK_SIZE = 1024

# Classes
class ExampleClass:
    """Class docstring."""
    
# Functions
def example_function():
    """Function docstring."""
```

### Function and Method Complexity

- **Limit function/method length:** Target functions and methods to be no longer than 15-20 lines of code (excluding docstring). If a function grows beyond this, consider refactoring into smaller helpers.
- **Limit cyclomatic complexity:** Functions should have a cyclomatic complexity of 7 or less. Use tools like `radon` or `flake8-cognitive-complexity` to monitor.
- **Single responsibility:** Each function or method should perform one logical task. Avoid mixing concerns (e.g., validation, mutation, and I/O in a single function).
- **Early returns:** Use early returns to reduce nesting and improve readability.
- **Descriptive naming:** Function and method names should clearly describe their purpose and side effects.
- **Use `match` / `case` statements for multi-condition branching:**  
  When branching logic involves three or more conditions, prefer `match` / `case` over chained `if` / `elif` blocks for readability and maintainability.  
  This is especially required when branching on a single variable (e.g., a mode, type, or enum value).  
  Match-case may also be used for more complex branching scenarios where patterns can simplify logic or make case distinctions explicit.
- **Document edge cases:** Clearly document any non-obvious logic or edge cases in the function docstring.

## Type Handling

### Best Practices for Data Models

## Classes vs. Dictionaries

- **Always prefer structured classes over plain dictionaries** for data that has consistent fields
- **Use `.` attribute access instead of `['key']` dictionary lookups** for better readability and IDE support
- **Leverage type hints** to catch errors at development time rather than runtime
- **Encapsulate related logic** within the class that owns the data

## Pydantic vs. Dataclasses

- **Use Pydantic V2 when data validation is important** (especially for external inputs)
- **Choose dataclasses for simple internal data structures** with minimal validation needs
- **Prefer Pydantic for API interfaces** where data needs parsing and validation
- **Use dataclasses when serialization features aren't needed** or for improved performance

## Pydantic Best Practices

- **Use `@computed_field` for derived properties** that should be included in serialization
- **Leverage field validation** with standard validators or custom methods
- **Use `model_config` for class-level configuration** like allowing extra fields
- **Take advantage of automatic type coercion** for cleaner interfaces
- **Create factory methods** (like `from_dict`, `from_legacy_format`) for special parsing needs

## General Design Guidelines

- **Keep data models immutable** when possible for safer concurrent code
- **Make validation errors descriptive** to simplify debugging
- **Separate data representation from business logic** where appropriate
- **Design for extensibility** by using inheritance or composition
- **Document expected formats** in docstrings, especially for complex structures

### Type Annotations

The project emphasizes strong typing throughout:

Basic type annotations are required even during prototyping:

```python
def process_text(
    text: str,
    language: Optional[str] = None,
    max_tokens: int = 0
) -> str:
```

Custom types should be defined for complex structures:

```python
from typing import NewType

MarkdownStr = NewType('MarkdownStr', str)
```

### Pydantic Models

Data models use Pydantic for validation:

```python
class TextObject(BaseModel):
    """Represents processed text with metadata."""
    language: str = Field(..., description="ISO 639-1 language code")
    sections: List[LogicalSection]
    metadata: Optional[Dict[str, Any]] = None
```

## Error Handling

Error handling requirements differ between prototyping and production phases:

### Errors - Prototyping Phase

During prototyping, error handling should prioritize visibility of failure cases over comprehensive handling. This approach helps identify and document necessary error cases early in development.

Preferred approach - allow exceptions to propagate:

```python
# TODO: Add error handling for ValueError and PatternError
result = process_text(input_text)
```

When try blocks are needed, use minimal handling to maintain visibility:

```python
try:
    # TODO: Handle specific exceptions in production
    result = process_text(input_text)
except:
    # Maintain stack trace while documenting intent
    raise
```

This approach:

- Maintains clear visibility of failure modes
- Documents intended error handling through TODO comments
- Preserves full stack traces for debugging
- Avoids masking exceptions during development

### Errors - Production Phase

Production code requires comprehensive error handling:

```python
try:
    result = process_text(input_text)
except ValueError as e:
    logger.error(f"Invalid input format: {e}")
    raise InvalidInputError(str(e)) from e
except APIError as e:
    logger.error(f"API processing failed: {e}")
    raise ProcessingError(str(e)) from e
```

Do **NOT** write catch-all exception handling such as in:

```python
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise SystemError(f"unexpected error: {e}") from e
```

It is preferred to let unknown exceptions propagate.

## Logging

### Logging - Prototyping Phase

Basic logging configuration is acceptable during prototyping:

```python
logger = get_logger(__name__)
logger.info("Processing started")
logger.error("Processing failed")
```

Especially important is DEBUG level logging.

### Logging - Production Phase

Production logging should include:

- Log levels properly used
- Structured logging where appropriate
- Contextual information
- Error tracebacks
- Provenance and fingerprinting if required

## Testing

### Test Organization

Tests follow this structure even during prototyping:

```plaintext
tests/
├── unit/
│   ├── test_text_processing.py
│   └── test_audio_processing.py
├── integration/
│   └── test_full_pipeline.py
└── conftest.py
```

### Test Requirements

Prototyping Phase:

- Basic unit tests for core functionality
- Critical path testing
- Basic integration tests

Production Phase:

- Comprehensive unit test coverage
- Full integration test suite
- Performance testing
- Edge case handling
- Mock external services

## Documentation

### Code Documentation

The project follows Google's Python documentation style for all docstrings. This style provides clear structure while maintaining readability.

Classes:

```python
class TextProcessor:
    """A class that processes text using configurable patterns.

    Implements pattern-based text processing with configurable token limits
    and language support. Designed for extensibility through the pattern system.

    Attributes:
        pattern: A Pattern instance defining processing instructions.
        max_tokens: An integer specifying maximum tokens for processing.

    Note:
        Pattern instances should be initialized with proper template validation.
    """
```

Functions:

```python
def process_text(text: str, language: Optional[str] = None) -> str:
    """Processes text according to pattern instructions.

    Applies the configured pattern to input text, handling language-specific
    requirements and token limitations.

    Args:
        text: Input text to process.
        language: Optional ISO 639-1 language code. Defaults to None for
            auto-detection.

    Returns:
        A string containing the processed text.

    Raises:
        ValueError: If text is empty or invalid.
        PatternError: If pattern application fails.

    Examples:
        >>> processor = TextProcessor(pattern)
        >>> result = process_text("Input text", language="en")
        >>> print(result)
        Processed text output
    """
```

### API Documentation

API documentation requirements increase with development phase:

Prototyping Phase:

- Basic function/class documentation
- Essential usage examples
- Known limitations noted

Production Phase:

- Comprehensive API documentation
- Multiple usage examples
- Error handling documentation
- Performance considerations
- Security implications

## Development Workflow

### Version Control

Git workflow standards apply across all phases:

- Feature branches for development
- Clear commit messages
- Regular main branch updates
- Version tags for releases

### Tooling

- **Code formatting:** Use `black` for automatic code formatting.
- **Linting:** Use `ruff` to enforce style and complexity limits.
- **Type checking:** Use `mypy` to enforce type annotations.
- **Complexity analysis:** Use Sourcery monitor function complexity.
- **Pre-commit hooks:** Configure pre-commit hooks to automate code quality checks.
- **Optional:** For stricter cyclomatic complexity enforcement, consider `radon` or `flake8-cognitive-complexity`.

### Code Review

Review requirements increase with development phase:

Prototyping Phase:

- Basic functionality review
- Core design review
- Critical security review
- Basic Sourcery review

Production Phase:

- Comprehensive code review
- Performance review
- Security audit
- Documentation review
- Test coverage review
- All files should pass Sourcery review with no un-resolved issues. All functions should have a quality score of 60% or better. Any functions with a lower score must be clearly documented with rationale (legacy code, necessary complexity for algorithmic or performance reasons)

## Security Considerations

### API Key Management

Consistent across all phases:

- No keys in code
- Environment variable usage
- Secure configuration loading
- Key rotation support

### Input Validation

Validation requirements increase with phase:

Prototyping Phase:

- Basic input validation
- Type checking
- Simple sanitization

Production Phase:

- Comprehensive validation
- Security scanning
- Input sanitization
- Output escaping

## Performance Guidelines

### Resource Management

Basic guidelines apply across phases:

Memory Management:

- Stream large files
- Clean up temporary files
- Monitor memory usage

Processing Optimization:

- Batch operations where possible
- Cache frequently used data
- Monitor API usage

## Future Considerations

Areas marked for future development:

- Plugin system architecture
- Configuration handling
- Rebuild of ai_text_processing suite
- Extended API integration
  - Batch processing
  - Alternate API model services
- Enhanced security features
- Performance optimization
- Extended pattern capabilities
- Additional CLI processing tools
- Model training tools
- Natural language processing tools