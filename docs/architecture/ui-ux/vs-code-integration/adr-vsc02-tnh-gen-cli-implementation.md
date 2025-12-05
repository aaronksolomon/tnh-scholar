# ADR-VSC02: `tnh-gen` CLI Implementation

**Status:** Proposed
**Author:** Aaron Solomon
**Date:** 2025-01-28
**Tags:** implementation, cli, genai, architecture
**Related ADRs:** ADR-VSC01 (VS Code Integration Strategy), GenAI Service Strategy, UI/UX Strategy

---

## 1. Context

ADR-VSC01 established that the VS Code extension will communicate with TNH-Scholar via a unified CLI tool named `tnh-gen`. This ADR defines the **detailed implementation** of that CLI tool.

### **1.1 Requirements from ADR-VSC01**

The CLI must:

1. **Wrap GenAI Service**: Expose GenAI Service capabilities via command-line interface
2. **Support flexible variable passing**: Both JSON file and inline parameter styles
3. **Provide rich metadata**: Enable prompt discovery with human-readable information
4. **Output structured data**: JSON-formatted responses for programmatic consumption
5. **Handle errors gracefully**: Clear exit codes and error messages
6. **Replace `tnh-fab`**: Consolidate scattered CLI tools into unified interface

### **1.2 Design Principles**

1. **GenAI Service parity**: Match the GenAI Service's rich domain model as closely as possible
2. **Composability**: CLI should be usable standalone, from scripts, and from VS Code extension
3. **Progressive disclosure**: Simple cases should be simple; complex cases should be possible
4. **Structured I/O**: Consistent JSON output for programmatic consumption
5. **Clear errors**: Map GenAI Service errors to appropriate exit codes and messages

---

## 2. Decision

### **2.1 CLI Tool Name and Entry Point**

**Tool Name:** `tnh-gen`

**Poetry Configuration:**

```toml
[tool.poetry.scripts]
tnh-gen = "tnh_scholar.cli_tools.tnh_gen.tnh_gen:main"
```

**Installation:**

```bash
poetry install
tnh-gen --version  # Should work after installation
```

---

## 3. Command Structure

### **3.1 Top-Level Commands**

```bash
tnh-gen list       # List available prompts
tnh-gen run        # Execute a prompt
tnh-gen config     # Manage configuration
tnh-gen version    # Show version info
tnh-gen help       # Show help
```

### **3.2 Global Flags**

```bash
--config <path>    # Override config file location
--format <format>  # Output format (json, yaml, text)
--verbose, -v      # Verbose logging
--quiet, -q        # Suppress non-error output
--no-color         # Disable colored output
```

---

## 4. Command: `tnh-gen list`

Lists all available prompts with metadata.

### **4.1 Signature**

```bash
tnh-gen list [OPTIONS]
```

### **4.2 Options**

```bash
--format <format>     # Output format: json (default), yaml, table
--tag <tag>           # Filter by tag (can be repeated)
--search <query>      # Search in names/descriptions
--keys-only           # Output only prompt keys (one per line)
```

### **4.3 Output Format (JSON)**

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

### **4.4 Output Format (Table)**

```text
KEY         NAME                               TAGS                  MODEL
translate   Vietnamese-English Translation     translation, dharma   gpt-4o
summarize   Summarize Teaching                 summarization         gpt-4o-mini
```

### **4.5 Examples**

```bash
# List all prompts as JSON
tnh-gen list --format json

# List prompts with "translation" tag
tnh-gen list --tag translation

# Search for summarization prompts
tnh-gen list --search summarize

# Get just the keys
tnh-gen list --keys-only
```

### **4.6 Implementation Notes**

- Calls `PromptsAdapter.list_all()` to get all prompts
- For each prompt, calls `PromptsAdapter.introspect(prompt_ref)` to get metadata
- Requires ADR-VSC03 (PromptCatalog Metadata Schema) to be implemented first

---

## 5. Command: `tnh-gen run`

Executes a prompt pattern with variable substitution.

### **5.1 Signature**

```bash
tnh-gen run --prompt <key> [OPTIONS]
```

### **5.2 Required Options**

```bash
--prompt <key>         # Prompt key to execute
--input-file <path>    # Input file (content becomes input_text variable)
```

### **5.3 Variable Passing Options**

**Style 1: JSON file** (preferred for complex variables)

```bash
--vars <path>          # JSON file with variable definitions
```

**Style 2: Inline parameters** (convenient for simple cases)

```bash
--var <key>=<value>    # Variable assignment (can be repeated)
```

### **5.4 Model and Parameter Overrides**

```bash
--model <model_name>       # Override default model
--intent <intent>          # Routing hint (translation, summarization, etc.)
--max-tokens <int>         # Max output tokens
--temperature <float>      # Model temperature (0.0-2.0)
--top-p <float>            # Nucleus sampling parameter
```

### **5.5 Output Options**

```bash
--output-file <path>       # Write output to file
--format <format>          # Output format: json (default), text
--no-provenance            # Omit provenance markers in output
--streaming                # Enable streaming output (future)
```

### **5.6 Variable Injection Strategy**

Variables are merged in this precedence order (highest to lowest):

1. **Inline `--var` parameters**
2. **JSON file via `--vars`**
3. **Input file content** (auto-injected as `input_text`)

**Example:**

```bash
tnh-gen run --prompt translate \
  --input-file teaching.md \
  --var source_lang=vi \
  --var target_lang=en \
  --var context="Dharma talk" \
  --output-file teaching.translate.md
```

**Variable resolution:**

```json
{
  "input_text": "<contents of teaching.md>",
  "source_lang": "vi",
  "target_lang": "en",
  "context": "Dharma talk"
}
```

### **5.7 Output Format (Success)**

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
    "pattern_id": "translate",
    "pattern_fingerprint": "sha256:abc123...",
    "pattern_version": "1.0",
    "started_at": "2025-01-28T10:30:00Z",
    "completed_at": "2025-01-28T10:30:03Z",
    "schema_version": "1.0"
  }
}
```

### **5.8 Output Format (Error)**

Exit code: `1-4` (see section 6)

```json
{
  "status": "failed",
  "error": "PolicyError: Budget exceeded (estimated $0.15, max $0.10)",
  "diagnostics": {
    "error_type": "PolicyError",
    "error_code": "BUDGET_EXCEEDED",
    "estimated_cost": 0.15,
    "max_cost": 0.10,
    "suggestion": "Increase max_dollars in config or reduce input size"
  },
  "correlation_id": "01HQXYZ123ABC"
}
```

### **5.9 File Output Handling**

When `--output-file` is specified:

1. Write result text to file
2. Prepend provenance markers (unless `--no-provenance`)
3. Use appropriate file format (markdown, JSON, etc.)
4. Print success message to stderr
5. Print JSON response to stdout (for VS Code parsing)

**Provenance Marker Format:**

```markdown
<!--
TNH-Scholar Generated Content
Pattern: translate (v1.0)
Model: gpt-4o
Fingerprint: sha256:abc123...
Correlation ID: 01HQXYZ123ABC
Generated: 2025-01-28T10:30:03Z
-->

[Generated content follows...]
```

### **5.10 Examples**

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

## 6. Error Handling and Exit Codes

### **6.1 Exit Code Taxonomy**

| Exit Code | Error Type       | Description                                    |
|-----------|------------------|------------------------------------------------|
| `0`       | Success          | Operation completed successfully               |
| `1`       | Policy Error     | Budget exceeded, size limits, validation failed|
| `2`       | Transport Error  | API failure, timeout, network issues           |
| `3`       | Provider Error   | Model unavailable, rate limit, auth failure    |
| `4`       | Format Error     | JSON parse failure, schema validation failed   |
| `5`       | Input Error      | Invalid arguments, missing required variables  |

### **6.2 Error Message Format**

All errors are output as JSON to stdout:

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

### **6.3 Mapping GenAI Service Errors to Exit Codes**

```python
# Error mapping
ERROR_CODE_MAP = {
    PolicyError: 1,
    TransportError: 2,
    ProviderError: 3,
    FormatError: 4,
    ValueError: 5,
    KeyError: 5,
}
```

### **6.4 Example Error Messages**

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
  }
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
  }
}
```

---

## 7. Command: `tnh-gen config`

Manage configuration settings.

### **7.1 Subcommands**

```bash
tnh-gen config show       # Display current configuration
tnh-gen config get <key>  # Get specific config value
tnh-gen config set <key> <value>  # Set config value
tnh-gen config list       # List all config keys
```

### **7.2 Configuration Sources and Precedence**

Configuration is loaded in this order (highest to lowest precedence):

1. CLI flags (e.g., `--model gpt-4o`)
2. Workspace config (`.vscode/tnh-scholar.json`)
3. User config (`~/.config/tnh-scholar/config.json`)
4. Environment variables (`TNH_GENAI_MODEL`, `OPENAI_API_KEY`)
5. Defaults (defined in GenAI Service)

### **7.3 Configuration Schema**

```json
{
  "prompt_catalog_dir": "/path/to/prompts",
  "default_model": "gpt-4o-mini",
  "max_dollars": 0.10,
  "max_input_chars": 50000,
  "default_temperature": 0.2,
  "api_key": "$OPENAI_API_KEY",  // Can reference env vars
  "cli_path": null  // Override CLI location for VS Code
}
```

### **7.4 Examples**

```bash
# Show all config
tnh-gen config show --format json

# Get specific value
tnh-gen config get default_model

# Set value (writes to user config)
tnh-gen config set max_dollars 0.25

# Set workspace-level config
tnh-gen config set --workspace prompt_catalog_dir ./prompts
```

**Note:** See ADR-VSC04 for detailed configuration discovery and management strategy.

---

## 8. Command: `tnh-gen version`

Display version information.

### **8.1 Output Format**

```json
{
  "tnh_scholar": "0.1.3",
  "tnh_gen": "0.1.0",
  "python": "3.12.1",
  "platform": "darwin",
  "genai_service_version": "1.0.0"
}
```

---

## 9. Implementation Architecture

### **9.1 Module Structure**

```
src/tnh_scholar/cli_tools/tnh_gen/
├── __init__.py
├── tnh_gen.py           # Main entry point, CLI argument parsing
├── commands/
│   ├── __init__.py
│   ├── list.py          # tnh-gen list implementation
│   ├── run.py           # tnh-gen run implementation
│   ├── config.py        # tnh-gen config implementation
│   └── version.py       # tnh-gen version implementation
├── output/
│   ├── __init__.py
│   ├── formatter.py     # JSON/YAML/table output formatting
│   └── provenance.py    # Provenance marker generation
├── errors.py            # Error handling and exit code mapping
└── config_loader.py     # Configuration discovery and loading
```

### **9.2 CLI Framework**

Use **Click** for argument parsing (already a dependency):

```python
# tnh_gen.py
import click
from tnh_scholar.cli_tools.tnh_gen.commands import list_cmd, run_cmd, config_cmd

@click.group()
@click.version_option()
@click.option('--config', type=click.Path(), help='Config file path')
@click.option('--format', type=click.Choice(['json', 'yaml', 'text']), default='json')
@click.option('--verbose', '-v', is_flag=True)
@click.pass_context
def cli(ctx, config, format, verbose):
    """TNH-Gen: Unified CLI for TNH Scholar GenAI operations"""
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config
    ctx.obj['format'] = format
    ctx.obj['verbose'] = verbose

cli.add_command(list_cmd.list_prompts, name='list')
cli.add_command(run_cmd.run_prompt, name='run')
cli.add_command(config_cmd.config, name='config')

def main():
    cli(obj={})
```

### **9.3 Integration with GenAI Service**

```python
# commands/run.py
from tnh_scholar.gen_ai_service import GenAIService, RenderRequest
from tnh_scholar.cli_tools.tnh_gen.errors import map_error_to_exit_code

def run_prompt(ctx, prompt, input_file, vars, var, model, output_file, **kwargs):
    try:
        # Load configuration
        config = load_config(ctx.obj['config_path'])

        # Initialize GenAI Service
        service = GenAIService(settings=config)

        # Build variable dict
        variables = build_variables(input_file, vars, var)

        # Create request
        request = RenderRequest(
            prompt_key=prompt,
            variables=variables,
            model=model,
            intent=kwargs.get('intent'),
            # ... other params
        )

        # Execute
        result = service.generate(request)

        # Handle output
        if output_file:
            write_output_file(output_file, result, kwargs.get('no_provenance'))

        # Print JSON response
        print_json(result.model_dump())

        sys.exit(0)

    except Exception as e:
        error_response = format_error(e)
        print_json(error_response)
        sys.exit(map_error_to_exit_code(e))
```

---

## 10. Migration from `tnh-fab`

### **10.1 Deprecation Strategy**

1. **Phase 1 (v0.1.0)**: Introduce `tnh-gen`, keep `tnh-fab` functional
2. **Phase 2 (v0.2.0)**: Add deprecation warnings to `tnh-fab`
3. **Phase 3 (v0.3.0)**: Remove `tnh-fab` from Poetry scripts

### **10.2 Feature Parity**

Map existing `tnh-fab` commands to `tnh-gen`:

| `tnh-fab` Command | `tnh-gen` Equivalent |
|-------------------|----------------------|
| `tnh-fab run <pattern>` | `tnh-gen run --prompt <pattern>` |
| (no equivalent) | `tnh-gen list` (new) |
| (no equivalent) | `tnh-gen config` (new) |

### **10.3 Migration Guide**

Provide migration guide showing side-by-side examples:

```bash
# Old (tnh-fab)
tnh-fab run translate --input teaching.md --source vi --target en

# New (tnh-gen)
tnh-gen run --prompt translate \
  --input-file teaching.md \
  --var source_lang=vi \
  --var target_lang=en
```

---

## 11. Testing Strategy

### **11.1 Unit Tests**

```python
# tests/cli_tools/tnh_gen/test_run.py
def test_run_with_inline_vars():
    result = runner.invoke(cli, [
        'run',
        '--prompt', 'translate',
        '--input-file', 'test.md',
        '--var', 'source_lang=vi',
        '--var', 'target_lang=en'
    ])

    assert result.exit_code == 0
    output = json.loads(result.output)
    assert output['status'] == 'succeeded'
```

### **11.2 Integration Tests**

```python
def test_run_with_real_genai_service():
    """Test against live GenAI Service (requires API key)"""
    # Mark with pytest.mark.integration
    # Run only when RUN_INTEGRATION_TESTS=1
```

### **11.3 Golden Tests**

- Store expected JSON outputs for known prompts
- Validate output schema against golden files
- Ensure backward compatibility

---

## 12. Documentation Requirements

### **12.1 CLI Reference**

Auto-generate from Click help strings:

```bash
tnh-gen --help > docs/cli/tnh-gen.md
```

### **12.2 User Guide**

- Getting Started guide
- Common workflows and examples
- Variable passing strategies
- Error troubleshooting

### **12.3 Migration Guide**

- `tnh-fab` → `tnh-gen` migration instructions
- Breaking changes and workarounds

---

## 13. Acceptance Criteria

- [ ] `tnh-gen list --format json` returns prompt metadata
- [ ] `tnh-gen run` supports JSON file variable passing via `--vars`
- [ ] `tnh-gen run` supports inline `--var` parameter passing
- [ ] `tnh-gen run` injects `--input-file` content as `input_text` variable
- [ ] CLI outputs structured JSON on success and failure
- [ ] CLI exits with appropriate error codes (0-5)
- [ ] CLI respects configuration precedence (flags > workspace > user > env)
- [ ] `tnh-gen` is installable via `poetry install`
- [ ] Error messages include actionable suggestions
- [ ] Provenance markers are prepended to output files
- [ ] VS Code extension can parse CLI output successfully

---

## 14. Open Questions

1. **Streaming output**: How should `--streaming` work? Line-by-line? Token-by-token?
2. **Batch operations**: Should `tnh-gen run` support multiple input files at once?
3. **Dry-run mode**: Should we add `--dry-run` to preview requests without calling API?
4. **Caching**: Should CLI cache `list` results locally? If so, for how long?

---

## 15. Future Enhancements (Post-v0.1.0)

- [ ] `tnh-gen validate <prompt-file>` - Validate prompt syntax
- [ ] `tnh-gen inspect <prompt-key>` - Show detailed prompt info
- [ ] `tnh-gen batch <file-list>` - Batch processing
- [ ] `tnh-gen diff <file1> <file2>` - Compare outputs
- [ ] Shell completion scripts (bash, zsh, fish)
- [ ] `tnh-gen init` - Initialize new project with config template

---

## 16. References

- ADR-VSC01: VS Code Integration Strategy
- ADR-VSC03: PromptCatalog Metadata Schema
- ADR-VSC04: Configuration Discovery & Management
- GenAI Service Strategy
- Click Documentation: https://click.palletsprojects.com/
