---
title: "ADR-A14: File-Based Registry System for Provider Metadata"
description: "Establishes a JSONC-based registry system for model capabilities, pricing, and provider metadata with auto-update mechanisms, aligned with VS Code's native configuration format."
owner: "aaronksolomon"
author: "Aaron Solomon, Anthropic Claude Sonnet 4.5"
status: wip
created: "2025-12-10"
---
# ADR-A14: File-Based Registry System for Provider Metadata

Establishes a human-editable, file-based registry for model capabilities, pricing tables, and provider metadata using **JSON with Comments (JSONC)** format to align with VS Code's native configuration system.

- **Filename**: `adr-a14-file-based-registry-system.md`
- **Heading**: `# ADR-A14: File-Based Registry System for Provider Metadata`
- **Status**: wip
- **Date**: 2025-12-10
- **Authors**: Aaron Solomon, Anthropic Claude Sonnet 4.5
- **Owner**: aaronksolomon

---

## Context

### Current State

Multiple modules currently contain hardcoded metadata that should be centralized and externalized:

1. **Pricing Defaults** (`src/tnh_scholar/gen_ai_service/config/settings.py:61`):

   ```python
   price_per_1k_tokens: float = 0.005
   ```

2. **Model Capabilities** (`src/tnh_scholar/gen_ai_service/routing/model_router.py:26`):

   ```python
   _MODEL_CAPABILITIES: Mapping[str, _Capability] = {
       "gpt-5o-mini": _Capability(vision=True, structured=True),
       "gpt-5o": _Capability(vision=True, structured=True),
       # ... hardcoded capability map
   }
   ```

3. **Context Limits** (`src/tnh_scholar/gen_ai_service/utils/token_utils.py:78`):

   ```python
   MODEL_CONTEXT_LIMITS: tuple[ModelLimitEntry, ...] = (
       ("gpt-5o-mini", 200_000),
       ("gpt-5o", 200_000),
       # ... hardcoded context limits
   )
   ```

### Problems with Current Approach

1. **Scattered Metadata**: Provider information duplicated across multiple modules
2. **Manual Updates**: Pricing and capability changes require code modifications
3. **No Single Source of Truth**: Inconsistencies between modules
4. **Poor Discoverability**: Users can't easily see available models or pricing
5. **Testing Difficulty**: Can't easily swap registries for testing
6. **No Audit Trail**: Changes to pricing/capabilities not tracked
7. **VS Code Integration Gap**: No alignment with upcoming VS Code extension configuration system

### External Data Availability Research

**OpenAI Pricing API**: After investigation ([Issue #2074](https://github.com/openai/openai-python/issues/2074)), OpenAI does **not** provide a programmatic pricing endpoint. Community requests exist ([OpenAI Forum](https://community.openai.com/t/is-there-an-endpoint-to-programmatically-fetch-openai-model-pricing/1229924)) but the feature is marked "not planned."

**Available Alternatives**:

- Official pricing page: <https://openai.com/api/pricing/>
- Usage/Costs API: Provides spend tracking but not pricing rates
- Models list endpoint: Lists models but excludes pricing/capabilities

**Implication**: We must maintain our own pricing data with manual or semi-automated updates from the official pricing page.

### VS Code Configuration System Research

**VS Code Native Format**: VS Code uses **JSON with Comments (JSONC)** for all configuration files:

- `settings.json`, `tasks.json`, `launch.json` use JSONC format
- JSONC supports `//` and `/* */` comments plus trailing commas
- JSON Schema enables IntelliSense and validation in VS Code
- Extension contribution system uses JSON/JSONC exclusively

**TNH Scholar VS Code Integration** (see [ADR-VSC01](/architecture/ui-ux/vs-code-integration/adr-vsc01-vscode-integration-strategy.md)):

- Workspace config: `.vscode/tnh-scholar.json`
- `tnh-gen` CLI will consume JSON configs
- Aligning registry format creates ecosystem consistency

### Referenced in Prior ADRs

- **ADR-A08**: "Future: provider registry, dynamic pricing, and per-model metadata" (line 82)
- **ADR-A09**: "Static price table in config; dynamic pricing registry deferred" (line 103)
- **ADR-OS01**: Multiple TODOs about externalizing capability constants
- **ADR-VSC01**: VS Code integration strategy using JSON configuration

## Decision

### Registry Architecture

Implement a **file-based registry system** using **JSON with Comments (JSONC)** format to align with VS Code's native configuration system, enabling seamless integration with the upcoming VS Code extension and providing excellent IDE tooling support.

#### Object-Service Layering

Per [ADR-OS01](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md), registry loading follows strict architectural boundaries:

**Domain Layer** (`src/tnh_scholar/gen_ai_service/config/`):

- `registry.py`: Registry loader domain logic and API (no protocol for V1)
- Returns typed domain models (`ModelInfo`, `ProviderRegistry`)
- Owns caching and validation; delegates parsing/override merging to infrastructure helpers

**Infrastructure Layer** (`src/tnh_scholar/gen_ai_service/adapters/registry/`):

- `jsonc_parser.py`: Pure JSONC parsing utilities (comment stripping, validation)
- `override_merger.py`: Typed override merging strategy
- Handles all file I/O and parsing

**Data Layer** (built-in, workspace, user):

- Built-in: `runtime_assets/registries/providers/*.jsonc`
- Workspace: `.tnh-scholar/registries/providers/*.jsonc`
- User: `~/.config/tnh-scholar/registries/providers/*.jsonc`
- Overrides: `{layer}/registries/overrides/<provider>.jsonc`
- `schema.json`: JSON Schema for VS Code validation (built-in layer)
- No Python code in these directories (data only)

**Schema Definitions** (`src/tnh_scholar/gen_ai_service/models/registry.py`):

- Pydantic models: `ModelInfo`, `ProviderRegistry`, `ModelCapabilities`, etc.
- Shared by domain and infrastructure layers
- Lives in models package per ADR-OS01 convention

**Dependency Flow**: Settings/Service → TNHContext → RegistryLoader → JsoncParser/OverrideMerger → Data Files

#### Core Design Principles

1. **VS Code Native**: JSONC format matches VS Code's `settings.json`, `package.json` conventions
2. **Human-Editable First**: JSONC supports comments and trailing commas for readability
3. **IDE Integration**: JSON Schema enables autocomplete and validation in VS Code
4. **Version-Controlled**: Built-in and workspace registries are committed to git; user registries are local-only
5. **Layered Precedence**: Workspace → user → built-in (per ADR-CF01 ownership rules)
6. **Schema-Validated**: All registry files validated via Pydantic models + JSON Schema
7. **Auto-Update Capable**: Optional scripts to fetch and update from stable URLs
8. **Strongly Typed**: Registry loader returns typed domain models, never dicts

### File Structure

```text
# Built-in data (package, target layout)
runtime_assets/
  registries/
    providers/
      openai.jsonc             # OpenAI models, pricing, capabilities
      anthropic.jsonc          # Anthropic models (future)
      schema.json              # JSON Schema for VS Code autocomplete
    .registry-metadata.json    # Last-update timestamps, sources

# Workspace data (project)
.tnh-scholar/
  registries/
    providers/
      openai.jsonc             # Project-specific overrides or additions
    overrides/
      openai.jsonc             # Provider-specific overrides (typed)

# User data (personal)
~/.config/tnh-scholar/
  registries/
    providers/
      openai.jsonc             # Personal overrides or additions
    overrides/
      openai.jsonc             # Provider-specific overrides (typed)

# Code files (src/)
src/tnh_scholar/gen_ai_service/
  models/
    registry.py                # Pydantic validation schemas (ModelInfo, etc.)
  config/
    registry.py                # Registry loader API (no protocol for V1)
  adapters/
    registry/
      jsonc_parser.py          # JSONC parsing utilities
      override_merger.py       # Typed override merging
```

### Registry Schema (providers/openai.jsonc)

```jsonc
// runtime_assets/registries/providers/openai.jsonc
{
  "$schema": "./schema.json",
  "schema_version": "1.0",
  "provider": "openai",
  "last_updated": "2025-12-10",
  "source_url": "https://openai.com/api/pricing/",
  "update_method": "manual",  // or "auto-scrape" when implemented

  // Default provider settings
  "defaults": {
    "base_url": "https://api.openai.com/v1",
    "timeout_s": 60.0,
    "max_retries": 3
  },

  // Model registry
  "models": {
    "gpt-5-mini": {
      "display_name": "GPT-5 Mini",
      "family": "gpt-5",
      "capabilities": {
        "vision": true,
        "structured_output": true,
        "function_calling": true,
        "streaming": true
      },
      "context_window": 128000,
      "max_output_tokens": 16384,
      "pricing": {
        "input_per_1k": 0.00015,   // $0.15 per 1M input tokens
        "output_per_1k": 0.0006,   // $0.60 per 1M output tokens
        "cached_input_per_1k": 0.000075  // 50% discount for cached
      },
      "training_cutoff": "2024-10",
      "released": "2024-11-20",
      "deprecated": false,
      "aliases": ["gpt-5-mini-latest"]
    },

    "gpt-5o": {
      "display_name": "GPT-5 Optimized",
      "family": "gpt-5",
      "capabilities": {
        "vision": true,
        "structured_output": true,
        "function_calling": true,
        "streaming": true
      },
      "context_window": 128000,
      "max_output_tokens": 16384,
      "pricing": {
        "input_per_1k": 0.0025,
        "output_per_1k": 0.01,
        "cached_input_per_1k": 0.00125
      },
      "training_cutoff": "2024-10",
      "released": "2024-11-20",
      "deprecated": false,
      "aliases": ["gpt-5o-latest"]
    },

    "gpt-4o": {
      "display_name": "GPT-4 Optimized",
      "family": "gpt-4",
      "capabilities": {
        "vision": true,
        "structured_output": true,
        "function_calling": true,
        "streaming": true
      },
      "context_window": 128000,
      "max_output_tokens": 16384,
      "pricing": {
        "input_per_1k": 0.0025,
        "output_per_1k": 0.01,
        "cached_input_per_1k": 0.00125
      },
      "training_cutoff": "2023-10",
      "released": "2024-05-13",
      "deprecated": false
    },

    "gpt-4o-mini": {
      "display_name": "GPT-4o Mini",
      "family": "gpt-4",
      "capabilities": {
        "vision": true,
        "structured_output": true,
        "function_calling": true,
        "streaming": true
      },
      "context_window": 128000,
      "max_output_tokens": 16384,
      "pricing": {
        "input_per_1k": 0.00015,
        "output_per_1k": 0.0006,
        "cached_input_per_1k": 0.000075
      },
      "training_cutoff": "2023-10",
      "released": "2024-07-18",
      "deprecated": false
    },

    "gpt-3.5-turbo": {
      "display_name": "GPT-3.5 Turbo",
      "family": "gpt-3.5",
      "capabilities": {
        "vision": false,
        "structured_output": false,
        "function_calling": true,
        "streaming": true
      },
      "context_window": 16385,
      "max_output_tokens": 4096,
      "pricing": {
        "input_per_1k": 0.0005,
        "output_per_1k": 0.0015
      },
      "training_cutoff": "2021-09",
      "released": "2022-11-28",
      "deprecated": false
    }
  },

  // Rate limits (tier-based, can be overridden locally)
  "rate_limits": {
    "tier_1": {
      "requests_per_minute": 500,
      "tokens_per_minute": 30000
    },
    "tier_2": {
      "requests_per_minute": 5000,
      "tokens_per_minute": 450000
    }
  }
}
```

### JSON Schema for VS Code (providers/schema.json)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://tnh-scholar.org/schemas/provider-registry-v1.json",
  "title": "TNH Scholar Provider Registry",
  "description": "Registry of AI provider models, capabilities, and pricing",
  "type": "object",
  "required": ["schema_version", "provider", "last_updated", "defaults", "models"],
  "properties": {
    "$schema": {
      "type": "string",
      "description": "JSON Schema reference"
    },
    "schema_version": {
      "type": "string",
      "enum": ["1.0"],
      "description": "Registry schema version"
    },
    "provider": {
      "type": "string",
      "enum": ["openai", "anthropic"],
      "description": "Provider identifier"
    },
    "last_updated": {
      "type": "string",
      "format": "date",
      "description": "Date of last registry update (YYYY-MM-DD)"
    },
    "source_url": {
      "type": "string",
      "format": "uri",
      "description": "Source URL for pricing/capability information"
    },
    "update_method": {
      "type": "string",
      "enum": ["manual", "auto-scrape", "api"],
      "description": "How this registry is updated"
    },
    "defaults": {
      "type": "object",
      "required": ["base_url"],
      "properties": {
        "base_url": {
          "type": "string",
          "format": "uri",
          "description": "Default API base URL"
        },
        "timeout_s": {
          "type": "number",
          "minimum": 0,
          "description": "Default timeout in seconds"
        },
        "max_retries": {
          "type": "integer",
          "minimum": 0,
          "description": "Default maximum retry attempts"
        }
      }
    },
    "models": {
      "type": "object",
      "additionalProperties": {
        "$ref": "#/definitions/ModelInfo"
      },
      "description": "Model registry keyed by model identifier"
    },
    "rate_limits": {
      "type": "object",
      "additionalProperties": {
        "$ref": "#/definitions/RateLimitTier"
      },
      "description": "Rate limit tiers"
    }
  },
  "definitions": {
    "ModelInfo": {
      "type": "object",
      "required": ["display_name", "family", "capabilities", "context_window", "max_output_tokens", "pricing"],
      "properties": {
        "display_name": {
          "type": "string",
          "description": "Human-readable model name"
        },
        "family": {
          "type": "string",
          "description": "Model family (e.g., gpt-4, gpt-5)"
        },
        "capabilities": {
          "$ref": "#/definitions/ModelCapabilities"
        },
        "context_window": {
          "type": "integer",
          "minimum": 1,
          "description": "Maximum context window size in tokens"
        },
        "max_output_tokens": {
          "type": "integer",
          "minimum": 1,
          "description": "Maximum output tokens"
        },
        "pricing": {
          "$ref": "#/definitions/ModelPricing"
        },
        "training_cutoff": {
          "type": "string",
          "description": "Training data cutoff (YYYY-MM format)"
        },
        "released": {
          "type": "string",
          "format": "date",
          "description": "Model release date"
        },
        "deprecated": {
          "type": "boolean",
          "description": "Whether model is deprecated"
        },
        "aliases": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Alternative names for this model"
        }
      }
    },
    "ModelCapabilities": {
      "type": "object",
      "properties": {
        "vision": {
          "type": "boolean",
          "description": "Supports image inputs"
        },
        "structured_output": {
          "type": "boolean",
          "description": "Supports JSON mode / structured outputs"
        },
        "function_calling": {
          "type": "boolean",
          "description": "Supports function/tool calling"
        },
        "streaming": {
          "type": "boolean",
          "description": "Supports streaming responses"
        },
        "audio_input": {
          "type": "boolean",
          "description": "Supports audio inputs"
        },
        "audio_output": {
          "type": "boolean",
          "description": "Supports audio outputs"
        }
      }
    },
    "ModelPricing": {
      "type": "object",
      "required": ["input_per_1k", "output_per_1k"],
      "properties": {
        "input_per_1k": {
          "type": "number",
          "minimum": 0,
          "description": "Price per 1K input tokens in USD"
        },
        "output_per_1k": {
          "type": "number",
          "minimum": 0,
          "description": "Price per 1K output tokens in USD"
        },
        "cached_input_per_1k": {
          "type": "number",
          "minimum": 0,
          "description": "Price per 1K cached input tokens in USD"
        }
      }
    },
    "RateLimitTier": {
      "type": "object",
      "required": ["requests_per_minute", "tokens_per_minute"],
      "properties": {
        "requests_per_minute": {
          "type": "integer",
          "minimum": 1,
          "description": "Maximum requests per minute"
        },
        "tokens_per_minute": {
          "type": "integer",
          "minimum": 1,
          "description": "Maximum tokens per minute"
        }
      }
    }
  }
}
```

### Pydantic Schema (src/tnh_scholar/gen_ai_service/models/registry.py)

```python
"""Pydantic schemas for registry validation.

All registry JSONC files must validate against these schemas.
Follows ADR-OS01 convention: models live in src/, data lives in runtime_assets/.
"""
from datetime import date
from typing import Dict, Literal

from pydantic import BaseModel, Field, HttpUrl


class ModelCapabilities(BaseModel):
    """Model capability flags."""
    vision: bool = False
    structured_output: bool = False
    function_calling: bool = False
    streaming: bool = False
    audio_input: bool = False
    audio_output: bool = False


class ModelPricing(BaseModel):
    """Per-model pricing in dollars per 1K tokens."""
    input_per_1k: float = Field(ge=0, description="Input token price per 1K")
    output_per_1k: float = Field(ge=0, description="Output token price per 1K")
    cached_input_per_1k: float | None = Field(
        None, ge=0, description="Cached input price (if supported)"
    )


class ModelInfo(BaseModel):
    """Complete model metadata."""
    display_name: str
    family: str
    capabilities: ModelCapabilities
    context_window: int = Field(gt=0)
    max_output_tokens: int = Field(gt=0)
    pricing: ModelPricing
    training_cutoff: str | None = None
    released: date | None = None
    deprecated: bool = False
    aliases: list[str] = Field(default_factory=list)


class ProviderDefaults(BaseModel):
    """Provider-level defaults."""
    base_url: HttpUrl
    timeout_s: float = Field(gt=0, default=60.0)
    max_retries: int = Field(ge=0, default=3)


class RateLimitTier(BaseModel):
    """Rate limit configuration for a tier."""
    requests_per_minute: int = Field(gt=0)
    tokens_per_minute: int = Field(gt=0)


class ProviderRegistry(BaseModel):
    """Root registry schema for a provider."""
    schema_version: Literal["1.0"] = "1.0"
    provider: str = Field(min_length=1)
    last_updated: date
    source_url: HttpUrl | None = None
    update_method: Literal["manual", "auto-scrape", "api"] = "manual"

    defaults: ProviderDefaults
    models: Dict[str, ModelInfo]
    rate_limits: Dict[str, RateLimitTier] = Field(default_factory=dict)

    class Config:
        extra = "forbid"  # Fail on unknown fields


class PricingOverride(BaseModel):
    """Override for a single model's pricing."""
    input_per_1k: float | None = Field(None, ge=0)
    output_per_1k: float | None = Field(None, ge=0)
    cached_input_per_1k: float | None = Field(None, ge=0)


class ModelOverride(BaseModel):
    """Override for a single model's metadata."""
    pricing: PricingOverride | None = None
    deprecated: bool | None = None


class RegistryOverrides(BaseModel):
    """User overrides for a provider registry."""
    schema_version: Literal["1.0"] = "1.0"
    provider: str
    models: Dict[str, ModelOverride] = Field(default_factory=dict)

    class Config:
        extra = "forbid"
```

### Schema Sync Strategy

**Challenge**: Maintain consistency between JSON Schema (`schema.json`) and Pydantic models (`models/registry.py`).

**Decision**: Manual synchronization with validation in CI.

**Rationale**:

- JSON Schema is the source of truth for VS Code IntelliSense
- Pydantic models are the source of truth for runtime validation
- Bi-directional generation adds complexity and brittleness
- Schema changes are infrequent (only on registry format updates)

**Process**:

1. **Schema Definition**: When adding new fields, update BOTH files:
   - `runtime_assets/registries/providers/schema.json` (for VS Code)
   - `src/tnh_scholar/gen_ai_service/models/registry.py` (for runtime)

2. **Validation**: CI validates consistency via test:

   ```python
   # tests/test_registry_schema.py
   def test_pydantic_matches_json_schema():
       """Verify Pydantic models match JSON Schema definitions."""
       json_schema = load_json_schema("runtime_assets/registries/providers/schema.json")
       pydantic_schema = ProviderRegistry.model_json_schema()

       # Compare required fields, types, constraints
       assert_schemas_match(json_schema, pydantic_schema)
   ```

3. **Documentation**: Schema changes require updating:
   - JSON Schema `schema.json`
   - Pydantic models `models/registry.py`
   - Example JSONC files `providers/openai.jsonc`
   - ADR-A14 (this document) if structural

**Future Consideration**: If schema changes become frequent, consider:

- Pydantic → JSON Schema generation (via `pydantic.json_schema()`)
- Or JSON Schema → Pydantic generation (via `datamodel-code-generator`)

**Why Not Auto-Generate Now**:

- Schema is stable (infrequent changes)
- Manual control ensures optimal VS Code IntelliSense
- Avoids build-time code generation complexity
- Hand-crafted JSON Schema provides better descriptions and examples

### Architectural Rationale: Pragmatic Layering

This implementation follows ADR-OS01's **spirit** (separation of concerns, testability, strong typing) without unnecessary protocol abstraction.

**Why no `RegistryLoaderProtocol`?**

Protocols are valuable when:

- Multiple implementations exist or are likely (database, HTTP API, file-based)
- Runtime swapping is required
- Abstract interface adds clarity to consumer code

**Our reality:**

- JSONC file-based storage is a **strategic architectural decision**, not a swappable detail
- OpenAI confirmed no pricing API exists (external data source ruled out)
- YAML/TOML alternatives explicitly rejected for VS Code ecosystem alignment
- Consumers only need `get_model_info(provider, model) -> ModelInfo` - they don't care about implementation
- Testing can mock at the class level without protocol overhead

**What we DO extract:**

- **JsoncParser**: Legitimate concern - parsing implementation might improve (library vs regex)
- **OverrideMerger**: Focused responsibility, testable business logic
- Both are **injectable dependencies** for testing without protocol ceremony

This achieves ADR-OS01's goals (clean separation, testability, maintainability) with appropriate abstraction level for V1.

### Registry Path Configuration

Per [ADR-CF01: Runtime Context Strategy](/architecture/configuration/adr/adr-cf01-runtime-context-strategy.md), registry discovery is delegated to `TNHContext`.

**Registry Lookup Strategy:**

1. **Workspace layer**: `<project>/.tnh-scholar/registries/providers/`
   - Project-owned registries and overrides
   - Discovered via `TNHContext` workspace root discovery

2. **User layer**: `~/.config/tnh-scholar/registries/providers/`
   - Personal overrides and local customizations
   - Resolved via `platformdirs.user_config_dir("tnh-scholar")`

3. **Built-in layer**: `<package>/runtime_assets/registries/providers/`
   - Read-only reference registries shipped with package
   - Located via `importlib.resources` (no TNH_ROOT dependency)

4. **Explicit override**: Constructor parameter for testing
   - `RegistryLoader(registry_paths=[custom_path])` for fixtures
   - Enables testing with mock registries without environment changes

### Registry Loader Architecture

**Domain Layer: `config/registry.py`**

Responsibilities:

- Orchestrate registry loading with caching
- Resolve model aliases to canonical names
- Apply override merging via infrastructure helpers
- Return strongly-typed domain models (`ModelInfo`, `ProviderRegistry`)
- Use `TNHContext` to resolve registry and override search paths

Key methods:

- `get_provider(provider: str) -> ProviderRegistry` - Load and cache provider registry
- `get_model(provider, model) -> ModelInfo` - Resolve model with alias support
- Constructor accepts optional `registry_paths`, `parser`, `merger` for dependency injection

Path resolution:

- If `registry_paths` is None, use `TNHContext.get_registry_search_paths("providers")`
- Search in order: workspace → user → built-in
- Raise clear `ConfigurationError` if registry not found in any layer

**Infrastructure Layer: `adapters/registry/jsonc_parser.py`**

Responsibilities:

- Pure JSONC parsing (strip comments, trailing commas)
- Convert JSONC files to Python dicts for validation
- Handle both file paths and string content

Key methods:

- `parse_file(path: Path) -> dict` - Load and parse JSONC file
- `parse_string(content: str) -> dict` - Parse JSONC string

Implementation notes:

- Regex-based comment stripping for V1 (simple, no dependencies)
- Future: Consider library-based parser if regex proves fragile
- Raises `json.JSONDecodeError` for invalid JSON after comment removal

**Infrastructure Layer: `adapters/registry/override_merger.py`**

Responsibilities:

- Apply typed overrides to base registry models
- Merge pricing, capabilities, deprecation flags
- Validate override files against `RegistryOverrides` schema

Key methods:

- `apply_overrides(registry, provider, overrides_dir, parser) -> ProviderRegistry`

Implementation notes:

- Mutates registry in-place for V1 simplicity
- Skips overrides for unknown models (defensive)
- Returns modified registry for method chaining

**Public API:**

Convenience functions for common use cases:

- `get_model_info(provider, model) -> ModelInfo` - Get model with capabilities/pricing
- `list_models(provider) -> list[str]` - List available models for provider

### Integration with Existing Modules

**Replace hardcoded constants with registry lookups:**

#### 1. Model Routing (`routing/model_router.py`)

Current problem: Hardcoded `_MODEL_CAPABILITIES` dict duplicates registry data.

**Integration approach:**

- Extract capability checking to focused helper: `_has_capability(model_info, capability) -> bool`
- Extract fallback selection to strategy class: `ModelFallbackSelector`
- Main routing function delegates to helpers, maintains single responsibility

**Key change:**

```python
from tnh_scholar.gen_ai_service.config.registry import get_model_info

# Replace: _MODEL_CAPABILITIES dict lookup
# With: get_model_info(provider, model).capabilities
```

#### 2. Cost Estimation (`safety/safety_gate.py`)

Current problem: Hardcoded `_PRICE_PER_1K_TOKENS` constant.

**Integration approach:**

- Extract cost calculation to pure function: `_calculate_token_cost(pricing, tokens_in, tokens_out, use_cache) -> float`
- Extract price lookup to helper: `_get_pricing(provider, model) -> ModelPricing`
- Safety gate orchestrator delegates to focused helpers

**Key change:**

```python
from tnh_scholar.gen_ai_service.config.registry import get_model_info

# Replace: hardcoded _PRICE_PER_1K_TOKENS
# With: get_model_info(provider, model).pricing
```

#### 3. Context Limits (`utils/token_utils.py`)

Current problem: Hardcoded `MODEL_CONTEXT_LIMITS` tuple.

**Integration approach:**

- Replace pattern-matching tuple with direct registry lookup
- Single-line helper: `get_context_limit(provider, model) -> int`
- No sequential logic needed - direct delegation

**Key change:**

```python
from tnh_scholar.gen_ai_service.config.registry import get_model_info

# Replace: MODEL_CONTEXT_LIMITS pattern matching
# With: get_model_info(provider, model).context_window
```

#### 4. Settings Validation (`config/settings.py`)

Current problem: Settings validators can't access dynamic registry data.

**Integration approach:**

- Extract validation to helper class: `ModelConfigValidator`
- Validator delegates to helper methods for registry lookups
- Keep validators focused on single validation concerns

**Pattern:**

```python
# Validator delegates to focused helper
model_info = get_model_info(provider, model)
if not _is_within_limit(max_tokens, model_info.context_window):
    raise ValueError(...)
```

**Implementation guidance:**

- Each integration point should extract helpers (functions or classes)
- Avoid sequential logic in main functions - dispatch to focused helpers
- Use classes when state tracking needed (e.g., fallback selection with history)
- Keep functions ≤20 LOC, cyclomatic complexity ≤9

### Auto-Update Mechanism

**Script: `scripts/update_registry.py`**

**V1 Requirements (Manual Update Helper):**

Core functionality:

- Check registry staleness (days since `last_updated` field)
- Provide manual update instructions when stale
- Validate updated registry files against Pydantic schema
- Runtime warnings are configured via `GenAISettings.registry_staleness_warn` and `GenAISettings.registry_staleness_threshold_days` (see [ADR-A14.1](/architecture/gen-ai-service/adr/adr-a14.1-registry-staleness-detection.md))

CLI interface:

- `--check-staleness` - Report age of each provider registry
- `--validate PROVIDER` - Validate registry file syntax and schema
- Exit codes: 0 (OK), 1 (stale >90 days), 2 (validation error)

**V2 Future (Auto-Scraping - Optional):**

Additional functionality if web scraping dependencies available:

- Fetch OpenAI pricing page HTML
- Parse pricing table to extract current values
- Show diff between current registry and scraped data
- `--apply` flag to write changes (with confirmation)

Optional dependencies: `requests`, `beautifulsoup4` (not required for V1)

**Design approach:**

- Extract staleness checking to pure function: `get_registry_age(path) -> int`
- Extract validation to helper: `validate_registry_file(path) -> list[ErrorInfo]`
- Use `JsoncParser` from registry infrastructure (no duplication)
- CLI orchestrator delegates to focused helpers
- Keep main script <50 LOC by extracting logic to helper modules

#### CI Integration

Add to `.github/workflows/registry-check.yml`:

```yaml
name: Registry Staleness Check

on:
  schedule:
    - cron: '0 0 * * 1'  # Weekly on Mondays
  workflow_dispatch:

jobs:
  check-staleness:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: poetry install
      - name: Check registry staleness
        id: check
        run: |
          poetry run python scripts/update_registry.py --check-staleness
          days=$(poetry run python scripts/update_registry.py --check-staleness | grep openai | awk '{print $3}')
          if [ "$days" -gt 90 ]; then
            echo "stale=true" >> $GITHUB_OUTPUT
            echo "days=$days" >> $GITHUB_OUTPUT
          fi
      - name: Create issue if stale
        if: steps.check.outputs.stale == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            const days = ${{ steps.check.outputs.days }};
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `Registry Update Needed: Pricing data ${days} days old`,
              body: `Provider registries may be out of date.\n\nPlease review and update:\n- Check https://openai.com/api/pricing/\n- Update runtime_assets/registries/providers/openai.jsonc\n- Commit changes with verification`,
              labels: ['maintenance', 'registry-update']
            });
```

### VS Code Integration

#### .vscode/settings.json

```jsonc
{
  // Associate schema with registry files
  "json.schemas": [
    {
      "fileMatch": [
        "runtime_assets/registries/providers/*.jsonc",
        ".vscode/tnh-scholar.json"
      ],
      "url": "./runtime_assets/registries/providers/schema.json"
    }
  ],

  // Enable JSONC for registry files
  "files.associations": {
    "**/registries/**/*.jsonc": "jsonc",
    ".vscode/tnh-scholar.json": "jsonc"
  }
}
```

This enables:

- ✅ Autocomplete for model names, pricing fields
- ✅ Inline validation errors for invalid values
- ✅ Hover documentation for fields
- ✅ IntelliSense suggestions

## Consequences

### Positive

1. **Single Source of Truth**: All provider metadata centralized in validated registries
2. **VS Code Native**: JSONC format matches VS Code ecosystem (settings.json, package.json)
3. **IDE Integration**: JSON Schema enables autocomplete and validation
4. **Human-Editable**: JSONC comments document pricing sources and changes
5. **Version Controlled**: Changes tracked in git with full history
6. **Type-Safe**: Pydantic validation prevents invalid data
7. **Testable**: Easy to swap registries for testing different configurations
8. **Discoverable**: Users can browse `runtime_assets/registries/` to see models
9. **Extensible**: Adding new providers requires only a new JSONC file
10. **Override-Friendly**: Users can locally override pricing without code changes
11. **Audit Trail**: Registry metadata tracks update sources and dates
12. **CI Integration**: Automated staleness checks prevent outdated pricing
13. **Ecosystem Consistency**: Same format as workspace config, extension settings

### Negative

1. **Manual Updates Required**: No programmatic OpenAI pricing API available
2. **Additional Files**: New directory structure and registry files to maintain
3. **Migration Work**: Existing hardcoded values must be moved to registries
4. **Learning Curve**: Developers must understand registry lookup patterns
5. **Validation Overhead**: Runtime validation adds minor startup cost (mitigated by caching)
6. **JSONC Parsing**: Requires custom parser (regex-based comment stripping)

### Risk Mitigation

- **Stale Data Risk**: CI checks + manual update reminders every 90 days
- **Invalid Registry Risk**: Pydantic validation fails fast with clear errors
- **Performance Risk**: Singleton + LRU caching ensures one-time load cost
- **Parse Errors**: Clear error messages with line numbers for syntax issues

## Alternatives Considered

### Alternative 1: YAML Format

**Pros**: Human-readable, no comment workarounds, multiline strings

**Cons**:

- Not VS Code native (settings.json uses JSONC)
- Ecosystem inconsistency with VS Code extension
- No JSON Schema support in VS Code
- Additional dependency (`pyyaml`)
- Less familiar to web developers

**Rejected**: JSONC is clearly superior for VS Code integration

### Alternative 2: Database-Backed Registry

**Pros**: Dynamic updates, multi-user edits, query flexibility

**Cons**:

- Requires database setup and migration system
- Overkill for read-heavy workload
- Harder to version-control and review changes
- More complex deployment

**Rejected**: Too heavy for current needs; file-based is sufficient for V1

### Alternative 3: Embedded Python Constants

**Pros**: No I/O, fastest access

**Cons**:

- Already causing problems (hardcoded literals everywhere)
- No user overrides without code changes
- Poor discoverability
- No audit trail

**Rejected**: This is the current problematic state we're fixing

### Alternative 4: External API Service

**Pros**: Always up-to-date, no manual work

**Cons**:

- Network dependency for startup
- Single point of failure
- Requires hosting and maintenance
- OpenAI doesn't provide this

**Rejected**: Not feasible given OpenAI's lack of pricing API

## Open Questions

1. **Multi-Provider Pricing**: Should we create a unified pricing comparison tool?
2. **Cached Token Pricing**: How to handle prompt caching discounts in cost estimates? (Now included in schema)
3. **Registry Versioning**: Should we support multiple registry versions simultaneously?
4. **Update Frequency**: What's the right cadence for checking staleness? (Proposed: 90 days)
5. **Web Scraping Legality**: Is automated scraping of OpenAI's pricing page acceptable? (Prefer manual for now)
6. **Model Deprecation**: How to handle deprecated models still in user code?
7. **Regional Pricing**: Do we need to support region-specific pricing? (Deferred to V2)

## Implementation Plan

### Phase 1: Core Registry (Week 1)

- [ ] Create directory structure `runtime_assets/registries/`
- [ ] Implement Pydantic schemas in `src/tnh_scholar/gen_ai_service/models/registry.py`
- [ ] Create JSON Schema in `providers/schema.json`
- [ ] Create `openai.jsonc` with current models/pricing
- [ ] Implement `RegistryLoader` with JSONC support
- [ ] Add unit tests for registry loading and validation

### Phase 2: Integration (Week 1-2)

- [ ] Refactor `model_router.py` to use registry
- [ ] Refactor `safety_gate.py` to use registry pricing
- [ ] Update `settings.py` validation to use registry
- [ ] Remove hardcoded constants from all modules
- [ ] Update tests to use registry fixtures

### Phase 3: Tooling (Week 2)

- [ ] Create `scripts/update_registry.py` skeleton
- [ ] Implement staleness checking
- [ ] Add CI workflow for staleness alerts
- [ ] Document registry update procedures
- [ ] Create user override example in docs
- [ ] **Note**: Web scraping dependencies (`requests`, `beautifulsoup4`) are optional for V1
  - V1 uses manual updates only
  - Auto-scraping planned for V2 (requires `poetry install --with scraping`)
  - Script gracefully degrades when dependencies unavailable

### Phase 4: Documentation (Week 2)

- [ ] Add registry usage to developer guide
- [ ] Document override mechanism
- [ ] Create registry maintenance playbook
- [ ] Add VS Code setup instructions

## Related ADRs

- **ADR-A08**: Config/Params/Policy Taxonomy (referenced registries as future work)
- **ADR-A09**: V1 Simplified Pathway (deferred registry to post-V1)
- **ADR-OS01**: Object-Service Architecture (strong typing requirements)
- **ADR-VSC01**: VS Code Integration Strategy (JSON configuration system)

## References

- [OpenAI Pricing Page](https://openai.com/api/pricing/)
- [OpenAI API Pricing Issue #2074](https://github.com/openai/openai-python/issues/2074)
- [OpenAI Developer Community: Pricing API Request](https://community.openai.com/t/is-there-an-endpoint-to-programmatically-fetch-openai-model-pricing/1229924)
- [VS Code Settings Documentation](https://code.visualstudio.com/docs/getstarted/settings)
- [VS Code JSON Editing](https://code.visualstudio.com/docs/languages/json)
- [VS Code Extension Contribution Points](https://code.visualstudio.com/api/references/contribution-points)
- [JSONC Specification](https://jsonc.org/)
- [Pydantic V2 Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

---

## As-Built Notes & Addenda

### 2026-01-01: Multi-Tier Pricing Implementation

**Status**: Implemented

**Changes**:

- Added `pricing_tiers` field to `ModelInfo` with support for batch, flex, standard, and priority tiers
- Updated all models in `openai.jsonc` with tiered pricing from official OpenAI pricing page
- Added `get_pricing(tier)` method to `ModelInfo` for tier-specific pricing retrieval
- Updated Pydantic schema to include `ModelPricingTiers` and `PricingTierMetadata`
- Fixed JSONC parser to handle URLs with `//` in strings (proper string-aware comment stripping)
- Removed backward compatibility - all models now require `pricing_tiers` (no legacy `pricing` field)

**Pricing Data Source**: OpenAI pricing page (2026-01-01, Standard tier)

**Batch Pricing Savings**:

- GPT-5: 50% savings on input/output
- GPT-5-mini: 50% savings on input/output
- GPT-4o: 50% savings on input/output
- GPT-4o-mini: 50% savings on input/output

### 2026-01-01: Custom JSONC Parser Decision

**Status**: Decision Final

**Context**:

ADR-A14 line 766 noted: "Future: Consider library-based parser if regex proves fragile." This addendum documents evaluation of the most popular Python JSONC library and the decision to retain the custom implementation.

**Evaluation of `jsonc-parser` Package**:

Investigated `jsonc-parser` (NickolaiBeloguzov, ~9K weekly downloads on PyPI):

**Package characteristics:**

- **Size**: 214 total lines (180 in `parser.py`, 34 in `errors.py`)
- **Implementation**: Regex-based comment stripping via `re.compile(r"(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\r\n]*$)", re.MULTILINE | re.DOTALL)`
- **Dependencies**: Zero (standard library only)
- **Maintenance**: No updates in 12+ months (as of 2026-01-01)

**Feature comparison:**

| Feature                            | `jsonc-parser`       | TNH Scholar Custom   |
| ---------------------------------- | -------------------- | -------------------- |
| Comment stripping (`//`, `/* */`)  | ✅ Regex-based       | ✅ State-machine     |
| Trailing comma support             | ❌ **Missing**       | ✅ Implemented       |
| Line/column error tracking         | ❌ Generic JSON errors | ✅ Custom tracking |
| String escape handling             | ✅ Via regex groups  | ✅ Explicit state    |
| Code size                          | 214 lines            | 173 lines            |
| Dependencies                       | 0                    | 0                    |

**Critical deficiency:**

The `jsonc-parser` package **does not handle trailing commas**, which are a core feature of JSONC and VS Code's `settings.json` format. The regex only strips comments:

```python
# Their implementation (parser.py:11)
regex = re.compile(r"(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\r\n]*$)", ...)
# No trailing comma logic present
```

Our implementation explicitly handles this via `_strip_trailing_commas()` (16 lines, `jsonc_parser.py:60-76`).

**Quality comparison:**

Custom implementation advantages:

- Better error messages with line/column numbers for debugging
- Proper context manager usage (`Path.read_text()` vs manual `open()`/`close()`)
- Cleaner separation of concerns (parsing vs validation)
- More robust string handling with explicit escape state tracking
- Already tested and working in production

**Decision**: **Retain custom JSONC parser implementation**

**Rationale**:

1. **Feature parity impossible**: `jsonc-parser` lacks trailing comma support (critical for VS Code compatibility)
2. **No size benefit**: Custom implementation is actually smaller (173 vs 214 lines)
3. **Quality superior**: Better error reporting, modern Python idioms, explicit state management
4. **Implementation equivalence**: Both use regex/parsing approach; library is not more robust
5. **Maintenance concern**: Package hasn't been updated in 12+ months
6. **Zero migration benefit**: Would need to add trailing comma logic anyway, negating any code reduction

**Reversal**: The ADR-A14 note about "consider library-based parser if regex proves fragile" is hereby **reversed**. After evaluating the canonical package, the custom implementation is confirmed as the superior choice for this use case.

**Files**: `src/tnh_scholar/gen_ai_service/adapters/registry/jsonc_parser.py:1-174`

**References**:

- [jsonc-parser on PyPI](https://pypi.org/project/jsonc-parser/)
- [jsonc-parser GitHub repository](https://github.com/NickolaiBeloguzov/jsonc-parser)

### Related Addenda

**[ADR-A14.1: Registry Staleness Detection](/architecture/gen-ai-service/adr/adr-a14.1-registry-staleness-detection.md)** (WIP 2026-01-01)

Extends this ADR with runtime warning system, CLI maintenance tooling, and CI automation for detecting when registry pricing data becomes outdated. Addresses the manual update workflow with configurable user warnings and GitHub workflow automation.
