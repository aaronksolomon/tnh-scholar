---
title: "ADR-TG01.1: Human-Friendly CLI Defaults"
description: "Default to human-readable output for CLI usage, with --verbose flag for API-style JSON"
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Sonnet 4.5"
status: proposed
created: "2025-12-23"
parent_adr: "adr-tg01-cli-architecture.md"
---
# ADR-TG01.1: Human-Friendly CLI Defaults

Extends [ADR-TG01](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md) to make tnh-gen CLI more human-friendly by default, while preserving API-style structured output for programmatic use via `--verbose` flag.

- **Filename**: `adr-tg01.1-human-friendly-defaults.md`
- **Heading**: `# ADR-TG01.1: Human-Friendly CLI Defaults`
- **Status**: Proposed
- **Date**: 2025-12-23
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
2. Parseable JSON/YAML
3. All fields including warnings, versions, sources
4. Consistent machine-readable format

### Requirements

1. **Default to human-friendly output** for direct CLI usage
2. **Preserve API mode** via `--verbose` flag for programmatic consumption
3. **Apply across commands** (`list`, `run`, etc.) consistently
4. **Maintain backward compatibility** with existing VS Code integration
5. **No breaking changes** to ADR-TG01 contract

---

## Decision

### 1. Default Output Mode: Human-Friendly

**When `--verbose` is NOT set**, default to simplified human-readable output:

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

#### `tnh-gen list --verbose` (API mode)

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

**Unchanged from ADR-TG01**: Full structured output with all metadata fields.

### 2. Flag Semantics

#### New Global Flag: `--verbose` / `-v`

```bash
--verbose, -v      # Enable API-style structured output (JSON default)
```

**Behavior**:
- **WITHOUT `--verbose`**: Human-friendly output (format auto-selected per command)
- **WITH `--verbose`**: API-style JSON output (full metadata, structured)

**Precedence rules**:
1. **Explicit `--format`**: Overrides everything (e.g., `--format yaml` gives YAML regardless of verbose)
2. **`--verbose` flag**: Triggers API mode (JSON with full metadata)
3. **Default**: Human-friendly mode (command-specific formatting)

**Examples**:
```bash
# Human-friendly (default)
tnh-gen list

# API mode (full JSON)
tnh-gen list --verbose
tnh-gen list -v

# Explicit format override
tnh-gen list --format yaml          # YAML, human-friendly subset
tnh-gen list --verbose --format yaml  # YAML, full API metadata

# Legacy table format still works
tnh-gen list --format table
```

### 3. Command-Specific Defaults

#### `tnh-gen list`

| Mode | Default Format | Content |
|------|----------------|---------|
| Human (default) | Custom text | Description, variables (simplified), model, tags |
| Verbose (`-v`) | JSON | Full metadata (all fields from ADR-TG01) |

#### `tnh-gen run`

| Mode | Default Format | Content |
|------|----------------|---------|
| Human (default) | Text output only | Just the generated text (no JSON wrapper) |
| Verbose (`-v`) | JSON | Full response with status, provenance, usage, latency |

**Example**:
```bash
# Human mode: just the generated content
$ tnh-gen run --prompt translate --input-file teaching.md --var source_lang=vi --var target_lang=en
[Generated translation text here...]

# Verbose mode: full structured response
$ tnh-gen run --prompt translate --input-file teaching.md --var source_lang=vi --var target_lang=en --verbose
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

| Mode | Default Format | Content |
|------|----------------|---------|
| Human (default) | YAML | Human-readable config (comments preserved) |
| Verbose (`-v`) | JSON | Full config with sources metadata |

### 4. Implementation Strategy

#### 4.1 Update `list.py`

**Current** (`list.py:96-127`):
- Always builds full JSON entries with all metadata
- Formats as JSON/YAML/table based on explicit `--format`

**Proposed**:
1. Check `ctx.verbose` flag first
2. If `not ctx.verbose` and `format is None`: use human-friendly text formatter
3. If `ctx.verbose` or explicit format: use current structured logic

```python
# Pseudocode
if not ctx.verbose and format is None:
    # Human-friendly mode
    output = format_human_friendly_list(prompts)
    typer.echo(output)
else:
    # API mode (current behavior)
    entries = [...full metadata...]
    fmt = format or ListOutputFormat.json
    typer.echo(render_output(payload, fmt))
```

#### 4.2 Add Human-Friendly Formatters

**New module**: `src/tnh_scholar/cli_tools/tnh_gen/output/human_formatter.py`

```python
def format_human_friendly_list(prompts: list[PromptMetadata]) -> str:
    """Format prompts for human readability.

    Args:
        prompts: List of prompt metadata objects.

    Returns:
        Formatted string with descriptions and simplified variables.
    """
    lines = [f"Available Prompts ({len(prompts)})", ""]

    for prompt in prompts:
        # Title line: key - name
        lines.append(f"{prompt.key} - {prompt.name}")

        # Description (indented)
        lines.append(f"  {prompt.description}")

        # Variables (simplified)
        req_vars = ", ".join(prompt.required_variables)
        opt_vars = ", ".join(f"[{v}]" for v in prompt.optional_variables)
        all_vars = ", ".join(filter(None, [req_vars, opt_vars]))
        lines.append(f"  Variables: {all_vars or '(none)'}")

        # Metadata line
        model = prompt.default_model or "(no default)"
        tags = ", ".join(prompt.tags) if prompt.tags else "(no tags)"
        lines.append(f"  Model: {model} | Tags: {tags}")

        lines.append("")  # Blank line between prompts

    return "\n".join(lines)
```

#### 4.3 Update `run.py`

**Current behavior**: Always outputs JSON response (ADR-TG01 §4.7)

**Proposed**:
- **Human mode** (`not verbose`): Output only `result.text` directly
- **Verbose mode**: Current JSON response with full metadata

```python
# After successful generation
if not ctx.verbose:
    # Human mode: just the content
    typer.echo(result.text)
else:
    # API mode: full JSON response
    payload = {
        "status": "succeeded",
        "result": {...},
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
        self.output_format: OutputFormat = OutputFormat.json
        self.verbose: bool = False  # ADD: Track verbose mode
        self.quiet: bool = False
```

**Modify** `src/tnh_scholar/cli_tools/tnh_gen/tnh_gen.py` (main entry point):

```python
@app.callback()
def main(
    config: Optional[Path] = typer.Option(None, "--config"),
    format: OutputFormat = typer.Option(OutputFormat.json, "--format"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="API-style structured output"),
    quiet: bool = typer.Option(False, "--quiet", "-q"),
):
    """Global options for all tnh-gen commands."""
    ctx.config_path = config
    ctx.output_format = format
    ctx.verbose = verbose  # Store in context
    ctx.quiet = quiet
```

### 5. Backward Compatibility

**VS Code Extension** (ADR-VSC02):
- Extension currently uses `tnh-gen list --format json` explicitly
- **No impact**: Explicit `--format` overrides verbose logic
- Extension continues to receive structured JSON as expected

**Scripts using JSON output**:
- Scripts that rely on default JSON output should add `--verbose` flag
- Alternatively, use explicit `--format json`
- **Migration period**: Add deprecation notice in v0.2.x, enforce in v0.3.0

**Table format**:
- `--format table` continues to work exactly as before
- Human-friendly text format is a new default, doesn't replace table

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

**Before & After (unchanged)**:
```bash
$ tnh-gen list --format json
{"prompts": [...], "count": 3, "sources": {...}}
# Extension explicitly requests JSON, gets structured output
```

#### Scenario 3: Script parsing output

**Before (implicit JSON)**:
```bash
$ tnh-gen list | jq '.prompts[].key'
daily
translate
```

**After (add --verbose)**:
```bash
$ tnh-gen list --verbose | jq '.prompts[].key'
daily
translate
# Scripts add --verbose flag for API mode
```

---

## Consequences

### Positive

1. **Better Human UX**: CLI is now friendly for interactive use without JSON noise
2. **Clear Intent**: `--verbose` flag explicitly signals "I want full API output"
3. **Progressive Disclosure**: Simple cases simple (default), complex cases possible (verbose)
4. **Backward Compatible**: VS Code and scripts using `--format json` unaffected
5. **Consistent Pattern**: Same verbose semantics apply across all commands (`list`, `run`, `config`)
6. **Easier Onboarding**: New users can read prompts naturally without parsing JSON

### Negative

1. **Breaking Change for Scripts**: Scripts relying on default JSON output must add `--verbose`
   - **Mitigation**: Document in CHANGELOG, provide migration guide
2. **Two Output Modes**: Increased testing surface (human + API modes)
   - **Mitigation**: Golden tests for both modes
3. **Format Ambiguity**: Users might be confused when `--format` overrides `--verbose`
   - **Mitigation**: Clear help text and examples in docs

### Neutral

- **Documentation Overhead**: Need to document both modes clearly
- **Code Complexity**: Additional formatter module, but well-isolated

---

## Alternatives Considered

### Option A: Keep JSON Default, Add `--human` Flag

```bash
tnh-gen list          # JSON (default)
tnh-gen list --human  # Human-friendly
```

**Rejected**: Optimizes for API use, not human use. Most CLI tools default to human-friendly output (e.g., `git log`, `ls`, `docker ps`).

### Option B: Default to Table Format

```bash
tnh-gen list          # Table (default)
tnh-gen list --format json  # API mode
```

**Rejected**: Table format lacks descriptions and is too constrained. Human-friendly text can include descriptions and multiline content.

### Option C: Separate Commands

```bash
tnh-gen list          # Human-friendly
tnh-gen list-json     # API mode
```

**Rejected**: Duplicates commands, breaks Unix conventions. Single command with flags is cleaner.

---

## Migration Guide

### For Direct CLI Users

**No action required**. You'll automatically get better, more readable output.

### For Scripts and Automation

**Add `--verbose` flag** to get structured JSON output:

```bash
# Before
tnh-gen list | jq '.prompts[].key'

# After
tnh-gen list --verbose | jq '.prompts[].key'
```

**Alternative**: Use explicit `--format json`:

```bash
tnh-gen list --format json | jq '.prompts[].key'
```

### For VS Code Extension (ADR-VSC02)

**No changes required**. Extension uses `--format json` explicitly, which overrides default behavior.

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

def test_list_verbose_json(cli_runner):
    """Verbose flag produces structured JSON."""
    result = cli_runner.invoke(app, ['list', '--verbose'])
    assert result.exit_code == 0
    output = json.loads(result.stdout)
    assert 'prompts' in output
    assert 'count' in output

def test_explicit_format_overrides_verbose(cli_runner):
    """Explicit --format overrides verbose logic."""
    result = cli_runner.invoke(app, ['list', '--format', 'yaml'])
    assert result.exit_code == 0
    # Should be YAML, not JSON or text
    assert '---' in result.stdout or 'prompts:' in result.stdout
```

### Golden Tests

- Store expected human-friendly output for known prompts
- Store expected JSON output for verbose mode
- Validate both modes against golden files

### Integration Tests

```bash
# Human mode
tnh-gen list | grep "Available Prompts"

# API mode
tnh-gen list --verbose | jq -e '.prompts'

# VS Code compatibility
tnh-gen list --format json | jq -e '.count'
```

---

## Open Questions

1. **Should `run` command default to text or JSON?**
   - Proposal: Text (just the generated content) for human mode
   - Verbose mode preserves full JSON response with provenance

2. **Should warnings still go to stderr in human mode?**
   - Proposal: Yes, keep warnings on stderr in both modes

3. **Should human-friendly mode support filtering/searching?**
   - Proposal: Yes, `--tag` and `--search` work the same in both modes

---

## References

### Parent ADR

- [ADR-TG01: tnh-gen CLI Architecture](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md) - Core CLI design

### Related ADRs

- [ADR-VSC02: VS Code Integration](/architecture/ui-ux/vs-code-integration/adr-vsc02-tnh-gen-cli-implementation.md) - VS Code client integration
- [ADR-PT04: Prompt System Refactor](/architecture/prompt-system/adr/adr-pt04-prompt-system-refactor.md) - PromptMetadata schema

### External References

- [The Art of Command Line](https://github.com/jlevy/the-art-of-command-line) - CLI best practices
- [12 Factor CLI Apps](https://medium.com/@jdxcode/12-factor-cli-apps-dd3c227a0e46) - Design principles
- [clig.dev](https://clig.dev/) - Command line interface guidelines

---

**Approval Path**: User review → Implementation → Testing → Documentation → Merge
