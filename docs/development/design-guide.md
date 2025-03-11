# TNH Scholar Design Guide

## Overview

This design guide establishes development standards for the TNH Scholar project. While the project is currently in a rapid prototyping phase, these guidelines aim to maintain code quality and consistency throughout development. The guide distinguishes between immediate prototyping requirements and standards for later production phases where appropriate.

## Code Style and Organization

### Python Standards

The project follows PEP 8 with some specific adaptations. All Python code should adhere to these standards regardless of development phase:

The project uses Python 3.12.4 exclusively, taking advantage of modern Python features including strict typing. This version requirement ensures consistency across all components and enables use of the latest language features.

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

## Type Handling

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

### Prototyping Phase

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

Do **NOT** write catch-all exception handling such as in:

```python
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise SystemError(f"unexpected error: {e}") from e
```

It is preferred to let unknown exceptions propagate.

## Logging

### Prototyping Phase

Basic logging configuration is acceptable during prototyping:

```python
logger = get_child_logger(__name__)
logger.info("Processing started")
logger.error("Processing failed")
```

Especially important is DEBUG level logging.

### Production Phase

Production logging should include:

- Log levels properly used
- Structured logging where appropriate
- Contextual information
- Error tracebacks

## Testing

### Test Organization

Tests follow this structure even during prototyping:

```
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

### Code Review

Review requirements increase with development phase:

Prototyping Phase:

- Basic functionality review
- Core design review
- Critical security review

Production Phase:

- Comprehensive code review
- Performance review
- Security audit
- Documentation review
- Test coverage review

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
