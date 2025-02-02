# TNH Scholar Pattern System

The TNH Scholar Pattern System is inspired by and builds upon concepts from Daniel Miessler's 'fabric' project (<https://github.com/danielmiessler/fabric>). Like fabric, it uses template-based prompting for AI interactions, but adds version control and concurrent access management.

It is designed to interface with **tnh-fab** a multi-command text processing tool.

Additional tools which use patterns may be developed for the project.

The pattern system provides a version-controlled, concurrent-safe way to manage text processing templates. It is built around Jinja2 templates with Git-based versioning and file locking for safety.

## Core Components

### Pattern

A Pattern represents a single text processing template with:

- Instructions (as a Jinja2 template)
- Default template values
- Metadata in YAML frontmatter (optional) which may include default template values

Example pattern file:

```markdown
---
description: Example pattern
version: 1.0
language: English
---
Process this text in {{ language }} using {{ style_convention }} formatting.
```

In this example pattern the default `language` template variable is specified as English.
If not supplied through a template or other means, this default value will be used.
Setting default values when possible in the frontmatter is a good practice and allows patterns to run
with less specifications.

### Pattern Files

- Stored as .md files
- Include optional YAML frontmatter
- Use Jinja2 template syntax
- Support template variables

## Using Patterns

### Through TNH-FAB CLI

The most common way to use patterns is through the TNH-FAB command-line tool:

```bash
# Basic pattern processing
tnh-fab process -p pattern_name input.txt

# Process with sections
tnh-fab process -p format_xml -s sections.json input.txt

# Process by paragraphs
tnh-fab process -p format_xml -g input.txt

# Process with template values
tnh-fab process -p format_xml -t template.yaml input.txt
```

Each TNH-FAB command (punctuate, section, translate, process) uses specific patterns:

- punctuate: Uses punctuation patterns (default: 'default_punctuate')
- section: Uses section analysis patterns (default: 'default_section')
- translate: Uses translation patterns (default: 'default_line_translation')
- process: Requires explicit pattern specification

### Programmatic Usage

For developers building tools that use the pattern system:

```python
from tnh_scholar.ai_text_processing import Pattern, PatternManager

# Initialize pattern manager
pattern_manager = PatternManager(pattern_dir)

# Load a pattern
pattern = pattern_manager.load_pattern("my_pattern")

# Apply template values
result = pattern.apply_template({
    "language": "English",
    "style_convention": "APA"
})
```

## Pattern Location

By default, patterns are stored in the user's home directory under:

```bash
~/.config/tnh-scholar/patterns/
```

This location can be customized by setting the `TNH_PATTERN_DIR` environment variable:

```bash
# In .bashrc, .zshrc, or similar:
export TNH_PATTERN_DIR=/path/to/patterns
```

(or loaded through a `.env` file for development installations.)

The pattern system will:

1. First check for `TNH_PATTERN_DIR` environment variable
2. If not set, use the default ~/.config/tnh-scholar/patterns
3. Create the pattern directory if it doesn't exist

When using a pattern name with tnh-fab commands (e.g., `tnh-fab process -p my_pattern`), the system searches for a corresponding .md file (e.g., `my_pattern.md`) in the pattern directory and its subdirectories.

### Default Patterns

Through the setup utility, tnh-setup, the user has the option to download and install several default and example patterns.

Note that tnh-fab expects the following patterns to be in the patterns directory for default use:

- default_punctuate.md - Default punctuation pattern
- default_section.md - Default section analysis pattern
- default_line_translation.md - Default translation pattern

These provide basic functionality but can be customized or overridden by creating patterns with the same names in your pattern directory.

### Pattern Integration

The pattern system can be integrated into other tools and workflows:

- Custom text processing applications
- Web services
- Analysis pipelines
- Batch processing systems

### Template Variables

Templates support variables through Jinja2 syntax:

- Use `{{ variable }}` for simple substitution
- Values provided when applying template
- Default values can be specified in Pattern

## Pattern Storage and Management

### Pattern Manager

The PatternManager provides the main interface for:

- Loading patterns by name
- Saving new patterns
- Version control integration
- Concurrent access management

### Pattern Locations

Patterns are stored in a directory specified as either:

- `$HOME/.config/tnh-scholar/patterns` (default search location)

- A custom directory specified by TNH_PATTERN_DIR environment variable, which can also be configured in a .env file.

### Version Control

Patterns are automatically version controlled:

- Git-backed storage
- Automatic commits on changes
- History tracking
- Change validation

### Concurrent Access

The system provides safe concurrent access through:

- File-level locking
- Lock cleanup
- Stale lock detection
- Safe access patterns

## Creating Patterns

Patterns must have:

1. Unique name
2. Valid Jinja2 template content
3. Optional default template values

Example pattern creation:

```python
from tnh_scholar.ai_text_processing import Pattern

pattern = Pattern(
    name="example_pattern",
    instructions="Process {{ text }} using {{ style }}",
    default_template_fields={"style": "default"}
)
```

## Pattern File Format

A pattern file (`example.md`):

```markdown
---
description: Example processing pattern
version: 1.0
author: TNH Scholar
---
Please process this text according to these parameters:

Language: {{ language }}
Style: {{ style_convention }}
Review Count: {{ review_count }}

Apply standard formatting while maintaining original meaning.
```

## Error Handling

The system handles common errors:

- Missing patterns
- Invalid template syntax
- Concurrent access conflicts
- Version control issues

## Technical Details

### File Locking

- Uses system-level file locking
- Automatic lock cleanup
- Timeout handling
- Safe concurrent access

### Version Control

- Git-based backend
- Automatic commit messages
- Change tracking
- History preservation

### Pattern Validation

All patterns are validated for:

- Template syntax
- Required variables
- Unique naming
- Content format

## Limitations

Current implementation:

- Single repository per PatternManager
- File-based storage only
- Local Git repository
- Synchronous operations

## Best Practices

### 1. Pattern Naming

- Use descriptive names
- Include purpose in name
- Follow lowercase_with_underscores format

### 2. Template Content

- Document required variables
- Include usage examples
- Provide default values
- Use clear template syntax

### 3. Pattern Management

- Regular pattern updates
- Version control usage
- Proper error handling
- Pattern testing
