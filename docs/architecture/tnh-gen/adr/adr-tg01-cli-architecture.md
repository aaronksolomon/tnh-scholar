---
title: "ADR-TG01: tnh-gen CLI Architecture"
description: "Core command structure, error handling, and configuration for the unified TNH Scholar CLI tool"
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Sonnet 4.5"
status: implemented
created: "2025-12-07"
---
# ADR-TG01: tnh-gen CLI Architecture

Defines the core architecture, command structure, error handling, and configuration system for the `tnh-gen` CLI tool—TNH Scholar's unified command-line interface for GenAI-powered text processing.

- **Filename**: `adr-tg01-cli-architecture.md`
- **Heading**: `# ADR-TG01: tnh-gen CLI Architecture`
- **Status**: Implemented
- **Date**: 2025-12-07
- **Authors**: Aaron Solomon, Claude Sonnet 4.5
- **Owner**: aaronksolomon

---

## Context

### Background

TNH Scholar requires a unified command-line interface to:

1. **Replace tnh-fab**: Consolidate scattered CLI tools into a single, coherent interface
2. **Support VS Code Integration**: Provide stable CLI contract for editor extension (ADR-VSC02)
3. **Enable Batch Processing**: Process multiple files with consistent provenance tracking
4. **Improve Discoverability**: Browse and search prompts with rich metadata
5. **Object-Service Compliance**: Align with TNH Scholar architectural patterns (ADR-OS01)

### Requirements

The CLI must:

- Expose prompt system capabilities (ADR-PT04) for discovery and execution
- Integrate with refactored `ai_text_processing` module (ADR-AT03)
- Provide structured JSON output for programmatic consumption
- Handle errors gracefully with clear exit codes and diagnostics
- Support hierarchical configuration with clear precedence rules
- Maintain stable interface across rapid prototype iterations

### Design Principles

1. **CLI-First Integration**: VS Code and other clients communicate exclusively via CLI (no Python imports)
2. **Structured I/O**: Consistent JSON output for machine readability
3. **Progressive Disclosure**: Simple cases simple; complex cases possible
4. **Clear Errors**: Actionable error messages with specific suggestions
5. **Stable Contract**: Interface remains stable for clients even as internals evolve

---

## Decision

### 1. CLI Tool Name and Entry Point

**Tool Name:** `tnh-gen`

**Poetry Configuration:**

```toml
[tool.poetry.scripts]
tnh-gen = "tnh_scholar.cli_tools.tnh_gen.tnh_gen:main"
```

**Installation:**

```bash
poetry install
tnh-gen --version  # Verify installation
```

**Rationale**: `tnh-gen` (TNH Generate) clearly indicates generative AI operations while maintaining TNH Scholar branding.

---

### 2. Command Structure

#### 2.1 Top-Level Commands

```bash
tnh-gen list       # List available prompts with metadata
tnh-gen run        # Execute a prompt with variable substitution
tnh-gen config     # Manage configuration settings
tnh-gen version    # Show version information
tnh-gen help       # Display help information
```

#### 2.2 Global Flags

```bash
--config <path>    # Override config file location
--format <format>  # Output format (json, yaml, text)
--verbose, -v      # Enable verbose logging
--quiet, -q        # Suppress non-error output
--no-color         # Disable colored terminal output
```

**Design Note**: Global flags apply to all commands and follow standard Unix CLI conventions.

---

### 3. Command: `tnh-gen list`

Lists all available prompts with metadata for discovery and selection.

#### 3.1 Signature

```bash
tnh-gen list [OPTIONS]
```

#### 3.2 Options

```bash
--format <format>     # Output format: json (default), yaml, table
--tag <tag>           # Filter by tag (repeatable)
--search <query>      # Search in names/descriptions (case-insensitive)
--keys-only           # Output only prompt keys (one per line)
```

#### 3.3 Output Format (JSON)

```json
{
  "prompts": [
    {
      "key": "translate",
      "name": "Vietnamese-English Translation",
      "description": "Translate Vietnamese dharma texts to English",
      "tags": ["translation", "dharma"],
      "required_variables": ["source_lang", "target_lang", "input_text"],
      "optional_variables": ["context"],
      "default_model": "gpt-4o",
      "output_mode": "text",
      "version": "1.0"
    },
    {
      "key": "summarize",
      "name": "Summarize Teaching",
      "description": "Generate concise summary of dharma teaching",
      "tags": ["summarization", "dharma"],
      "required_variables": ["input_text"],
      "optional_variables": ["max_length"],
      "default_model": "gpt-4o-mini",
      "output_mode": "text",
      "version": "1.0"
    }
  ],
  "count": 2
}
```

#### 3.4 Output Format (Table)

```text
KEY         NAME                               TAGS                  MODEL
translate   Vietnamese-English Translation     translation, dharma   gpt-4o
summarize   Summarize Teaching                 summarization         gpt-4o-mini
```

#### 3.5 Examples

```bash
# List all prompts as JSON
tnh-gen list --format json

# List prompts with "translation" tag
tnh-gen list --tag translation

# Search for summarization prompts
tnh-gen list --search summarize

# Get just the keys for scripting
tnh-gen list --keys-only
```

#### 3.6 Implementation Notes

- Calls `PromptsAdapter.list_all()` to retrieve all prompts (see ADR-TG02)
- Metadata schema defined in ADR-PT04 §2 (PromptMetadata)
- Filtering and search performed client-side for simplicity

---

### 4. Command: `tnh-gen run`

Executes a prompt with variable substitution and AI processing.

#### 4.1 Signature

```bash
tnh-gen run --prompt <key> [OPTIONS]
```

#### 4.2 Required Options

```bash
--prompt <key>         # Prompt key to execute (from tnh-gen list)
--input-file <path>    # Input file (content auto-injected as input_text)
```

#### 4.3 Variable Passing Options

**Style 1: JSON file** (preferred for complex variables)

```bash
--vars <path>          # JSON file with variable definitions
```

**Style 2: Inline parameters** (convenient for simple cases)

```bash
--var <key>=<value>    # Variable assignment (repeatable)
```

#### 4.4 Model and Parameter Overrides

```bash
--model <model_name>       # Override prompt's default model
--intent <intent>          # Routing hint (translation, summarization, etc.)
--max-tokens <int>         # Max output tokens
--temperature <float>      # Model temperature (0.0-2.0)
--top-p <float>            # Nucleus sampling parameter
```

#### 4.5 Output Options

```bash
--output-file <path>       # Write result to file
--format <format>          # Output format: json (default), text
--no-provenance            # Omit provenance markers from output
--streaming                # Enable streaming output (future)
```

#### 4.6 Variable Precedence

Variables are merged in this precedence order (highest to lowest):

1. **Inline `--var` parameters** (highest precedence)
2. **JSON file via `--vars`**
3. **Input file content** (auto-injected as `input_text`) (lowest precedence)

**Example:**

```bash
tnh-gen run --prompt translate \
  --input-file teaching.md \
  --var source_lang=vi \
  --var target_lang=en \
  --var context="Dharma talk" \
  --output-file teaching.translate.md
```

**Variable Resolution:**

```json
{
  "input_text": "<contents of teaching.md>",
  "source_lang": "vi",
  "target_lang": "en",
  "context": "Dharma talk"
}
```

#### 4.7 Success Output (JSON)

Exit code: `0`

```json
{
  "status": "succeeded",
  "result": {
    "text": "...",
    "model": "gpt-4o",
    "usage": {
      "prompt_tokens": 1234,
      "completion_tokens": 567,
      "total_tokens": 1801,
      "estimated_cost_usd": 0.08
    },
    "latency_ms": 3456,
    "correlation_id": "01HQXYZ123ABC"
  },
  "provenance": {
    "backend": "openai",
    "model": "gpt-4o",
    "prompt_key": "translate",
    "prompt_fingerprint": "sha256:abc123...",
    "prompt_version": "1.0",
    "started_at": "2025-12-07T10:30:00Z",
    "completed_at": "2025-12-07T10:30:03Z",
    "schema_version": "1.0"
  }
}
```

#### 4.8 File Output Handling

When `--output-file` is specified:

1. Write result text to file
2. Prepend provenance markers (unless `--no-provenance`)
3. Use appropriate format (markdown, JSON, etc.)
4. Print success message to stderr
5. Print JSON response to stdout (for client parsing)

**Provenance Marker Format:**

```markdown
<!--
TNH-Scholar Generated Content
Prompt: translate (v1.0)
Model: gpt-4o
Fingerprint: sha256:abc123...
Correlation ID: 01HQXYZ123ABC
Generated: 2025-12-07T10:30:03Z
-->

[Generated content follows...]
```

#### 4.9 Examples

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

# JSON output without file
tnh-gen run --prompt extract_quotes \
  --input-file teaching.md \
  --format json
```

---

### 5. Error Handling and Exit Codes

#### 5.1 Exit Code Taxonomy

| Exit Code | Error Type       | Description                                    |
|-----------|------------------|------------------------------------------------|
| `0`       | Success          | Operation completed successfully               |
| `1`       | Policy Error     | Budget exceeded, size limits, validation failed|
| `2`       | Transport Error  | API failure, timeout, network issues           |
| `3`       | Provider Error   | Model unavailable, rate limit, auth failure    |
| `4`       | Format Error     | JSON parse failure, schema validation failed   |
| `5`       | Input Error      | Invalid arguments, missing required variables  |

**Rationale**: Exit codes follow semantic categories to enable programmatic error handling by clients (VS Code, scripts).

#### 5.2 Error Message Format

All errors output structured JSON to stdout:

```json
{
  "status": "failed",
  "error": "<human-readable error message>",
  "diagnostics": {
    "error_type": "<ErrorClass>",
    "error_code": "<MACHINE_READABLE_CODE>",
    "<context-specific fields>": "...",
    "suggestion": "<actionable suggestion for user>"
  },
  "correlation_id": "<ulid>"
}
```

**Design Note**: Structured error format enables VS Code extension to display context-appropriate error messages and suggestions.

#### 5.3 Error Mapping

```python
# Map GenAI Service errors to exit codes
ERROR_CODE_MAP = {
    PolicyError: 1,
    TransportError: 2,
    ProviderError: 3,
    FormatError: 4,
    ValueError: 5,
    KeyError: 5,
}
```

#### 5.4 Example Error Messages

**Policy Error (exit 1):**

```json
{
  "status": "failed",
  "error": "Budget exceeded: estimated cost $0.15 exceeds maximum $0.10",
  "diagnostics": {
    "error_type": "PolicyError",
    "error_code": "BUDGET_EXCEEDED",
    "estimated_cost": 0.15,
    "max_cost": 0.10,
    "suggestion": "Increase 'max_dollars' in config or reduce input size"
  },
  "correlation_id": "01HQXYZ789DEF"
}
```

**Input Error (exit 5):**

```json
{
  "status": "failed",
  "error": "Missing required variable: 'source_lang'",
  "diagnostics": {
    "error_type": "InputError",
    "error_code": "MISSING_REQUIRED_VARIABLE",
    "missing_variable": "source_lang",
    "required_variables": ["source_lang", "target_lang", "input_text"],
    "suggestion": "Provide --var source_lang=<value> or include in --vars JSON file"
  },
  "correlation_id": "01HQXYZ456GHI"
}
```

---

### 6. Command: `tnh-gen config`

Manages configuration settings with hierarchical precedence.

#### 6.1 Subcommands

```bash
tnh-gen config show              # Display current configuration
tnh-gen config get <key>         # Get specific config value
tnh-gen config set <key> <value> # Set config value
tnh-gen config list              # List all config keys
```

#### 6.2 Configuration Sources and Precedence

Configuration loaded in this order (highest to lowest precedence):

1. **CLI flags** (e.g., `--model gpt-4o`)
2. **Workspace config** (`.vscode/tnh-scholar.json` or local project config)
3. **User config** (`~/.config/tnh-scholar/config.json`)
4. **Environment variables** (`TNH_GENAI_MODEL`, `OPENAI_API_KEY`, `TNH_PROMPT_DIR`)
5. **Defaults** (defined in GenAI Service and prompt system)

#### 6.3 Configuration Schema

```json
{
  "prompt_catalog_dir": "/path/to/prompts",
  "default_model": "gpt-4o-mini",
  "max_dollars": 0.10,
  "max_input_chars": 50000,
  "default_temperature": 0.2,
  "api_key": "$OPENAI_API_KEY",
  "cli_path": null
}
```

**Note**: `api_key` can reference environment variables using `$VAR_NAME` syntax.

#### 6.4 Examples

```bash
# Show all configuration
tnh-gen config show --format json

# Get specific value
tnh-gen config get default_model

# Set value (writes to user config)
tnh-gen config set max_dollars 0.25

# Set workspace-level config
tnh-gen config set --workspace prompt_catalog_dir ./prompts
```

---

### 7. Command: `tnh-gen version`

Displays version information for debugging and compatibility verification.

#### 7.1 Output Format

```json
{
  "tnh_scholar": "0.2.0",
  "tnh_gen": "0.1.0",
  "python": "3.12.1",
  "platform": "darwin",
  "prompt_system_version": "1.0.0",
  "genai_service_version": "1.0.0"
}
```

#### 7.2 Example

```bash
tnh-gen version --format json
```

---

### 8. Implementation Architecture

#### 8.1 Module Structure

```text
src/tnh_scholar/cli_tools/tnh_gen/
├── __init__.py
├── tnh_gen.py               # Main entry point, CLI argument parsing
├── commands/
│   ├── __init__.py
│   ├── list.py              # tnh-gen list implementation
│   ├── run.py               # tnh-gen run implementation
│   ├── config.py            # tnh-gen config implementation
│   └── version.py           # tnh-gen version implementation
├── output/
│   ├── __init__.py
│   ├── formatter.py         # JSON/YAML/table output formatting
│   └── provenance.py        # Provenance marker generation
├── errors.py                # Error handling and exit code mapping
└── config_loader.py         # Configuration discovery and loading
```

#### 8.2 CLI Framework

Use **Typer** for argument parsing with rich type hints and automatic help generation:

```python
# tnh_gen.py
import typer
from typing import Optional
from pathlib import Path
from enum import Enum
from tnh_scholar.cli_tools.tnh_gen.commands import list_cmd, run_cmd, config_cmd

class OutputFormat(str, Enum):
    """Output format options."""
    json = "json"
    yaml = "yaml"
    text = "text"

app = typer.Typer(
    name="tnh-gen",
    help="TNH-Gen: Unified CLI for TNH Scholar GenAI operations",
    add_completion=False
)

# Global state for shared options
class CLIContext:
    def __init__(self):
        self.config_path: Optional[Path] = None
        self.format: OutputFormat = OutputFormat.json
        self.verbose: bool = False

ctx = CLIContext()

@app.callback()
def main(
    config: Optional[Path] = typer.Option(None, "--config", help="Override config file location"),
    format: OutputFormat = typer.Option(OutputFormat.json, "--format", help="Output format"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress non-error output"),
):
    """Global options for all tnh-gen commands."""
    ctx.config_path = config
    ctx.format = format
    ctx.verbose = verbose

# Register subcommands
app.add_typer(list_cmd.app, name="list")
app.add_typer(run_cmd.app, name="run")
app.add_typer(config_cmd.app, name="config")
app.command()(version_cmd.version)

if __name__ == "__main__":
    app()
```

**Rationale**: Typer provides:

- **Better Type Hints**: Automatic validation and conversion based on Python type annotations
- **Rich Help**: Automatic generation of beautiful help text with colors and formatting
- **Fewer Decorators**: Cleaner code with type-based argument inference
- **Pydantic Integration**: Native support for Pydantic models (aligns with TNH Scholar object-service patterns)
- **Modern Python**: Built on top of Click but with Python 3.6+ features

#### 8.3 Integration Points

The CLI integrates with:

- **Prompt System** (ADR-PT04, ADR-TG02): Via `PromptsAdapter` for discovery and rendering
- **AI Text Processing** (ADR-AT03): Via refactored `TextProcessor` pipeline
- **GenAI Service** (ADR-A13): Via `GenAIService.generate()` for completions
- **Configuration** (ADR-OS01): Via hierarchical settings/config/params pattern

**Design Note**: CLI acts as a thin orchestration layer, delegating domain logic to appropriate services.

---

## Consequences

- **Positive**:
  - Stable CLI contract for VS Code and scripting clients
  - Structured JSON output enables programmatic consumption and error handling
  - Semantic exit codes and detailed diagnostics improve debugging
  - Progressive disclosure: simple commands (`list`) and complex commands (`run`) coexist
  - Hierarchical configuration with clear precedence rules
  - Typer provides type-safe arguments, rich help generation, and Pydantic integration
  - Unified interface consolidates scattered CLI tools (`tnh-fab`, etc.)

- **Negative**:
  - JSON-first output may be verbose for human-only CLI usage (mitigated by `--format text`)
  - Hierarchical configuration precedence requires clear documentation
  - Error mapping requires synchronization between GenAI Service errors and CLI exit codes
  - Typer dependency adds to project dependencies (though built on Click, already present)

---

## Alternatives Considered

### Click (Rejected)

`tnh-fab` currently uses Click, which is mature and widely adopted.

**Rejected because**:

- Less type-safe: Requires manual type conversion and validation
- More verbose: Requires explicit decorators for all arguments
- Less modern: Predates Python 3.6+ type hints
- No Pydantic integration: Harder to align with TNH Scholar object-service patterns

### argparse (Rejected)

Standard library solution, no external dependencies.

**Rejected because**:

- Extremely verbose: Requires manual parser configuration
- Poor composability: Subcommands require boilerplate
- No automatic help generation: Must manually format help text
- Low-level API: Requires significant code for basic CLI

### Fire (Rejected)

Google's Fire library auto-generates CLIs from Python objects.

**Rejected because**:

- Too magical: Exposes Python internals directly to CLI (poor contract stability)
- Limited control: Hard to customize argument parsing behavior
- Poor error messages: Generic Python exceptions exposed to users
- Not designed for multi-command CLIs

---

## Migration from tnh-fab

### Deprecation Strategy

1. **Phase 1 (v0.2.0)**: Introduce `tnh-gen`, keep `tnh-fab` functional
2. **Phase 2 (v0.3.0)**: Add deprecation warnings to `tnh-fab`
3. **Phase 3 (v0.4.0)**: Remove `tnh-fab` from Poetry scripts

### Feature Parity

Map existing `tnh-fab` commands to `tnh-gen`:

| `tnh-fab` Command | `tnh-gen` Equivalent |
|-------------------|----------------------|
| `tnh-fab run <pattern>` | `tnh-gen run --prompt <pattern>` |
| (no equivalent) | `tnh-gen list` (new) |
| (no equivalent) | `tnh-gen config` (new) |

**Migration Guide**: Provide side-by-side examples in user documentation.

---

## Open Questions

1. **Streaming Output**: How should `--streaming` work? Line-by-line? Token-by-token? (Deferred to future ADR)
2. **Batch Operations**: Should `tnh-gen run` support multiple input files? (Deferred to v0.2.0)
3. **Dry-Run Mode**: Add `--dry-run` to preview requests without API calls? (Deferred)
4. **Caching**: Should CLI cache `list` results locally? (Deferred)

---

## Testing Strategy

### Unit Tests

```python
# tests/cli_tools/tnh_gen/test_run.py
from typer.testing import CliRunner
from tnh_scholar.cli_tools.tnh_gen.tnh_gen import app

runner = CliRunner()

def test_run_with_inline_vars():
    """Test run command with inline variable parameters."""
    result = runner.invoke(app, [
        'run',
        '--prompt', 'translate',
        '--input-file', 'test.md',
        '--var', 'source_lang=vi',
        '--var', 'target_lang=en'
    ])

    assert result.exit_code == 0
    output = json.loads(result.stdout)
    assert output['status'] == 'succeeded'
```

### Integration Tests

```python
@pytest.mark.integration
def test_run_with_real_prompt_system():
    """Test against live prompt system (requires TNH_PROMPT_DIR)."""
    # Run only when RUN_INTEGRATION_TESTS=1
    result = runner.invoke(app, ['list', '--format', 'json'])
    assert result.exit_code == 0
```

### Golden Tests

- Store expected JSON outputs for known prompts
- Validate output schema against golden files
- Ensure backward compatibility across versions

---

## References

### Related ADRs

- [ADR-TG02: Prompt System Integration](/architecture/tnh-gen/adr/adr-tg02-prompt-integration.md) - CLI ↔ prompt system
- [ADR-AT03: AI Text Processing Refactor](/architecture/ai-text-processing/adr/adr-at03-object-service-refactor.md) - 3-tier refactor
- [ADR-PT04: Prompt System Refactor](/architecture/prompt-system/adr/adr-pt04-prompt-system-refactor.md) - Prompt architecture
- [ADR-VSC02: VS Code Integration](/architecture/ui-ux/vs-code-integration/adr-vsc02-tnh-gen-cli-implementation.md) - VS Code client
- [ADR-OS01: Object-Service Architecture](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md) - Architecture patterns

### External References

- [Click Documentation](https://click.palletsprojects.com/) - CLI framework
- [12 Factor CLI Apps](https://medium.com/@jdxcode/12-factor-cli-apps-dd3c227a0e46) - CLI design principles

---

## Addendum: 2025-12-28 - Provenance Format Standardization

**Issue**: Initial ADR specified HTML comment format for provenance markers (§4.8), which is inconsistent with TNH Scholar's standard use of YAML frontmatter throughout documentation, ADRs, and other generated content.

**Decision**: Standardize on **YAML frontmatter** for provenance metadata to maintain consistency across the TNH Scholar ecosystem.

**Planned Format**:

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

**Benefits**:

- Consistent with TNH Scholar metadata standards (ADRs, docs, etc.)
- Machine-parseable with standard YAML libraries
- Widely supported across tools (MkDocs, static site generators, etc.)
- Enables downstream processing and validation

**Migration**: Implementation work tracked in TODO.md (see "Provenance Format Refactor"). Current HTML comment format will be replaced in a future branch.

**Status**: Accepted addendum; implementation pending

---

**Approval Path**: Architecture review → Implementation → Testing → Documentation
