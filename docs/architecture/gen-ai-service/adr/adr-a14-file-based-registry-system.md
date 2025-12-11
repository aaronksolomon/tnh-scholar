---
title: "ADR-A14: File-Based Registry System for Provider Metadata"
description: "Establishes a JSONC-based registry system for model capabilities, pricing, and provider metadata with auto-update mechanisms, aligned with VS Code's native configuration format."
owner: "aaronksolomon"
author: "Aaron Solomon, Anthropic Claude Sonnet 4.5"
status: proposed
created: "2025-12-10"
---
# ADR-A14: File-Based Registry System for Provider Metadata

Establishes a human-editable, file-based registry for model capabilities, pricing tables, and provider metadata using **JSON with Comments (JSONC)** format to align with VS Code's native configuration system.

- **Filename**: `adr-a14-file-based-registry-system.md`
- **Heading**: `# ADR-A14: File-Based Registry System for Provider Metadata`
- **Status**: Proposed
- **Date**: 2025-12-10
- **Authors**: Aaron Solomon, Anthropic Claude Sonnet 4.5
- **Owner**: aaronksolomon

---

## ADR Editing Policy

**IMPORTANT**: This ADR is in **proposed** status. We may rewrite or edit the document as needed to refine the design. Once accepted and implementation begins, only addenda may be added.

## Context

### Current State

Multiple modules currently contain hardcoded metadata that should be centralized and externalized:

1. **Pricing Constants** ([safety_gate.py:30](https://github.com/aaronksolomon/tnh-scholar/blob/main/src/tnh_scholar/gen_ai_service/safety/safety_gate.py#L30)):

   ```python
   _PRICE_PER_1K_TOKENS = 0.005  # placeholder until price tables are wired
   ```

2. **Model Capabilities** ([model_router.py:25-34](https://github.com/aaronksolomon/tnh-scholar/blob/main/src/tnh_scholar/gen_ai_service/routing/model_router.py#L25-L34)):

   ```python
   _MODEL_CAPABILITIES: Mapping[str, _Capability] = {
       "gpt-5o-mini": _Capability(vision=True, structured=True),
       "gpt-5o": _Capability(vision=True, structured=True),
       # ... hardcoded capability map
   }
   ```

3. **Context Limits** (token_utils.py):

   ```python
   MODEL_CONTEXT_LIMITS = [
       ("gpt-5", 128_000),
       ("gpt-4", 128_000),
       # ... hardcoded context limits
   ]
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

**TNH Scholar VS Code Integration** ([ADR-VSC01](/architecture/ui-ux/vs-code-integration/adr-vsc01-vscode-integration-strategy.md)):

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

#### Core Design Principles

1. **VS Code Native**: JSONC format matches VS Code's `settings.json`, `package.json` conventions
2. **Human-Editable First**: JSONC supports comments and trailing commas for readability
3. **IDE Integration**: JSON Schema enables autocomplete and validation in VS Code
4. **Version-Controlled**: Registry files live in `runtime_assets/registries/` and are committed to git
5. **Layered Precedence**: User overrides → project defaults → system defaults
6. **Schema-Validated**: All registry files validated via Pydantic models + JSON Schema
7. **Auto-Update Capable**: Optional scripts to fetch and update from stable URLs
8. **Strongly Typed**: Registry loader returns typed domain models, never dicts

### File Structure

```text
runtime_assets/
  registries/
    providers/
      openai.jsonc             # OpenAI models, pricing, capabilities
      anthropic.jsonc          # Anthropic models (future)
      schema.py                # Pydantic validation schemas
      schema.json              # JSON Schema for VS Code autocomplete
    overrides/                 # User-editable overrides (gitignored)
      pricing-overrides.jsonc  # Local price adjustments
      capability-overrides.jsonc
    .registry-metadata.json    # Last-update timestamps, sources
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

### Pydantic Schema (providers/schema.py)

```python
"""Pydantic schemas for registry validation.

All registry JSONC files must validate against these schemas.
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
```

### Registry Loader API

```python
# gen_ai_service/config/registry.py
"""Registry loader for provider metadata.

Provides singleton access to validated provider registries with layered
precedence: user overrides → project defaults → system defaults.
"""
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict

from pydantic import ValidationError

from tnh_scholar.gen_ai_service.models.errors import ConfigurationError
from tnh_scholar.runtime_assets.registries.providers.schema import (
    ModelInfo,
    ProviderRegistry,
)


def _load_jsonc(path: Path) -> dict:
    """Load JSON with Comments (JSONC) file.

    Strips comments and trailing commas before parsing.
    Compatible with VS Code's JSONC format.
    """
    with path.open() as f:
        content = f.read()

    # Strip single-line comments (// ...)
    content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)

    # Strip multi-line comments (/* ... */)
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

    # Strip trailing commas before } or ]
    content = re.sub(r',(\s*[}\]])', r'\1', content)

    return json.loads(content)


class RegistryLoader:
    """Loads and caches provider registries."""

    def __init__(self, registry_root: Path | None = None):
        """Initialize registry loader.

        Args:
            registry_root: Path to registries directory. Defaults to
                runtime_assets/registries in the package.
        """
        if registry_root is None:
            from tnh_scholar import TNH_ROOT
            registry_root = TNH_ROOT / "runtime_assets" / "registries"

        self.registry_root = registry_root
        self.providers_dir = registry_root / "providers"
        self.overrides_dir = registry_root / "overrides"
        self._cache: Dict[str, ProviderRegistry] = {}

    def get_provider(self, provider: str) -> ProviderRegistry:
        """Load and validate provider registry.

        Args:
            provider: Provider name (e.g., "openai", "anthropic")

        Returns:
            Validated ProviderRegistry instance

        Raises:
            ConfigurationError: If registry file missing or invalid
        """
        if provider in self._cache:
            return self._cache[provider]

        registry_path = self.providers_dir / f"{provider}.jsonc"
        if not registry_path.exists():
            raise ConfigurationError(
                f"Provider registry not found: {registry_path}"
            )

        try:
            data = _load_jsonc(registry_path)
            registry = ProviderRegistry.model_validate(data)

            # Apply user overrides if present
            self._apply_overrides(registry, provider)

            self._cache[provider] = registry
            return registry

        except ValidationError as e:
            raise ConfigurationError(
                f"Invalid provider registry {registry_path}: {e}"
            ) from e
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON in registry {registry_path}: {e}"
            ) from e

    def get_model(self, provider: str, model: str) -> ModelInfo:
        """Get model info with alias resolution.

        Args:
            provider: Provider name
            model: Model name or alias

        Returns:
            ModelInfo instance

        Raises:
            ConfigurationError: If model not found
        """
        registry = self.get_provider(provider)

        # Direct lookup
        if model in registry.models:
            return registry.models[model]

        # Alias lookup
        for model_name, info in registry.models.items():
            if model in info.aliases:
                return info

        raise ConfigurationError(
            f"Model {model} not found in {provider} registry. "
            f"Available: {', '.join(registry.models.keys())}"
        )

    def _apply_overrides(self, registry: ProviderRegistry, provider: str) -> None:
        """Apply user overrides if present (in-place modification)."""
        override_path = self.overrides_dir / f"{provider}-overrides.jsonc"
        if not override_path.exists():
            return

        # Load and merge overrides (pricing, rate limits, etc.)
        overrides = _load_jsonc(override_path)

        # Example: override pricing for specific models
        if "pricing" in overrides:
            for model_name, pricing_data in overrides["pricing"].items():
                if model_name in registry.models:
                    registry.models[model_name].pricing = ModelPricing.model_validate(
                        pricing_data
                    )


@lru_cache(maxsize=1)
def get_registry_loader() -> RegistryLoader:
    """Get singleton registry loader."""
    return RegistryLoader()


def get_model_info(provider: str, model: str) -> ModelInfo:
    """Convenience function to get model info.

    Args:
        provider: Provider name (e.g., "openai")
        model: Model name or alias

    Returns:
        ModelInfo with capabilities, pricing, limits

    Example:
        >>> info = get_model_info("openai", "gpt-4o-mini")
        >>> print(f"Context: {info.context_window}, Price: ${info.pricing.input_per_1k}")
    """
    return get_registry_loader().get_model(provider, model)


def list_models(provider: str) -> list[str]:
    """List available models for a provider.

    Args:
        provider: Provider name

    Returns:
        List of model identifiers
    """
    registry = get_registry_loader().get_provider(provider)
    return list(registry.models.keys())
```

### Integration with Existing Modules

#### 1. Update model_router.py

```python
# routing/model_router.py
from tnh_scholar.gen_ai_service.config.registry import get_model_info

def select_provider_and_model(...) -> ResolvedParams:
    """Intent-aware routing with registry-based capability checks."""

    # Look up model capabilities from registry
    model_info = get_model_info(params.provider, params.model)

    structured_needed = params.output_mode == "json"

    if structured_needed and not model_info.capabilities.structured_output:
        # Pick a structured-capable fallback
        fallback = _pick_structured_fallback(params.provider, settings.default_model)
        routing_reason = f"{routing_reason} → switched to {fallback}"
        model = fallback

    # ... rest of logic
```

#### 2. Update safety_gate.py

```python
# safety/safety_gate.py
from tnh_scholar.gen_ai_service.config.registry import get_model_info

def _estimate_cost(
    provider: str,
    model: str,
    tokens_in: int,
    max_tokens_out: int,
    *,
    use_cache: bool = False
) -> float:
    """Estimate cost using registry pricing."""
    model_info = get_model_info(provider, model)

    input_price = model_info.pricing.input_per_1k
    if use_cache and model_info.pricing.cached_input_per_1k:
        input_price = model_info.pricing.cached_input_per_1k

    input_cost = (tokens_in / 1000.0) * input_price
    output_cost = (max_tokens_out / 1000.0) * model_info.pricing.output_per_1k

    return input_cost + output_cost


def _context_limit_for_model(provider: str, model: str) -> int:
    """Get context limit from registry."""
    model_info = get_model_info(provider, model)
    return model_info.context_window
```

#### 3. Update settings.py

```python
# config/settings.py
from tnh_scholar.gen_ai_service.config.registry import get_model_info

@model_validator(mode="after")
def validate_max_output_tokens(cls, values):
    """Validate against registry-sourced context limits."""
    model = values.default_model
    provider = values.default_provider
    max_tokens = values.default_max_output_tokens

    model_info = get_model_info(provider, model)
    limit = model_info.context_window

    if max_tokens > limit:
        raise ValueError(
            f"default_max_output_tokens={max_tokens} exceeds "
            f"context limit for {model} ({limit})"
        )
    return values
```

### Auto-Update Mechanism

#### Update Script (scripts/update_registry.py)

```python
#!/usr/bin/env python
"""Update provider registries from external sources.

Usage:
    poetry run python scripts/update_registry.py openai --dry-run
    poetry run python scripts/update_registry.py openai --apply
    poetry run python scripts/update_registry.py --all --apply
"""
import argparse
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from tnh_scholar import TNH_ROOT


class RegistryUpdater:
    """Updates provider registry files."""

    def __init__(self, registry_root: Path):
        self.registry_root = registry_root

    def update_openai(self, dry_run: bool = True) -> dict:
        """Update OpenAI registry.

        Strategy:
        1. Fetch official pricing page HTML
        2. Parse pricing table (BeautifulSoup)
        3. Validate against current registry
        4. Show diff and update if --apply

        Returns:
            Dict of changes detected
        """
        # For V1, manual update only
        print("OpenAI pricing must be updated manually from:")
        print("https://openai.com/api/pricing/")

        registry_path = self.registry_root / "providers" / "openai.jsonc"
        print(f"\nRegistry location: {registry_path}")

        # Future: implement web scraping with BeautifulSoup
        # resp = requests.get("https://openai.com/api/pricing/")
        # soup = BeautifulSoup(resp.text, 'html.parser')
        # pricing_table = soup.find('table', class_='pricing')
        # ...

        return {"status": "manual_update_required"}

    def check_staleness(self, provider: str) -> int:
        """Check days since last registry update."""
        import json

        registry_path = self.registry_root / "providers" / f"{provider}.jsonc"

        # Load using simplified JSONC parser
        with registry_path.open() as f:
            content = f.read()
            # Strip comments for parsing
            import re
            content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            content = re.sub(r',(\s*[}\]])', r'\1', content)
            data = json.loads(content)

        last_updated = date.fromisoformat(data["last_updated"])
        days_old = (date.today() - last_updated).days

        return days_old


def main():
    parser = argparse.ArgumentParser(description="Update provider registries")
    parser.add_argument("provider", nargs="?", help="Provider to update (or --all)")
    parser.add_argument("--all", action="store_true", help="Update all providers")
    parser.add_argument("--apply", action="store_true", help="Apply changes")
    parser.add_argument("--check-staleness", action="store_true")

    args = parser.parse_args()

    registry_root = TNH_ROOT / "runtime_assets" / "registries"
    updater = RegistryUpdater(registry_root)

    if args.check_staleness:
        for provider in ["openai"]:  # Add more as implemented
            days = updater.check_staleness(provider)
            status = "⚠️ STALE" if days > 90 else "✅ OK"
            print(f"{provider}: {days} days old {status}")
        return

    if args.all or args.provider == "openai":
        updater.update_openai(dry_run=not args.apply)


if __name__ == "__main__":
    main()
```

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
- [ ] Implement Pydantic schemas in `providers/schema.py`
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

*This section will be populated during implementation. Never edit the original Context/Decision/Consequences sections - always append addenda here.*
