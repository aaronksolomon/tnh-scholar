---
title: "TNH Scholar Prompt System"
description: "This document describes the TNH Scholar Prompt System (formerly called patterns). The system allows for template-based prompting of AI interactions, with version control and concurrent access management."
owner: ""
author: ""
status: current
created: "2025-01-19"
---
# TNH Scholar Prompt System

This document describes the TNH Scholar Prompt System (formerly called patterns). The system allows for template-based prompting of AI interactions, with version control and concurrent access management.

It is designed to interface with **tnh-gen**, the unified CLI for prompt-driven text processing.

Additional tools which use prompts may be developed for the project.

The prompt system provides a version-controlled, concurrent-safe way to manage text processing templates. It is built around Jinja2 templates with Git-based versioning and file locking for safety.

## Core Components

### Prompt

A Prompt represents a single text processing template with:

- Instructions (as a Jinja2 template)
- Default template values
- Metadata in YAML frontmatter (optional) which may include default template values

Example prompt file:

```markdown
---
description: Example prompt
version: 1.0
language: English
---
Process this text in {{ language }} using {{ style_convention }} formatting.
```

In this example prompt the default `language` template variable is specified as English.
If not supplied through a template or other means, this default value will be used.
Setting default values when possible in the frontmatter is a good practice and allows prompts to run
with less specifications.

### Prompt Files

- Stored as .md files
- Include optional YAML frontmatter
- Use Jinja2 template syntax
- Support template variables

## Using Prompts

### Through tnh-gen CLI

The most common way to use prompts is through the `tnh-gen` command-line tool:

```bash
# Basic prompt processing
tnh-gen run --prompt prompt_name --input-file input.txt

# Process with sections (pass a vars JSON file)
tnh-gen run --prompt format_xml --input-file input.txt --vars sections.json

# Process with inline variables
tnh-gen run --prompt format_xml --input-file input.txt --var key=value
```

```bash
# List available prompts
tnh-gen list

# Run a specific prompt
tnh-gen run --prompt translate --input-file input.txt --var source_lang=vi --var target_lang=en
```

### Programmatic Usage

For developers building tools that use the prompt system:

```python
from tnh_scholar.ai_text_processing import Prompt, PromptCatalog

# Initialize prompt catalog
prompt_catalog = PromptCatalog(prompt_dir)

# Load a prompt
prompt = prompt_catalog.load("my_prompt")

# Apply template values
result = prompt.apply_template({
    "language": "English",
    "style_convention": "APA"
})
```

## Prompt Location

By default, prompts are stored in the user's home directory under:

```bash
~/.config/tnh-scholar/prompts/
```

(Patterns are legacy terminology; the directory is now `prompts`.)

This location can be customized by setting the `TNH_PROMPT_DIR` environment variable:

```bash
# In .bashrc, .zshrc, or similar:
export TNH_PROMPT_DIR=/path/to/prompts
```

(or loaded through a `.env` file for development installations.)

The prompt system will:

1. First check for `TNH_PROMPT_DIR` environment variable
2. If not set, use the default ~/.config/tnh-scholar/prompts
3. Create the prompt directory if it doesn't exist

When using a prompt name with `tnh-gen` (for example, `tnh-gen run --prompt my_prompt`), the system searches for a corresponding .md file (for example, `my_prompt.md`) in the prompt directory and its subdirectories.

### Default Prompt/Patterns

Through the setup utility, tnh-setup, the user has the option to download and install several default and example prompts.

**Note**: The prompt system is used by `tnh-gen`. Default prompts expected in the prompts directory:

- default_punctuate.md - Default punctuation prompt
- default_section.md - Default section analysis pattern
- default_line_translation.md - Default translation pattern

These provide basic functionality but can be customized or overridden by creating patterns with the same names in your prompt directory.

### Pattern Integration

The prompt system can be integrated into other tools and workflows:

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

- `$HOME/.config/tnh-scholar/prompts` (default search location)

- A custom directory specified by TNH_PROMPT_DIR environment variable, which can also be configured in a .env file.

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
