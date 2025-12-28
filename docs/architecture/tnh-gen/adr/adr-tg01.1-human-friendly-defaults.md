---
title: "ADR-TG01.1: Human-Friendly CLI Defaults with --api Flag"
description: "Default to human-readable output for CLI usage, with --api flag for machine-readable contract output"
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Code - Claude Sonnet 4.5, Codex Max"
status: accepted
created: "2025-12-23"
updated: "2025-12-27"
parent_adr: "adr-tg01-cli-architecture.md"
---
# ADR-TG01.1: Human-Friendly CLI Defaults with --api Flag

Extends [ADR-TG01](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md) to make tnh-gen CLI more human-friendly by default, while preserving machine-readable contract output for programmatic use via `--api` flag.

- **Filename**: `adr-tg01.1-human-friendly-defaults.md`
- **Heading**: `# ADR-TG01.1: Human-Friendly CLI Defaults with --api Flag`
- **Status**: Proposed
- **Date**: 2025-12-23
- **Updated**: 2025-12-27
- **Authors**: Aaron Solomon, Claude Sonnet 4.5
- **Owner**: aaronksolomon
- **Parent ADR**: [ADR-TG01: tnh-gen CLI Architecture](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md)

---

## Context

### Background

ADR-TG01 designed tnh-gen with an API-first approach, optimizing for VS Code integration and programmatic consumption. The CLI defaults to JSON output with complete metadata, which is ideal for structured consumption but verbose for human interactive use.

**Current behavior** (`tnh-gen list --format json`):

```json
{
  "prompts": [
    {
      "key": "daily",
      "name": "Daily Guidance",
      "description": "Daily guidance prompt for testing.",
      "tags": ["guidance", "study"],
      "required_variables": ["audience"],
      "optional_variables": ["location"],
      "default_variables": {"location": "Plum Village"},
      "default_model": "gpt-4o",
      "output_mode": "text",
      "version": "1.0.0",
      "warnings": []
    }
  ],
  "count": 1,
  "sources": {...}
}
```

**Human perspective**: When using the CLI directly (not via VS Code), developers want:

1. Quick scanning of available prompts with descriptions
2. Simple variable lists (not JSON dictionaries)
3. Less visual noise from metadata fields
4. Natural reading experience without JSON syntax

**API perspective**: VS Code extension and scripts need:

1. Complete structured metadata
2. Machine-readable JSON contract
3. All fields including warnings, versions, sources
4. Consistent, stable API output format

### Requirements

1. **Default to human-friendly output** for direct CLI usage
2. **Explicit API mode** via `--api` flag for programmatic consumption
3. **Clear semantic separation**: `--api` = machine contract, `--format` = serialization
4. **Apply across commands** (`list`, `run`, `config`, `version`) consistently
5. **Reserve `--verbose`** for future human-mode verbosity (streaming, extended diagnostics)
6. **Breaking change accepted**: This redesigns the output contract for clarity

---

## Decision

### 1. Default Output Mode: Human-Friendly

**When `--api` is NOT set**, default to simplified human-readable output:

#### `tnh-gen list` (default human mode)

```text
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

**Design choices**:

- **Header**: Shows total count for quick reference
- **Prompt title**: `key - name` on first line (key is what you type in commands)
- **Description**: Full description on second line (indented)
- **Variables**: Simple comma-separated list, optional vars in brackets `[var]`
- **Metadata line**: Compact single line with model and tags
- **Whitespace**: Blank line between prompts for scanning

#### `tnh-gen list --api` (API mode)

```json
{
  "prompts": [
    {
      "key": "daily",
      "name": "Daily Guidance",
      "description": "Daily guidance prompt for testing.",
      "tags": ["guidance", "study"],
      "required_variables": ["audience"],
      "optional_variables": ["location"],
      "default_variables": {"location": "Plum Village"},
      "default_model": "gpt-4o",
      "output_mode": "text",
      "version": "1.0.0",
      "warnings": []
    }
  ],
  "count": 1,
  "sources": {...}
}
```

**API contract**: Full structured output with all metadata fields, stable machine-readable format.

### 2. Flag Semantics

#### New Global Flag: `--api`

```bash
--api      # Enable machine-readable API contract output (JSON by default)
```

**Behavior**:

- **WITHOUT `--api`**: Human-friendly output (command-specific formatting)
- **WITH `--api`**: Machine-readable API contract (JSON with full metadata)

**Precedence rules**:

1. **`--api` flag**: Triggers API mode with full metadata contract
2. **`--format` with `--api`**: Serialization format for API output (json, yaml)
3. **`--format` without `--api`**: Human-friendly output in specified format (yaml, table, text)
4. **Default** (no flags): Human-friendly mode (command-specific text formatting)

**Flag Semantics**:

- `--api` controls **WHAT** data is included (full API contract vs. human-friendly)
- `--format` controls **HOW** it's serialized (json, yaml, text, table)
- `--api` implies JSON by default; can be combined with `--format yaml`
- `--api` **cannot** be combined with `--format text` or `--format table` (API requires structured data)

**Examples**:

```bash
# Human-friendly (default)
tnh-gen list
# → Simplified text format with descriptions

# API mode (JSON contract)
tnh-gen list --api
# → Full metadata as JSON (default for --api)

# API mode with YAML serialization
tnh-gen list --api --format yaml
# → Full metadata as YAML

# Human-friendly YAML (no API mode)
tnh-gen list --format yaml
# → Simplified content as YAML (human-readable)

# Human-friendly table
tnh-gen list --format table
# → Simplified table (key, name, desc, vars, model, tags)

# INVALID: --api requires structured format
tnh-gen list --api --format text
# → Error: --api cannot be combined with --format text (use --format json or yaml)

tnh-gen list --api --format table
# → Error: --api cannot be combined with --format table (use --format json or yaml)
```

### 3. Command-Specific Defaults

**Note**: All filtering and searching flags (`--tag`, `--search`, `--keys-only`) work identically in both human and API modes. Filtering is orthogonal to output format.

**Example**:

```bash
# Human mode with tag filter
$ tnh-gen list --tag translation
Available Prompts (1)

translate - Vietnamese-English Translation
  Translate Vietnamese dharma texts to English with context awareness.
  Variables: source_lang, target_lang, input_text, [context]
  Model: gpt-4o | Tags: translation, dharma

# API mode with same filter
$ tnh-gen list --tag translation --api
{"prompts": [{"key": "translate", ...}], "count": 1}

# Keys-only works in both modes
$ tnh-gen list --keys-only
daily
translate
summarize
```

#### `tnh-gen list`

| Mode            | Default Format | Content                                           |
|-----------------|----------------|---------------------------------------------------|
| Human (default) | Custom text    | Description, variables (simplified), model, tags  |
| API (`--api`)   | JSON           | Full metadata (all fields from ADR-TG01)          |

#### `tnh-gen run`

| Mode            | Default Format   | Content                                                       |
|-----------------|------------------|---------------------------------------------------------------|
| Human (default) | Text output only | Just the generated text (no JSON wrapper)                    |
| API (`--api`)   | JSON             | Full response with status, provenance, usage, latency         |

**Example**:

```bash
# Human mode: just the generated content
$ tnh-gen run --prompt translate --input-file teaching.md --var source_lang=vi --var target_lang=en
[Generated translation text here...]

# API mode: full structured response
$ tnh-gen run --prompt translate --input-file teaching.md --var source_lang=vi --var target_lang=en --api
{
  "status": "succeeded",
  "result": {
    "text": "[Generated translation...]",
    "model": "gpt-4o",
    "usage": {...},
    "latency_ms": 3456
  },
  "provenance": {...}
}
```

#### `tnh-gen config`

| Mode               | Default Format | Content                                                                   |
|--------------------|----------------|---------------------------------------------------------------------------|
| Human (default)    | YAML           | User + workspace config only (no defaults, no source annotations)         |
| API (`--api`)      | JSON           | Full merged config with defaults, sources metadata                        |

**Example**:

```bash
# Human mode: just your overrides
$ tnh-gen config show
prompt_catalog: /custom/path
default_model: gpt-4o-mini

# API mode: full config with metadata
$ tnh-gen config show --api
{
  "config": {
    "prompt_catalog": "/custom/path",
    "default_model": "gpt-4o-mini",
    "provider_api_keys": {
      "openai": "${OPENAI_API_KEY}",
      "anthropic": "${ANTHROPIC_API_KEY}"
    }
  },
  "sources": {
    "prompt_catalog": "workspace",
    "default_model": "user",
    "provider_api_keys": "defaults"
  },
  "config_files": [
    "/path/to/workspace/.tnh-scholar/config.yaml",
    "~/.config/tnh-scholar/config.yaml"
  ]
}
```

**Rationale**: API mode provides machine-readable JSON with full provenance. Human mode stays YAML-first for edit ability.

#### `tnh-gen` Error Responses

| Mode            | Output Channel | Content                                                         |
|-----------------|----------------|----------------------------------------------------------------|
| Human (default) | stdout         | Plain text error + suggestion (trace ID logged to stderr)      |
| API (`--api`)   | stdout         | JSON error envelope with diagnostics and trace_id              |

**Output Channel Specification**:

- **stdout**: Error message (human text or JSON envelope)
- **stderr**: Trace ID, warnings, diagnostics (in both modes)

**Human-friendly error example**:

```bash
$ tnh-gen run --prompt missing_prompt --input-file test.md
# stdout:
Error: Prompt 'missing_prompt' not found

Suggestion: Run 'tnh-gen list' to see available prompts, or check your prompt key spelling.

# stderr:
[2025-12-27 10:15:23] trace_id=01JGKZ... error_code=PROMPT_NOT_FOUND
```

**Trace ID Mapping**: The stderr trace ID can be used to correlate with logs, metrics, or support requests. Set `TNH_TRACE_ID` environment variable to override auto-generation.

**API error example**:

```bash
$ tnh-gen run --prompt missing_prompt --input-file test.md --api
# stdout (JSON for parsing):
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

# stderr (same as human mode):
[2025-12-27 10:15:23] trace_id=01JGKZ... error_code=PROMPT_NOT_FOUND
```

**Implementation**: Update `error_response()` in `errors.py` to check `ctx.api` and format accordingly. Always log trace ID to stderr for correlation.

### 4. Implementation Strategy

#### 4.1 Update `list.py`

**Current** (`list.py:96-127`):

- Always builds full JSON entries with all metadata
- Formats as JSON/YAML/table based on explicit `--format`

**Proposed**:

1. Check `ctx.api` flag to determine output mode
2. If `--api`: build full metadata, serialize as JSON (or YAML if `--format yaml`)
3. If not `--api`: use human-friendly formatter based on `--format` (default: text)
4. Validate `--api` incompatible with `--format text` or `--format table`

```python
# Pseudocode
if ctx.api:
    # API mode: full metadata contract
    if format == 'text' or format == 'table':
        raise CliError("--api cannot be combined with --format text or table")

    entries = [...full metadata...]
    fmt = format or 'json'  # API defaults to JSON
    typer.echo(render_output(payload, fmt))
else:
    # Human mode: simplified output
    if format is None:
        # Default: custom text format
        output = format_human_friendly_list(prompts)
        typer.echo(output)
    elif format == 'yaml':
        # Human-friendly YAML (simplified)
        output = render_simplified_yaml(prompts)
        typer.echo(output)
    elif format == 'table':
        # Human-friendly table
        output = render_table(prompts, simplified=True)
        typer.echo(output)
```

#### 4.2 Add Human-Friendly Formatters

**New module**: `src/tnh_scholar/cli_tools/tnh_gen/output/human_formatter.py`

```python
def format_human_friendly_list(prompts: list[PromptMetadata]) -> str:
    """Format prompts for human readability with optional color.

    Args:
        prompts: List of prompt metadata objects.

    Returns:
        Formatted string with descriptions and simplified variables.
    """
    from typer import style
    from .state import ctx

    use_color = not ctx.no_color
    lines = [f"Available Prompts ({len(prompts)})", ""]

    for prompt in prompts:
        # Title line: key - name (with color)
        title = f"{prompt.key} - {prompt.name}"
        if use_color:
            title = style(title, fg="bright_blue", bold=True)
        lines.append(title)

        # Description (indented)
        lines.append(f"  {prompt.description}")

        # Variables (simplified, with color)
        req_vars = ", ".join(prompt.required_variables)
        opt_vars = ", ".join(f"[{v}]" for v in prompt.optional_variables)
        all_vars = ", ".join(filter(None, [req_vars, opt_vars]))
        var_line = f"  Variables: {all_vars or '(none)'}"
        if use_color and all_vars:
            var_line = f"  Variables: {style(all_vars, fg='cyan')}"
        lines.append(var_line)

        # Metadata line (with color)
        model = prompt.default_model or "(no default)"
        tags = ", ".join(prompt.tags) if prompt.tags else "(no tags)"
        if use_color:
            model = style(model, fg="green")
            if prompt.tags:
                tags = style(tags, fg="yellow")
        lines.append(f"  Model: {model} | Tags: {tags}")

        lines.append("")  # Blank line between prompts

    return "\n".join(lines)


def format_human_friendly_error(error: Exception, suggestion: str | None = None) -> str:
    """Format error for human readability.

    Args:
        error: The exception that occurred.
        suggestion: Optional actionable suggestion for the user.

    Returns:
        Formatted error string with suggestion.
    """
    from typer import style
    from .state import ctx
    use_color = not ctx.no_color

    error_msg = f"Error: {str(error)}"
    if use_color:
        error_msg = style(error_msg, fg="red", bold=True)

    lines = [error_msg, ""]

    if suggestion:
        sugg_line = f"Suggestion: {suggestion}"
        if use_color:
            sugg_line = style(sugg_line, fg="yellow")
        lines.append(sugg_line)
        lines.append("")

    return "\n".join(lines)
```

#### 4.3 Update `run.py`

**Current behavior**: Always outputs JSON response (ADR-TG01 §4.7)

**Proposed**:

- **Human mode** (`not ctx.api`): Output only `result.text` directly to stdout
- **API mode** (`ctx.api`): Full JSON response with status, provenance, usage
- **Warnings/Diagnostics**: Go to stderr in BOTH modes (see §4.5)

```python
# After successful generation
if not ctx.api:
    # Human mode: just the content
    typer.echo(result.text)
else:
    # API mode: full JSON response
    payload = {
        "status": "succeeded",
        "result": {
            "text": result.text,
            "model": result.model,
            "usage": result.usage,
            "latency_ms": result.latency_ms
        },
        "provenance": {...}
    }
    typer.echo(render_output(payload, OutputFormat.json))
```

#### 4.4 Update Global CLI State

**Modify** `src/tnh_scholar/cli_tools/tnh_gen/state.py`:

```python
class CLIContext:
    def __init__(self):
        self.config_path: Path | None = None
        self.output_format: OutputFormat | None = None  # CHANGED: default to None
        self.api: bool = False  # ADD: Track API mode (machine-readable contract)
        self.quiet: bool = False
        self.no_color: bool = False  # ADD: Track color preference
```

**Modify** `src/tnh_scholar/cli_tools/tnh_gen/tnh_gen.py` (main entry point):

```python
@app.callback()
def main(
    config: Optional[Path] = typer.Option(None, "--config", help="Override config file path"),
    format: Optional[OutputFormat] = typer.Option(None, "--format", help="Output format (json|yaml|text|table)"),
    api: bool = typer.Option(False, "--api", help="Machine-readable API contract output (JSON)"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress non-essential output"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable colored output"),
):
    """Global options for all tnh-gen commands.

    Default behavior: human-friendly output optimized for interactive CLI use.
    Use --api for machine-readable JSON contract (for scripts and VS Code extension).

    Examples:
      # List prompts (human-friendly text)
      tnh-gen list

      # List prompts (machine-readable API contract)
      tnh-gen list --api

      # Run translation with variables
      tnh-gen run --prompt translate --input-file text.md \\
        --var source_lang=vi --var target_lang=en

      # Get API output with full metadata
      tnh-gen run --prompt daily --input-file notes.md --api

      # Human-friendly YAML output
      tnh-gen config show --format yaml
    """
    # Validate flag combinations
    if api and format in ('text', 'table'):
        raise typer.BadParameter("--api cannot be combined with --format text or table")

    ctx.config_path = config
    ctx.output_format = format
    ctx.api = api  # Store API mode flag
    ctx.quiet = quiet
    ctx.no_color = no_color
```

**Enhancement**: Improved help text with clear default behavior and examples. Added validation for incompatible flag combinations.

#### 4.5 Warnings and Diagnostic Output

**Decision**: Warnings and diagnostics go to stderr in BOTH human and API modes.

**Rationale**:

- Warnings are diagnostic information, not primary output
- Stderr allows scripts to capture clean stdout while monitoring warnings
- Consistent with Unix philosophy (data to stdout, diagnostics to stderr)
- Enables clean piping for both human and API modes

**Implementation**: All warning/info/trace messages use `typer.echo(message, err=True)` regardless of mode.

**Example**:

```bash
$ tnh-gen list > prompts.txt 2> warnings.log
# stdout → prompts.txt (clean human-friendly or API output)
# stderr → warnings.log (warnings about invalid frontmatter, trace IDs)
```

### 5. Programmatic Consumer Contract

**VS Code Extension** (ADR-VSC02):

- Extension will use `--api` flag for all CLI interactions
- ADR-VSC02 is still in **proposed** status, coordinated design
- `--api` is the machine-readable API contract mode
- Extension receives full metadata (prompts, config, errors) via `--api`
- Extension should parse stdout for JSON, stderr for diagnostics

**Scripts and Automation**:

- All programmatic consumers should use `--api` for stable JSON contract
- Optional: `--api --format yaml` for YAML serialization with full metadata
- Direct use of `--format json` without `--api` is **not recommended** (may give simplified output in future)

**Human-Friendly Formats**:

- `--format table` - tabular output (simplified)
- `--format yaml` - YAML output (simplified, human-editable)
- `--format text` - custom text format (default, most readable)
- Default (no flags) - command-specific text formatting

### 6. Examples (Before & After)

#### Scenario 1: Human using CLI directly

**Before (ADR-TG01)**:

```bash
$ tnh-gen list
{"prompts": [{"key": "daily", "name": "Daily Guidance", ...}], "count": 1, ...}
# JSON blob is hard to read
```

**After (ADR-TG01.1)**:

```bash
$ tnh-gen list
Available Prompts (1)

daily - Daily Guidance
  Daily guidance prompt for testing.
  Variables: audience, [location]
  Model: gpt-4o | Tags: guidance, study
# Easy to scan and understand
```

#### Scenario 2: VS Code extension

**ADR-VSC02 uses `--api` flag**:

```bash
$ tnh-gen list --api
{"prompts": [...], "count": 3, "sources": {...}}
# Extension uses --api for full machine-readable API contract

$ tnh-gen run --prompt translate --input-file text.md --var source_lang=vi --api
{
  "status": "succeeded",
  "result": {"text": "...", "model": "gpt-4o", ...},
  "provenance": {...}
}
# All extension CLI calls use --api for consistent contract
```

#### Scenario 3: Script parsing output

**Recommended approach**:

```bash
$ tnh-gen list --api | jq '.prompts[].key'
daily
translate
# Scripts use --api flag for stable JSON contract
```

**Alternative (YAML)**:

```bash
$ tnh-gen list --api --format yaml | yq '.prompts[].key'
daily
translate
# API mode supports YAML serialization too
```

---

## Consequences

### Positive

1. **Better Human UX**: CLI is now friendly for interactive use without JSON noise
2. **Clear Intent**: `--api` flag explicitly signals "I want machine-readable contract output"
3. **Semantic Clarity**: `--api` clearly indicates programmatic use, reserves `--verbose` for future human verbosity features
4. **Progressive Disclosure**: Simple cases simple (default), complex cases possible (`--api`)
5. **Consistent Pattern**: Same `--api` semantics apply across all commands (`list`, `run`, `config`, `version`, errors)
6. **Easier Onboarding**: New users can read prompts naturally without parsing JSON
7. **Color Support**: Optional colors improve scannability without breaking plain text output
8. **Better Help Text**: Examples in help make common usage patterns immediately discoverable
9. **Future-Proof**: Reserves `--verbose` for human-mode verbosity (streaming progress, extended diagnostics)

### Negative

1. **Breaking Change**: This redesigns the output contract, changing default behavior from JSON to human-friendly text
   - **Rationale**: ADR-VSC02 is still proposed, so this is the right time for breaking changes
   - **Mitigation**: Clear migration guide, explicit `--api` flag for programmatic consumers
2. **Two Output Modes**: Increased testing surface (human + API modes + color variants + format combinations)
   - **Mitigation**: Golden tests for both modes, validation of incompatible flag combinations
3. **Format Semantics Complexity**: `--format` behaves differently with/without `--api`
   - **Mitigation**: Clear help text, validation errors for invalid combinations (e.g., `--api --format text`)
4. **Color Compatibility**: Some terminals may not support ANSI color codes
   - **Mitigation**: `--no-color` flag disables colors, auto-detect non-TTY environments

### Neutral

- **Documentation Overhead**: Need to document both modes clearly
- **Code Complexity**: Additional formatter module, but well-isolated

---

## Alternatives Considered

### Option A: Keep `--verbose` for API Mode

```bash
tnh-gen list --verbose  # API mode
```

**Rejected**: Semantic confusion between "more data" and "different format". `--verbose` traditionally means "more human-readable detail" (e.g., `ls -v`, `git commit -v`), not "machine-readable contract".  Mixing these concepts creates ambiguity and prevents future use of `--verbose` for actual verbosity (streaming, extended human output).

### Option B: Keep JSON Default, Add `--human` Flag

```bash
tnh-gen list          # JSON (default)
tnh-gen list --human  # Human-friendly
```

**Rejected**: Optimizes for API use, not human use. Most CLI tools default to human-friendly output (e.g., `git log`, `ls`, `docker ps`). Forces interactive users to always add a flag.

### Option C: Default to Table Format

```bash
tnh-gen list          # Table (default)
tnh-gen list --format json  # API mode
```

**Rejected**: Table format lacks descriptions and is too constrained. Human-friendly text can include descriptions and multiline content. Also, `--format json` without `--api` doesn't clearly signal "full API contract".

### Option D: Separate Commands

```bash
tnh-gen list          # Human-friendly
tnh-gen api-list      # API mode
```

**Rejected**: Duplicates commands, breaks Unix conventions. Single command with explicit mode flags (`--api`) is cleaner and more discoverable.

---

## Integration with ADR-VSC02

Since ADR-VSC02 (VS Code Integration) is still in **proposed** status, we are designing the CLI contract and VS Code consumer together:

### VS Code Extension Requirements

1. **Use `--api` for all CLI calls**: Extension must use `--api` flag for stable machine-readable contract
2. **Parse stdout for JSON**: Extension parses stdout for JSON responses (prompts, results, errors)
3. **Monitor stderr for diagnostics**: Extension logs stderr for trace IDs, warnings, debug info
4. **Error handling**: Parse JSON error responses with `diagnostics` field (see §3.4)
5. **Full metadata access**: `--api` provides complete prompt metadata, provenance, usage stats
6. **Consistent contract**: All commands (`list`, `run`, `config`, `version`) use same `--api` semantics

### Example VS Code CLI Calls

```bash
# List prompts for UI dropdown
tnh-gen list --api

# Execute prompt on selected text
tnh-gen run --prompt <key> --input-file <temp> --var key=value --api

# Get configuration for settings UI
tnh-gen config show --api

# Check CLI version compatibility
tnh-gen version --api
```

### Changes Required to ADR-VSC02

ADR-VSC02 must be updated to:

1. Replace all `--format json` with `--api` flag in CLI invocation examples
2. Document stdout/stderr separation (JSON on stdout, diagnostics on stderr)
3. Update error handling to parse JSON error envelope from stdout (§3.4)
4. Note that human-friendly mode exists but extension never uses it
5. Add validation that `--api` is always included in CLI calls

---

## Testing Strategy

### Unit Tests

```python
def test_list_default_human_friendly(cli_runner):
    """Default list output is human-friendly text."""
    result = cli_runner.invoke(app, ['list'])
    assert result.exit_code == 0
    assert "Available Prompts" in result.stdout
    assert "Variables:" in result.stdout
    # Should NOT be JSON
    assert not result.stdout.startswith('{')

def test_list_api_json(cli_runner):
    """--api flag produces structured JSON contract."""
    result = cli_runner.invoke(app, ['list', '--api'])
    assert result.exit_code == 0
    output = json.loads(result.stdout)
    assert 'prompts' in output
    assert 'count' in output
    assert 'sources' in output

def test_api_with_yaml_format(cli_runner):
    """--api --format yaml produces full metadata as YAML."""
    result = cli_runner.invoke(app, ['list', '--api', '--format', 'yaml'])
    assert result.exit_code == 0
    output = yaml.safe_load(result.stdout)
    assert 'prompts' in output
    assert 'count' in output

def test_api_with_text_format_fails(cli_runner):
    """--api cannot be combined with --format text."""
    result = cli_runner.invoke(app, ['list', '--api', '--format', 'text'])
    assert result.exit_code != 0
    assert "cannot be combined" in result.stderr.lower()

def test_filtering_works_in_both_modes(cli_runner):
    """Tag filtering works identically in human and API modes."""
    # Human mode with filter
    result_human = cli_runner.invoke(app, ['list', '--tag', 'translation'])
    assert result_human.exit_code == 0
    assert "translate" in result_human.stdout.lower()

    # API mode with same filter
    result_api = cli_runner.invoke(app, ['list', '--tag', 'translation', '--api'])
    assert result_api.exit_code == 0
    output = json.loads(result_api.stdout)
    assert all('translation' in p.get('tags', []) for p in output['prompts'])

def test_error_format_human_friendly(cli_runner):
    """Errors are human-friendly in default mode."""
    result = cli_runner.invoke(app, ['run', '--prompt', 'nonexistent', '--input-file', 'test.md'])
    assert result.exit_code != 0
    assert "Error:" in result.stdout
    assert "Suggestion:" in result.stdout
    # Should NOT be JSON
    assert not result.stdout.startswith('{')
    # Trace ID should be in stderr
    assert "trace_id=" in result.stderr

def test_error_format_api(cli_runner):
    """Errors are JSON in API mode."""
    result = cli_runner.invoke(app, ['run', '--prompt', 'nonexistent', '--input-file', 'test.md', '--api'])
    assert result.exit_code != 0
    output = json.loads(result.stdout)
    assert output['status'] == 'failed'
    assert 'error' in output
    assert 'diagnostics' in output
    assert 'trace_id' in output
    # Trace ID also in stderr for correlation
    assert "trace_id=" in result.stderr

def test_color_disabled_with_flag(cli_runner):
    """--no-color disables ANSI color codes."""
    result = cli_runner.invoke(app, ['list', '--no-color'])
    assert result.exit_code == 0
    # Check for absence of ANSI escape codes
    assert '\033[' not in result.stdout

def test_warnings_go_to_stderr(cli_runner):
    """Warnings go to stderr in both modes."""
    # Setup: Create prompt with warnings
    result = cli_runner.invoke(app, ['list'])
    # Warnings should be in stderr, not stdout
    # (Actual assertion depends on test setup with invalid prompts)

def test_run_human_mode_text_only(cli_runner):
    """run command in human mode outputs only generated text."""
    result = cli_runner.invoke(app, ['run', '--prompt', 'test', '--input-file', 'test.md'])
    assert result.exit_code == 0
    # Should be plain text, not JSON
    assert not result.stdout.startswith('{')
    # Should NOT have status/provenance wrapper
    assert 'status' not in result.stdout
    assert 'provenance' not in result.stdout

def test_run_api_mode_full_response(cli_runner):
    """run command in API mode outputs full JSON response."""
    result = cli_runner.invoke(app, ['run', '--prompt', 'test', '--input-file', 'test.md', '--api'])
    assert result.exit_code == 0
    output = json.loads(result.stdout)
    assert output['status'] == 'succeeded'
    assert 'result' in output
    assert 'provenance' in output
    assert output['result']['text']  # Generated text is inside result
```

### Golden Tests

- Store expected human-friendly output for known prompts
- Store expected JSON output for API mode (`--api`)
- Validate both modes against golden files

### Integration Tests

```bash
# Human mode
tnh-gen list | grep "Available Prompts"

# API mode
tnh-gen list --api | jq -e '.prompts'

# VS Code compatibility (uses --api flag)
tnh-gen list --api | jq -e '.count'

# Config API mode
tnh-gen config show --api | jq -e '.config'

# Error handling in both modes
tnh-gen run --prompt nonexistent --input-file test.md 2>&1 | grep "Error:"
tnh-gen run --prompt nonexistent --input-file test.md --api 2>&1 | jq -e '.error'
```

---

## Future Enhancement Opportunities

While this ADR focuses on human-friendly defaults with the `--api` flag for machine-readable contract output, codebase exploration revealed additional UX improvements that could be addressed in future ADRs:

### ADR-TG01.2: Interactive Feedback (Medium Priority)

**Problem**: Long-running `run` commands provide no feedback during execution. Users can't tell if the command is stuck or processing.

**Proposed Solution**:

- Add progress indicators (spinner) for API calls
- Show model name and elapsed time during generation
- Implement streaming support (already has `--streaming` flag stub)

**Example**:

```bash
$ tnh-gen run --prompt translate --input-file large.md
Generating translation... ⠋ (gpt-4o, 3.2s)
[output appears]
```

**Scope**: Progress indicators, streaming output, real-time feedback.

### ADR-TG01.3: Smart Command Assistance (Lower Priority)

**Problem**: Users must know exact prompt keys. Typos result in cryptic "not found" errors without suggestions.

**Proposed Solution**:

- Fuzzy matching with "did you mean?" suggestions
- `--dry-run` flag to validate without API calls
- Pre-check validation with helpful error messages before making expensive API requests

**Example**:

```bash
$ tnh-gen run --prompt translat --input-file test.md
Error: Prompt 'translat' not found

Did you mean: translate?

$ tnh-gen run --prompt translate --input-file test.md --dry-run
✓ Prompt 'translate' found
✓ Input file readable (1.2 KB)
✗ Missing required variable: source_lang
✗ Missing required variable: target_lang

Fix: Add --var source_lang=vi --var target_lang=en
```

**Scope**: Fuzzy matching, validation pre-checks, dry-run mode, smart suggestions.

### ADR-TG03: Config Management UX (Lower Priority)

**Problem**: Configuration hierarchy is powerful but opaque. Users can't easily see where values come from or reset to defaults.

**Proposed Solution**:

- `config diff` - Show what changed from defaults
- `config reset [key]` - Reset specific key or entire config to defaults
- `config which <key>` - Show source of value (defaults/user/workspace/CLI)
- `config validate` - Check for errors/warnings in config files

**Example**:

```bash
$ tnh-gen config which default_model
default_model: gpt-4o-mini
Source: user config (~/.config/tnh-scholar/config.yaml:12)

$ tnh-gen config diff
Changed from defaults:
  prompt_catalog: /custom/path (workspace)
  default_model: gpt-4o-mini (user)

$ tnh-gen config reset default_model
Reset default_model to default value (gpt-4o)
```

**Scope**: Config introspection, reset capabilities, validation utilities.

---

## References

### Parent ADR

- [ADR-TG01: tnh-gen CLI Architecture](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md) - Core CLI design

### Related ADRs

- [ADR-VSC02: VS Code Integration](/architecture/ui-ux/vs-code-integration/adr-vsc02-tnh-gen-cli-implementation.md) - VS Code client integration (updated to use `--api` flag)
- [ADR-PT04: Prompt System Refactor](/architecture/prompt-system/adr/adr-pt04-prompt-system-refactor.md) - PromptMetadata schema

### External References

- [The Art of Command Line](https://github.com/jlevy/the-art-of-command-line) - CLI best practices
- [12 Factor CLI Apps](https://medium.com/@jdxcode/12-factor-cli-apps-dd3c227a0e46) - Design principles
- [clig.dev](https://clig.dev/) - Command line interface guidelines

---

## Changelog

### 2025-12-27: Refactored to use `--api` flag

**Breaking Change**: Replaced `--verbose` flag with `--api` flag for machine-readable contract output.

**Rationale**:

- `--verbose` mixed semantic concepts: "more data" vs "different format"
- Traditional Unix `--verbose` means "more human-readable detail", not "machine output"
- `--api` clearly signals programmatic/machine-readable contract
- Reserves `--verbose` for future human-mode verbosity features

**Changes Made**:

1. Renamed flag from `--verbose` to `--api` throughout ADR
2. Fixed config command API mode to output JSON (was YAML)
3. Clarified stdout/stderr separation for errors and diagnostics
4. Added validation: `--api` cannot combine with `--format text` or `--format table`
5. Updated ADR-VSC02 reference to reflect `--api` usage
6. Changed ADR status from "WIP" to "proposed"
7. Documented trace ID mapping and environment variable override
8. Added explicit breaking change acknowledgment in Consequences

**Issues Addressed**:

- Semantic confusion of `--verbose` flag (what vs how)
- Config format inconsistency (YAML in verbose mode)
- Error output channel ambiguity (stdout vs stderr)
- Human-friendly default logic bug (format defaulting to JSON)
- "No breaking changes" claim conflicted with actual design

---

**Approval Path**: User review → Implementation → Testing → Documentation → Merge
