---
title: "ADR-TG02: TNH-Gen CLI Prompt System Integration"
description: "Integration pattern for tnh-gen CLI with prompt system via PromptsAdapter"
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Sonnet 4.5"
status: draft
created: "2025-12-07"
---

# ADR-TG02: TNH-Gen CLI Prompt System Integration

This ADR defines how the `tnh-gen` CLI integrates with the prompt system (ADR-PT04) through the `PromptsAdapter`, establishing variable precedence rules and command implementation patterns.

- **Status**: Draft
- **Date**: 2025-12-07
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, Claude Sonnet 4.5

## Context

The `tnh-gen` CLI must bridge user input (files, variables, flags) to the prompt system while maintaining clean separation of concerns. Key requirements include:

1. **Variable Precedence**: CLI flags must override file-based variables, which override defaults
2. **Prompt Discovery**: Users need to list and search available prompts without exposing internal catalog structure
3. **Transport Isolation**: CLI layer should not depend on prompt storage implementation (git, filesystem, etc.)
4. **VS Code Integration**: Command outputs must be JSON-formatted for programmatic consumption
5. **Consistency**: Variable handling must align with prompt system's rendering policy (ADR-PT04 §5)

The `PromptsAdapter` (defined in ADR-PT04 §8.1) provides the contract boundary between CLI and prompt system, offering `list_all()`, `introspect()`, and `render()` methods.

## Decision

### 1. CLI Variable Precedence Model

The CLI collects variables from three sources with clear precedence:

```python
# In tnh-gen CLI implementation (commands/run.py):
from tnh_scholar.prompt_system.domain.models import RenderParams
from tnh_scholar.gen_ai_service.models.domain import RenderRequest

def run_prompt(prompt_key: str, input_file: Path, vars_file: Path, var: list[str]):
    """Execute a prompt with CLI-provided variables."""

    # 1. Build variables dict with CLI precedence (lowest to highest)
    variables = {}

    # Lowest precedence: input file content (auto-injected as input_text)
    if input_file:
        variables["input_text"] = input_file.read_text()

    # Medium precedence: JSON vars file (--vars)
    if vars_file:
        variables.update(json.loads(vars_file.read_text()))

    # Highest precedence: inline --var parameters
    for v in var:
        k, val = v.split('=', 1)
        variables[k] = val

    # 2. Build RenderParams (feeds into prompt_system's caller_context)
    # This becomes the highest precedence in PromptRenderPolicy
    params = RenderParams(
        variables=variables,
        strict_undefined=True
    )

    # 3. Call PromptsAdapter
    adapter = PromptsAdapter(catalog, renderer, validator)
    rendered, fingerprint = adapter.render(
        RenderRequest(
            instruction_key=prompt_key,
            variables=variables,
            user_input=variables.get("input_text", "")
        )
    )

    return rendered, fingerprint
```

**Precedence Alignment:**

| CLI Layer (ADR-TG02) | Prompt System Layer (ADR-PT04) |
|----------------------|-------------------------------|
| `--var` inline params | `caller_context` (highest) |
| `--vars` JSON file | `caller_context` (highest) |
| `--input-file` content | `caller_context` (highest) |
| (not applicable) | `frontmatter_defaults` (medium) |
| (not applicable) | `settings_defaults` (lowest) |

All CLI-provided variables merge into a single `variables` dict that becomes `caller_context` in the prompt system's precedence order.

### 2. List Command Implementation

The `list` command uses `PromptsAdapter.list_all()` for prompt discovery:

```python
# In tnh-gen CLI implementation (commands/list.py):
from tnh_scholar.gen_ai_service.pattern_catalog.adapters.prompts_adapter import PromptsAdapter

def list_prompts(tag: str | None = None, search: str | None = None):
    """List all available prompts with optional filtering."""

    # Initialize adapter
    adapter = PromptsAdapter(catalog, renderer, validator)

    # Get all prompts via new list_all() method
    all_prompts = adapter.list_all()

    # Apply filters
    filtered = [
        p for p in all_prompts
        if (not tag or tag in p.tags)
        and (not search or search.lower() in p.name.lower()
             or search.lower() in p.description.lower())
    ]

    # Format output for CLI/VS Code consumption
    return {
        "prompts": [
            {
                "key": p.key,
                "name": p.name,
                "description": p.description,
                "tags": p.tags,
                "required_variables": p.required_variables,
                "optional_variables": p.optional_variables,
                "default_model": p.default_model,
                "output_mode": p.output_mode,
                "version": p.version
            }
            for p in filtered
        ],
        "count": len(filtered)
    }
```

**Design Note**: The `list_all()` and `introspect()` methods added to `PromptsAdapter` enable prompt discoverability without exposing internal prompt system implementation to the CLI layer. This maintains clean separation of concerns.

### 3. PromptsAdapter Dependency Injection

The CLI uses dependency injection to configure the `PromptsAdapter`:

```python
# In tnh-gen CLI initialization (cli.py):
from tnh_scholar.prompt_system.adapters.git_catalog_adapter import GitPromptCatalog
from tnh_scholar.prompt_system.service.renderer import PromptRenderer
from tnh_scholar.prompt_system.service.validator import PromptValidator
from tnh_scholar.gen_ai_service.pattern_catalog.adapters.prompts_adapter import PromptsAdapter
from tnh_scholar.gen_ai_service.services.genai_service import GenAIService

def initialize_app() -> tuple[PromptsAdapter, GenAIService]:
    """Initialize application dependencies."""

    # 1. Configure prompt catalog
    catalog_config = PromptCatalogConfig.from_env()
    catalog = GitPromptCatalog.from_config(catalog_config)

    # 2. Configure renderer and validator
    render_policy = PromptRenderPolicy.from_config(catalog_config.render_policy)
    renderer = PromptRenderer(render_policy)
    validator = PromptValidator()

    # 3. Build PromptsAdapter
    prompts_adapter = PromptsAdapter(
        catalog=catalog,
        renderer=renderer,
        validator=validator
    )

    # 4. Configure GenAIService
    genai_service = GenAIService.from_config(GenAIConfig.from_env())

    return prompts_adapter, genai_service
```

### 4. Error Handling Alignment

CLI error codes (ADR-TG01 §5) map to prompt system exceptions:

| Prompt System Exception | CLI Exit Code | Error Type |
|------------------------|--------------|------------|
| `PromptNotFoundError` | `5` | Input Error |
| `VariableValidationError` | `5` | Input Error |
| `RenderError` (template syntax) | `4` | Format Error |
| `ValidationError` (schema) | `1` | Policy Error |
| `GitTransportError` | `2` | Transport Error |

### 5. Configuration Integration

The CLI respects prompt system configuration via hierarchical precedence:

```yaml
# ~/.config/tnh-scholar/tnh-gen.yaml
prompt_system:
  repository_path: /path/to/prompts
  enable_git_refresh: true
  validation_on_load: true
  cache_ttl_s: 3600
  render_policy:
    strict_undefined: true
    max_output_size_kb: 100
```

CLI flags override config file values (see ADR-TG01 §4 for precedence).

## Consequences

### Positive

- **Clean Separation**: CLI layer depends only on `PromptsAdapter` contract, not prompt system internals
- **Consistent Precedence**: Variable handling aligns across CLI and prompt system layers
- **Discoverability**: `list_all()` and `introspect()` enable rich prompt exploration without leaking implementation
- **Testability**: Adapter contract allows mocking entire prompt system in CLI tests
- **VS Code Integration**: JSON output format enables seamless editor consumption

### Negative

- **Adapter Maintenance**: Changes to prompt system require coordinated updates to `PromptsAdapter`
- **Variable Complexity**: Three-level CLI precedence (file → vars → flags) may confuse users unfamiliar with override patterns
- **Validation Boundaries**: Prompt variable validation happens after CLI parsing, delaying error feedback

### Risks

- **Breaking Changes**: Prompt system refactors (e.g., new metadata fields) may break CLI expectations
- **Performance**: Listing all prompts via `list_all()` may be slow for large catalogs (mitigated by caching in ADR-PT04 §6)

## Alternatives Considered

### Alternative 1: Direct Prompt System Access

**Approach**: CLI directly imports and uses `PromptCatalog`, `PromptRenderer`, etc.

**Rejected**: Violates object-service architecture (ADR-OS01). CLI should not depend on domain internals.

### Alternative 2: Separate CLI Variable Layer

**Approach**: Create `CLIVariableResolver` to handle precedence, separate from `RenderParams`.

**Rejected**: Adds unnecessary abstraction. Merging variables into `caller_context` is simpler and aligns with existing prompt system precedence.

### Alternative 3: GraphQL API Between CLI and Prompt System

**Approach**: Expose prompt system via GraphQL API that CLI queries.

**Rejected**: Overengineering for single-process CLI. Useful for future web UI but premature for MVP.

## Open Questions

1. **Lazy Loading**: Should `list_all()` return full metadata or just keys/names for performance? (See ADR-PT04 §8.1)
2. **Variable Validation Feedback**: Should CLI pre-validate variables against prompt schema before calling `render()`?
3. **Cache Control**: Should CLI expose `--no-cache` flag to bypass prompt caching?

## References

### Related ADRs

- **[ADR-TG01: CLI Architecture](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md)** - Command structure, error codes, configuration
- **[ADR-PT04: Prompt System Refactor](/architecture/prompt-system/adr/adr-pt04-prompt-system-refactor.md)** - Prompt system architecture, `PromptsAdapter` contract
- **[ADR-AT03: AI Text Processing Refactor](/architecture/ai-text-processing/adr/adr-at03-object-service-refactor.md)** - `ai_text_processing` module refactor
- **[ADR-VSC02: VS Code Extension](/architecture/ui-ux/vs-code-integration/adr-vsc02-tnh-gen-cli-implementation.md)** - VS Code integration strategy

### External Resources

- [Typer Documentation](https://typer.tiangolo.com/)
- [Jinja2 Template Syntax](https://jinja.palletsprojects.com/)
- [Pydantic Validation](https://docs.pydantic.dev/)

---

*This ADR implements prompt system integration patterns from ADR-PT04 §8.2.*
