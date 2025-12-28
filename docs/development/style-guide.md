---
title: "TNH Scholar Style Guide"
description: "Code formatting, naming conventions, and Python standards for TNH Scholar development."
owner: ""
author: ""
status: current
created: "2025-11-29"
---
# TNH Scholar Style Guide

Code formatting, naming conventions, and Python standards for TNH Scholar development.

## Overview

This style guide establishes coding standards for the TNH Scholar project. These guidelines ensure code quality, consistency, and maintainability across all development phases. For architectural design principles, see [Design Principles](/development/design-principles.md).

## Python Standards

### Version Requirement

The project uses **Python 3.12.4 exclusively**, taking advantage of modern Python features including strict typing, pattern matching, and improved error messages. This version requirement ensures consistency across all components and enables use of the latest language features.

### PEP 8 Compliance

All Python code follows PEP 8 with project-specific adaptations detailed below.

## Code Organization

### Import Conventions

Import organization follows this pattern:

1. Standard library imports
2. External package imports
3. Internal package imports
4. Relative imports (use sparingly)

**Example:**

```python
from pathlib import Path
from typing import Optional, Dict

import click
from pydantic import BaseModel

from tnh_scholar.utils import ensure_directory_exists
from .environment import check_env
```

### Absolute vs Relative Imports

**Preferred**: Use **absolute imports** from the top-level package (`tnh_scholar.`) for all intra-project references.

**Rationale**: Maintains explicit architectural boundaries, avoids ambiguity in layered modules, and ensures IDE/refactor tooling compatibility.

**Example:**

```python
# ✅ Preferred
from tnh_scholar.gen_ai_service.models.domain import Message

# 🚫 Avoid
from ..models.domain import Message
```

**Exception**: Relative imports may be used only for very local module groups (e.g., sibling adapters or mappers within the same provider directory) when the reference is clearly confined to that module cluster and no cross-layer boundary is crossed.

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

## Naming Conventions

### File and Directory Naming

**Python files**: Use lowercase with underscores

```
audio_processing.py
text_processor.py
```

**Directory names**: Use lowercase with underscores

```
text_processing/
gen_ai_service/
```

**Exception cases** (traditional conventions):

- `README.md`
- `LICENSE`
- `CONTRIBUTING.md`
- Requirements files (`requirements.txt`, `dev-requirements.txt`)

### Function and Method Names

- Use lowercase with underscores: `process_text()`, `get_pattern()`
- Names must be **descriptive** and scoped appropriately, reflecting their purpose without ambiguity
- Document side effects in name if not obvious: `update_and_save()`, `fetch_and_cache()`

### Class Names

- Use PascalCase: `TextProcessor`, `PromptCatalog`
- Keep cohesive and avoid unnecessary complexity

### Variable Names

- Use lowercase with underscores: `text_content`, `max_tokens`
- Make names self-explanatory and accessible
- Avoid single-letter names except for loop counters in short scopes

## Type Annotations

### Required Type Hints

Type annotations are **required** for all function signatures, even during prototyping:

```python
def process_text(
    text: str,
    language: Optional[str] = None,
    max_tokens: int = 0
) -> str:
    """Process text with optional language specification."""
```

### Custom Types

Define custom types for complex structures:

```python
from typing import NewType

MarkdownStr = NewType('MarkdownStr', str)
LanguageCode = NewType('LanguageCode', str)
```

### Type Handling Best Practices

**Always prefer structured classes over plain dictionaries** for data with consistent fields:

- Use `.` attribute access instead of `['key']` dictionary lookups
- Leverage type hints to catch errors at development time
- Encapsulate related logic within the class that owns the data

## Data Models

### Pydantic vs Dataclasses

**Use Pydantic V2** when:

- Data validation is important (especially for external inputs)
- Working with API interfaces where data needs parsing and validation
- Serialization features are needed

**Use dataclasses** when:

- Creating simple internal data structures with minimal validation needs
- Serialization features aren't needed
- Improved performance is required

### Pydantic Best Practices

```python
from pydantic import BaseModel, Field, computed_field

class TextObject(BaseModel):
    """Represents processed text with metadata."""

    language: str = Field(..., description="ISO 639-1 language code")
    sections: List[LogicalSection]
    metadata: Optional[Dict[str, Any]] = None

    @computed_field
    @property
    def word_count(self) -> int:
        """Compute total word count across all sections."""
        return sum(len(s.content.split()) for s in self.sections)
```

**Best practices:**

- Use `@computed_field` for derived properties included in serialization
- Leverage field validation with standard validators or custom methods
- Use `model_config` for class-level configuration
- Take advantage of automatic type coercion for cleaner interfaces
- Create factory methods (`from_dict`, `from_legacy_format`) for special parsing needs

## Strong Typing Standards

**Critical project requirements:**

- Always use typed classes, enums, and dataclasses
- **Avoid literal strings and numbers in app logic**
- Configuration values come from `Settings` (pydantic BaseSettings), policies, or prompt metadata — **never hardcoded**
- **Dicts are not used in app layers**; prefer Pydantic models or dataclasses
- Enums replace string literals for identifiers (e.g., provider names, roles, intent types)
- Adapters may handle dict conversions only at API transport boundaries

**Abstract interfaces:**

- Use `Protocol` for structural typing and interface contracts (no inheritance required)
- Use `ABC` only when enforcing init-time invariants or providing shared mixin behavior
- All system interfaces must be defined via abstract base classes

**Goal**: Zero literals, zero dicts, clear typing, explicit configuration — ensuring predictable behavior and strong IDE/type support.

### Replacing Literal Values

**Avoid module-level constants at the top of files.** Instead, use these patterns:

**For display labels/messages** → `@dataclass(frozen=True)`:

```python
@dataclass(frozen=True)
class HumanOutputLabels:
    """Display labels for human-friendly CLI output."""
    no_variables: str = "(none)"
    no_default_model: str = "(no default)"

LABELS = HumanOutputLabels()
# Usage: LABELS.no_variables
```

**For identifiers/categories** → `str` Enum:

```python
class OutputColor(str, Enum):
    """ANSI color codes for terminal output."""
    TITLE = "bright_blue"
    ERROR = "red"

# Usage: OutputColor.TITLE
```

**For numeric thresholds** → `@dataclass(frozen=True)`:

```python
@dataclass(frozen=True)
class ValidationLimits:
    """Validation thresholds for CLI inputs."""
    max_prompt_key_length: int = 64
    max_temperature: float = 2.0

LIMITS = ValidationLimits()
# Usage: LIMITS.max_temperature
```

**Benefits**: Type-safe, discoverable with IDE autocomplete, grouped by semantic purpose, testable, avoids top-of-file constant clutter.

## Function and Method Complexity

### Size Limits

- **Target length**: 15-20 lines of code (excluding docstring)
- **Cyclomatic complexity**: Target 7 or less (enforced at 9 by Ruff)
  - McCabe complexity counts decision points (if/elif/match), which can flag low-complexity patterns like simple match statements with many cases
  - Use Sourcery for cognitive complexity analysis (better semantic understanding)
  - Ruff threshold set at 9 to avoid false positives on type-safe mappings
- If a function grows beyond limits, refactor into smaller helpers

### Single Responsibility

Each function or method should perform **one logical task**. Avoid mixing concerns (e.g., validation, mutation, and I/O in a single function).

### Control Flow

**Use early returns** to reduce nesting:

```python
# ✅ Preferred
def process_text(text: str) -> str:
    if not text:
        return ""

    if len(text) > MAX_LENGTH:
        raise ValueError("Text too long")

    return text.upper()

# 🚫 Avoid deep nesting
def process_text(text: str) -> str:
    if text:
        if len(text) <= MAX_LENGTH:
            return text.upper()
        else:
            raise ValueError("Text too long")
    else:
        return ""
```

**Use `match`/`case` for multi-condition branching** (3+ conditions):

```python
# ✅ Preferred for 3+ conditions
match processing_mode:
    case "punctuate":
        return punctuate_text(text)
    case "translate":
        return translate_text(text, target_lang)
    case "section":
        return section_text(text)
    case _:
        raise ValueError(f"Unknown mode: {processing_mode}")

# 🚫 Avoid long if/elif chains
if processing_mode == "punctuate":
    return punctuate_text(text)
elif processing_mode == "translate":
    return translate_text(text, target_lang)
# ... many more elifs
```

## Code Documentation

### Docstring Style

The project follows **Google's Python documentation style** for all docstrings.

**Classes:**

```python
class TextProcessor:
    """A class that processes text using configurable prompts.

    Implements prompt-based text processing with configurable token limits
    and language support. Designed for extensibility through the prompt system.

    Attributes:
        prompt: A Prompt instance defining processing instructions.
        max_tokens: An integer specifying maximum tokens for processing.

    Note:
        Prompt instances should be initialized with proper template validation.
    """
```

**Functions:**

```python
def process_text(text: str, language: Optional[str] = None) -> str:
    """Processes text according to prompt instructions.

    Applies the configured prompt to input text, handling language-specific
    requirements and token limitations.

    Args:
        text: Input text to process.
        language: Optional ISO 639-1 language code. Defaults to None for
            auto-detection.

    Returns:
        A string containing the processed text.

    Raises:
        ValueError: If text is empty or invalid.
        PromptError: If prompt application fails.

    Examples:
        >>> processor = TextProcessor(prompt)
        >>> result = process_text("Input text", language="en")
        >>> print(result)
        Processed text output
    """
```

### Documentation Requirements by Phase

**Prototyping Phase:**

- Basic function/class documentation
- Essential usage examples
- Known limitations noted

**Production Phase:**

- Comprehensive API documentation
- Multiple usage examples
- Error handling documentation
- Performance considerations
- Security implications

## Error Handling

### Prototyping Phase

During prototyping, error handling should prioritize **visibility of failure cases** over comprehensive handling.

**Preferred approach** — allow exceptions to propagate:

```python
# TODO: Add error handling for ValueError and PromptError
result = process_text(input_text)
```

When try blocks are needed, use minimal handling:

```python
try:
    # TODO: Handle specific exceptions in production
    result = process_text(input_text)
except:
    # Maintain stack trace while documenting intent
    raise
```

This approach maintains clear visibility of failure modes and preserves full stack traces for debugging.

### Production Phase

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

**Do NOT write catch-all exception handling:**

```python
# 🚫 Avoid
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise SystemError(f"unexpected error: {e}") from e
```

**Prefer** letting unknown exceptions propagate.

## Logging

### Prototyping Phase

Basic logging configuration is acceptable:

```python
logger = get_logger(__name__)
logger.info("Processing started")
logger.debug("Processing details: %s", details)  # DEBUG level especially important
logger.error("Processing failed")
```

### Production Phase

Production logging should include:

- Log levels properly used (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Structured logging where appropriate
- Contextual information
- Error tracebacks
- Provenance and fingerprinting if required

## Development Tooling

### Required Tools

- **Code formatting**: `black` for automatic code formatting
- **Linting**: `ruff` to enforce style and complexity limits
- **Type checking**: `mypy` to enforce type annotations
- **Complexity analysis**: Sourcery to monitor function complexity

### Optional Tools

- `radon` or `flake8-cognitive-complexity` for stricter cyclomatic complexity enforcement

### Sourcery Standards

**Prototyping Phase:**

- Basic Sourcery review

**Production Phase:**

- All files must pass Sourcery review with no unresolved issues
- All functions should have a quality score of 60% or better
- Functions with lower scores must be clearly documented with rationale (legacy code, necessary complexity for algorithmic or performance reasons)

## Security Standards

### API Key Management

Consistent across **all phases**:

- **No keys in code** (ever)
- Use environment variables
- Secure configuration loading
- Support key rotation

### Input Validation

**Prototyping Phase:**

- Basic input validation
- Type checking
- Simple sanitization

**Production Phase:**

- Comprehensive validation
- Security scanning
- Input sanitization
- Output escaping

## Version Control

### Git Workflow

Standards apply across all phases:

- Feature branches for development
- Clear, descriptive commit messages
- Regular main branch updates
- Version tags for releases

### Commit Message Format

```
Brief summary (50 chars or less)

Detailed explanation if needed (wrap at 72 chars):
- What changed
- Why it changed
- References to issues/ADRs

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Related Documentation

- [Design Principles](/development/design-principles.md) - Architectural patterns and design philosophy
- [Contributing Guide](/development/contributing-prototype-phase.md) - Contribution workflow and standards
- [Project Principles](/project/principles.md) - High-level project principles
- [System Design](/development/system-design.md) - Overall system architecture

## References

- [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/)
