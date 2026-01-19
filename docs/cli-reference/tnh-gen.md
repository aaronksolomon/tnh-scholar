---
title: "tnh-gen"
description: "Complete reference for the tnh-gen CLI - TNH Scholar's unified command-line interface for GenAI-powered text processing"
owner: ""
author: ""
status: current
created: "2025-12-28"
---
# tnh-gen

TNH Scholar's unified command-line interface for GenAI-powered text processing operations. The `tnh-gen` CLI provides prompt discovery, text processing, configuration management, and VS Code integration support.

## Overview

`tnh-gen` is a modern, object-service compliant CLI tool that replaces the legacy `tnh-fab` tool. It provides:

- **Prompt Discovery**: Browse and search available prompts with rich metadata
- **Text Processing**: Execute AI-powered transformations (translation, sectioning, summarization, etc.)
- **Configuration Management**: Hierarchical configuration with clear precedence rules
- **Human-Friendly Defaults**: Optimized for direct CLI usage with `--api` flag for programmatic consumption
- **Provenance Tracking**: All outputs include generation metadata and fingerprints

## Installation

```bash
pip install tnh-scholar
```

Verify installation:

```bash
tnh-gen version
```

## Quick Start

```bash
# List available prompts
tnh-gen list

# Execute a prompt (human-friendly output)
tnh-gen run --prompt translate \
  --input-file teaching.md \
  --var source_lang=vi \
  --var target_lang=en

# Get machine-readable output for scripts
tnh-gen run --prompt translate \
  --input-file teaching.md \
  --var source_lang=vi \
  --var target_lang=en \
  --api
```

## Global Flags

These flags work with all commands:

```bash
--api              # Enable machine-readable API contract output (JSON)
--format FORMAT    # Output format: json, yaml, text, table
--quiet, -q        # Suppress non-error output
--no-color         # Disable colored terminal output
--config PATH      # Override config file location
```

### Output Modes

`tnh-gen` has two output modes designed for different use cases:

**Human Mode (Default)**:
- Optimized for direct CLI usage
- Simplified, readable output
- Command-specific formatting
- Omits verbose metadata

**API Mode (`--api` flag)**:
- Optimized for programmatic consumption (VS Code, scripts)
- Complete structured JSON output
- Full metadata, provenance, and diagnostics
- Stable machine-readable contract

**Flag Precedence**:
1. `--api` controls **WHAT** data is included (full contract vs. human-friendly)
2. `--format` controls **HOW** it's serialized (json, yaml, text, table)
3. `--api` implies JSON by default; can be combined with `--format yaml`
4. `--api` **cannot** be combined with `--format text` or `--format table`

**Examples**:

```bash
# Human-friendly (default)
tnh-gen list
# → Simplified text format with descriptions

# API mode (JSON contract)
tnh-gen list --api
# → Full metadata as JSON

# API mode with YAML serialization
tnh-gen list --api --format yaml
# → Full metadata as YAML

# Human-friendly table
tnh-gen list --format table
# → Simplified table format
```

## Commands

### `tnh-gen list`

List all available prompts with metadata for discovery and selection.

#### Synopsis

```bash
tnh-gen list [OPTIONS]
```

#### Options

```bash
--tag TAG          # Filter by tag (repeatable)
--search QUERY     # Search in names/descriptions (case-insensitive)
--keys-only        # Output only prompt keys (one per line)
--format FORMAT    # Output format: text (default), json, yaml, table
--api              # Enable API mode with full metadata
```

#### Human-Friendly Output (Default)

```bash
$ tnh-gen list
Available Prompts (3)

daily - Daily Guidance
  Daily guidance prompt for testing.
  Variables: audience, [location]
  Model: gpt-4o | Tags: guidance, study

translate - Vietnamese-English Translation
  Translate Vietnamese dharma texts to English with context awareness.
  Variables: source_lang, target_lang, input_text, [context]
  Model: gpt-4o | Tags: translation, dharma

summarize - Summarize Teaching
  Generate concise summary of dharma teaching.
  Variables: input_text, [max_length]
  Model: gpt-4o-mini | Tags: summarization, dharma
```

**Format Notes**:
- Optional variables shown in brackets: `[var_name]`
- Blank line between prompts for easy scanning
- Metadata on single line: Model and Tags

#### API Output

```bash
$ tnh-gen list --api
{
  "prompts": [
    {
      "key": "translate",
      "name": "Vietnamese-English Translation",
      "description": "Translate Vietnamese dharma texts to English",
      "tags": ["translation", "dharma"],
      "required_variables": ["source_lang", "target_lang", "input_text"],
      "optional_variables": ["context"],
      "default_variables": {},
      "default_model": "gpt-4o",
      "output_mode": "text",
      "version": "1.0.0",
      "warnings": []
    }
  ],
  "count": 1,
  "sources": {
    "catalog_type": "filesystem",
    "catalog_path": "/path/to/prompts"
  }
}
```

#### Table Format

```bash
$ tnh-gen list --format table
KEY         NAME                               TAGS                  MODEL
translate   Vietnamese-English Translation     translation, dharma   gpt-4o
summarize   Summarize Teaching                 summarization         gpt-4o-mini
```

#### Filtering Examples

```bash
# Filter by tag
tnh-gen list --tag translation

# Search by keyword
tnh-gen list --search summarize

# Combine filters
tnh-gen list --tag dharma --search translation

# Get just the keys for scripting
tnh-gen list --keys-only
translate
summarize
daily
```

---

### `tnh-gen run`

Execute a prompt with variable substitution and AI processing.

#### Synopsis

```bash
tnh-gen run --prompt KEY [OPTIONS]
```

#### Required Options

```bash
--prompt KEY         # Prompt key to execute (from tnh-gen list)
--input-file PATH    # Input file (content auto-injected as input_text)
```

#### Variable Passing Options

**Style 1: JSON file** (preferred for complex variables)

```bash
--vars PATH          # JSON file with variable definitions
```

**Style 2: Inline parameters** (convenient for simple cases)

```bash
--var KEY=VALUE      # Variable assignment (repeatable)
```

#### Model and Parameter Overrides

```bash
--model MODEL_NAME       # Override prompt's default model
--intent INTENT          # Routing hint (translation, summarization, etc.)
--max-tokens INT         # Max output tokens
--temperature FLOAT      # Model temperature (0.0-2.0)
--top-p FLOAT            # Nucleus sampling parameter
```

#### Output Options

```bash
--output-file PATH       # Write result to file
--format FORMAT          # Output format: text (default), json
--no-provenance          # Omit provenance markers from output
--api                    # Enable API mode with full metadata
```

#### Variable Precedence

Variables are merged in this precedence order (highest to lowest):

1. **Inline `--var` parameters** (highest precedence)
2. **JSON file via `--vars`**
3. **Input file content** (auto-injected as `input_text`) (lowest precedence)

**Example:**

```bash
tnh-gen run --prompt translate \
  --input-file teaching.md \
  --vars base_vars.json \
  --var source_lang=vi \
  --var target_lang=en
```

If `base_vars.json` contains `{"source_lang": "en"}`, the inline `--var source_lang=vi` wins.

#### Human-Friendly Output (Default)

```bash
$ tnh-gen run --prompt translate --input-file teaching.md --var source_lang=vi --var target_lang=en

[Generated translation text appears here without JSON wrapper...]
```

**Behavior**:
- Only the generated text is printed to stdout
- No JSON structure wrapper
- Suitable for piping to other commands or files

#### API Output

```bash
$ tnh-gen run --prompt translate --input-file teaching.md --var source_lang=vi --var target_lang=en --api
{
  "status": "succeeded",
  "result": {
    "text": "[Generated translation...]",
    "model": "gpt-4o",
    "usage": {
      "prompt_tokens": 1234,
      "completion_tokens": 567,
      "total_tokens": 1801,
      "estimated_cost_usd": 0.08
    },
    "latency_ms": 3456
  },
  "provenance": {
    "backend": "openai",
    "model": "gpt-4o",
    "prompt_key": "translate",
    "prompt_fingerprint": "sha256:abc123...",
    "prompt_version": "1.0.0",
    "started_at": "2025-12-28T10:30:00Z",
    "completed_at": "2025-12-28T10:30:03Z",
    "schema_version": "1.0"
  },
  "trace_id": "01HQXYZ123ABC"
}
```

#### File Output Handling

When `--output-file` is specified:

1. Write result text to file
2. Prepend provenance markers (unless `--no-provenance`)
3. Use appropriate format (markdown, JSON, etc.)
4. Print success message to stderr
5. Print JSON response to stdout (for client parsing)

**Provenance Marker Format (YAML frontmatter):**

```yaml
---
tnh_scholar_generated: true
prompt_key: translate
prompt_version: "1.0.0"
model: gpt-4o
fingerprint: sha256:abc123...
trace_id: 01HQXYZ123ABC
generated_at: "2025-12-28T10:30:03Z"
schema_version: "1.0"
---

[Generated content follows...]
```

#### Examples

```bash
# Simple translation with inline variables
tnh-gen run --prompt translate \
  --input-file teaching.md \
  --var source_lang=vi \
  --var target_lang=en \
  --output-file teaching.en.md

# Complex variables via JSON file
tnh-gen run --prompt summarize \
  --input-file lecture.md \
  --vars config.json \
  --output-file lecture.summary.md

# Override model
tnh-gen run --prompt translate \
  --input-file teaching.md \
  --vars vars.json \
  --model gpt-4o \
  --output-file teaching.translate.md

# JSON output for scripting
tnh-gen run --prompt extract_quotes \
  --input-file teaching.md \
  --api > output.json
```

---

### `tnh-gen config`

Manage configuration settings with hierarchical precedence.

#### Synopsis

```bash
tnh-gen config SUBCOMMAND [OPTIONS]
```

#### Subcommands

```bash
tnh-gen config show              # Display current configuration
tnh-gen config get KEY           # Get specific config value
tnh-gen config set KEY VALUE     # Set config value
tnh-gen config list              # List all config keys
```

#### Configuration Sources and Precedence

Configuration loaded in this order (highest to lowest precedence):

1. **CLI flags** (e.g., `--model gpt-4o`)
2. **Workspace config** (`.vscode/tnh-scholar.json` or local project config)
3. **User config** (`~/.config/tnh-scholar/config.json`)
4. **Environment variables** (`TNH_GENAI_MODEL`, `OPENAI_API_KEY`, `TNH_PROMPT_DIR`)
5. **Defaults** (defined in GenAI Service and prompt system)

#### Configuration Schema

```json
{
  "prompt_catalog_dir": "/path/to/prompts",
  "default_model": "gpt-4o-mini",
  "max_dollars": 0.10,
  "max_input_chars": 50000,
  "default_temperature": 0.2,
  "provider_api_keys": {
    "openai": "$OPENAI_API_KEY",
    "anthropic": "$ANTHROPIC_API_KEY"
  }
}
```

**Note**: API keys can reference environment variables using `$VAR_NAME` syntax.

#### Human-Friendly Output (Default)

```bash
$ tnh-gen config show
prompt_catalog_dir: /custom/path
default_model: gpt-4o-mini
max_dollars: 0.10
```

**Behavior**:
- YAML format for editability
- Shows only user/workspace overrides
- Omits defaults and source annotations

#### API Output

```bash
$ tnh-gen config show --api
{
  "config": {
    "prompt_catalog_dir": "/custom/path",
    "default_model": "gpt-4o-mini",
    "max_dollars": 0.10,
    "provider_api_keys": {
      "openai": "${OPENAI_API_KEY}",
      "anthropic": "${ANTHROPIC_API_KEY}"
    }
  },
  "sources": {
    "prompt_catalog_dir": "workspace",
    "default_model": "user",
    "max_dollars": "defaults",
    "provider_api_keys": "defaults"
  },
  "config_files": [
    "/path/to/workspace/.tnh-scholar/config.yaml",
    "~/.config/tnh-scholar/config.yaml"
  ]
}
```

#### Examples

```bash
# Show all configuration (human-friendly YAML)
tnh-gen config show

# Show all configuration with sources (API mode)
tnh-gen config show --api

# Get specific value
tnh-gen config get default_model
gpt-4o-mini

# Set value (writes to user config)
tnh-gen config set max_dollars 0.25

# Set workspace-level config
tnh-gen config set --workspace prompt_catalog_dir ./prompts
```

---

### `tnh-gen version`

Display version information for debugging and compatibility verification.

#### Synopsis

```bash
tnh-gen version [OPTIONS]
```

#### Human-Friendly Output (Default)

```bash
$ tnh-gen version
tnh-gen 0.2.2 (tnh-scholar 0.2.2)
Python 3.12.4 on darwin
```

#### API Output

```bash
$ tnh-gen version --api
{
  "tnh_scholar": "0.2.2",
  "tnh_gen": "0.2.2",
  "python": "3.12.4",
  "platform": "darwin",
  "prompt_system_version": "1.0.0",
  "genai_service_version": "1.0.0"
}
```

---

## Error Handling

### Exit Codes

| Exit Code | Error Type       | Description                                    |
|-----------|------------------|------------------------------------------------|
| `0`       | Success          | Operation completed successfully               |
| `1`       | Policy Error     | Budget exceeded, size limits, validation failed|
| `2`       | Transport Error  | API failure, timeout, network issues           |
| `3`       | Provider Error   | Model unavailable, rate limit, auth failure    |
| `4`       | Format Error     | JSON parse failure, schema validation failed   |
| `5`       | Input Error      | Invalid arguments, missing required variables  |

### Error Output

#### Human-Friendly Error

```bash
$ tnh-gen run --prompt missing_prompt --input-file test.md
# stdout:
Error: Prompt 'missing_prompt' not found

Suggestion: Run 'tnh-gen list' to see available prompts, or check your prompt key spelling.

# stderr:
[2025-12-28 10:15:23] trace_id=01JGKZ... error_code=PROMPT_NOT_FOUND
```

#### API Error

```bash
$ tnh-gen run --prompt missing_prompt --input-file test.md --api
# stdout:
{
  "status": "failed",
  "error": "Prompt 'missing_prompt' not found",
  "diagnostics": {
    "error_type": "PromptNotFoundError",
    "error_code": "PROMPT_NOT_FOUND",
    "suggestion": "Run 'tnh-gen list' to see available prompts"
  },
  "trace_id": "01JGKZ..."
}

# stderr:
[2025-12-28 10:15:23] trace_id=01JGKZ... error_code=PROMPT_NOT_FOUND
```

**Trace ID**: Use the trace ID from stderr to correlate with logs or support requests. Set `TNH_TRACE_ID` environment variable to override auto-generation.

---

## Environment Variables

```bash
TNH_PROMPT_DIR         # Path to prompt catalog directory
OPENAI_API_KEY         # OpenAI API key (required for OpenAI models)
ANTHROPIC_API_KEY      # Anthropic API key (required for Claude models)
TNH_GENAI_MODEL        # Default model to use
TNH_TRACE_ID           # Override auto-generated trace ID
TNH_CONFIG_PATH        # Override config file location
```

---

## Architecture

`tnh-gen` follows object-service architecture patterns and integrates with:

- **Prompt System** - Discovery and rendering via `PromptsAdapter`
- **GenAI Service** - Model execution and provenance tracking
- **AI Text Processing** - Refactored text processing pipeline
- **Configuration System** - Hierarchical settings management

For architectural details, see:
- [ADR-TG01: CLI Architecture](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md)
- [ADR-TG01.1: Human-Friendly Defaults](/architecture/tnh-gen/adr/adr-tg01.1-human-friendly-defaults.md)
- [ADR-TG02: Prompt System Integration](/architecture/tnh-gen/adr/adr-tg02-prompt-integration.md)
- [TNH-Gen Architecture Overview](/architecture/tnh-gen/index.md)

---

## Migration from tnh-fab

The `tnh-gen` CLI supersedes the legacy `tnh-fab` tool. Key differences:

| Aspect | tnh-fab (Legacy) | tnh-gen (Current) |
|--------|------------------|-------------------|
| Architecture | Monolithic, mixed concerns | Object-service compliant |
| Output Mode | JSON-first | Human-friendly by default |
| Prompt System | Legacy patterns | New prompt catalog |
| Configuration | Ad-hoc, `TNH_PROMPT_DIR` | Hierarchical, `TNH_PROMPT_DIR` |
| VS Code Support | None | First-class with `--api` flag |

**Migration Steps**:

1. Replace `tnh-fab run <pattern>` with `tnh-gen run --prompt <pattern>`
2. Update environment variable to `TNH_PROMPT_DIR`
3. Update scripts to use `--api` flag for JSON output
4. Review configuration files for new schema

For complete migration guide, see [TNH-Gen Architecture](/architecture/tnh-gen/index.md).

---

## See Also

- [Getting Started: Quick Start Guide](/getting-started/quick-start-guide.md)
- [User Guide: Prompt System](/user-guide/prompt-system.md)
- [CLI Reference: Overview](/cli-reference/overview.md)
- [Architecture: TNH-Gen](/architecture/tnh-gen/index.md)
