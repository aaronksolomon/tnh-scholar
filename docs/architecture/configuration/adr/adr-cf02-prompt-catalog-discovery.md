---
title: "ADR-CF02: Prompt Catalog Discovery Strategy"
description: "Extends TNHContext three-layer model to prompt catalog path resolution, replacing hard-coded module constants."
owner: "aaronksolomon"
author: "Claude Opus 4.5"
status: accepted
created: "2026-02-05"
related_adrs: ["adr-cf01-runtime-context-strategy.md", "adr-a08-config-params-policy-taxonomy.md"]
---

# ADR-CF02: Prompt Catalog Discovery Strategy

Extends the ADR-CF01 three-layer configuration model to prompt catalog discovery, providing consistent runtime resolution for user prompts (production) and dev prompts (workspace development).

- **Status**: Accepted
- **Date**: 2026-02-05
- **Authors**: Claude Opus 4.5
- **Owner**: aaronksolomon

---

## Context

### Current State

Prompt directory resolution is fragmented across multiple mechanisms:

| Source | Default Value | Mechanism |
|--------|---------------|-----------|
| `__init__.py:59` | `TNH_PROJECT_ROOT_DIR / "prompts"` | Hard-coded module constant |
| `GenAISettings.prompt_dir` | Falls back to `TNH_DEFAULT_PROMPT_DIR` | Env vars `PROMPT_DIR` or `TNH_PROMPT_DIR` |
| `PromptSystemSettings.tnh_prompt_dir` | `Path("prompts/")` (relative) | Env var `TNH_PROMPT_DIR` |
| tnh-gen `config_loader` | Gets from `GenAISettings` | 5-level precedence chain |

### Problems

1. **Hard-coded repo path**: `TNH_DEFAULT_PROMPT_DIR` in `__init__.py` points to `<repo>/prompts/`, which fails when tnh-scholar is installed as a package (no repo structure).

2. **Relative path ambiguity**: `PromptSystemSettings` defaults to `Path("prompts/")` - behavior depends on current working directory.

3. **No user vs dev distinction**: No clean separation between:
   - **User prompts**: Personal, persistent, lives in `~/.config/tnh-scholar/prompts/`
   - **Dev prompts**: Workspace-local, cloned from `tnh-prompts` repo for active development

4. **Inconsistent with registry pattern**: TNHContext implements three-layer discovery for registries (`RegistryPathBuilder`), but prompts don't use this established pattern.

5. **Import-time side effects**: `__init__.py` raises `FileNotFoundError` at import if expected paths don't exist, breaking package installs.

### Constraints

- Prompts are **not tracked in tnh-scholar's git repo**. They live in a separate [`tnh-prompts`](https://github.com/aaronksolomon/patterns) repository.
- End users install prompts via `tnh-setup`, which clones to `~/.config/tnh-scholar/prompts/`.
- Developers clone `tnh-prompts` into their workspace's `prompts/` directory for active development.
- A minimal fallback set should ship with the package for basic functionality.

---

## Decision

### 1. Extend TNHContext with Prompt Path Discovery

Add `PromptPathBuilder` to `src/tnh_scholar/configuration/context.py`, following the same pattern as `RegistryPathBuilder`:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PROMPT DIRECTORY PRECEDENCE                     │
├─────────────────────────────────────────────────────────────────────┤
│ 1. Workspace prompts  │ <workspace>/prompts/                        │
│    (dev use)          │ Discovered via TNHContext.workspace_root    │
│                       │ Clone of tnh-prompts repo for development   │
├───────────────────────┼─────────────────────────────────────────────┤
│ 2. User prompts       │ ~/.config/tnh-scholar/prompts/              │
│    (production)       │ Installed via tnh-setup                     │
│                       │ Standard location for end users             │
├───────────────────────┼─────────────────────────────────────────────┤
│ 3. Built-in prompts   │ <package>/runtime_assets/prompts/           │
│    (fallback)         │ Minimal set bundled with pip install        │
│                       │ Ensures basic functionality always works    │
└───────────────────────┴─────────────────────────────────────────────┘
```

**Key methods to add to TNHContext**:

- `get_prompt_search_paths() -> list[Path]`: Returns all valid prompt directories in precedence order
- `get_primary_prompt_dir() -> Path | None`: Returns highest-precedence directory that exists

### 2. Remove Module-Level Path Constants

Eliminate from `src/tnh_scholar/__init__.py`:

- `TNH_DEFAULT_PROMPT_DIR` - replace with lazy resolution via TNHContext
- `TNH_CONFIG_DIR` - replace with `UserRootLocator().resolve()`
- `TNH_LOG_DIR` - derive from user root at runtime

These constants violate the style guide's "no module-level constants" rule and bypass runtime discovery.

### 3. Update GenAISettings to Use TNHContext

Replace hard-coded default with lazy resolution:

```python
class GenAISettings(BaseSettings):
    prompt_dir: Path | None = Field(
        default=None,  # Resolved at runtime, not import time
        validation_alias=AliasChoices("PROMPT_DIR", "TNH_PROMPT_DIR"),
    )

    @model_validator(mode="after")
    def resolve_prompt_dir_default(self) -> "GenAISettings":
        if self.prompt_dir is None:
            from tnh_scholar.configuration.context import TNHContext
            context = TNHContext.discover()
            self.prompt_dir = context.get_primary_prompt_dir()
        return self
```

### 4. Consolidate PromptSystemSettings

Align `PromptSystemSettings` with `GenAISettings` - either:
- **Option A**: Deprecate `PromptSystemSettings.tnh_prompt_dir` in favor of `GenAISettings.prompt_dir`
- **Option B**: Have `PromptSystemSettings` also use TNHContext for its default

Recommendation: **Option A** - single source of truth for prompt directory in `GenAISettings`.

### 5. Bundle Minimal Built-in Prompts

Create `src/tnh_scholar/runtime_assets/prompts/` with a minimal set of essential prompts:

- `_catalog.yaml` (manifest)
- 2-3 core prompts for basic tnh-gen functionality

This ensures `pip install tnh-scholar` works out of the box without requiring `tnh-setup`.

---

## Consequences

### Positive

1. **Consistent discovery**: Prompts use the same three-layer model as registries (ADR-CF01).
2. **Package-installable**: No hard-coded repo paths; works correctly with `pip install`.
3. **Clean dev/user separation**: Developers get workspace prompts; users get `~/.config` prompts.
4. **No import-time failures**: Path resolution happens lazily, not at module import.
5. **Single source of truth**: One mechanism for prompt directory resolution across all subsystems.

### Negative

1. **Migration effort**: Existing code importing `TNH_DEFAULT_PROMPT_DIR` needs updating.
2. **Lazy resolution complexity**: First access to `GenAISettings().prompt_dir` triggers discovery.
3. **Built-in prompts maintenance**: Need to decide which prompts are "essential" for the fallback set.

### Neutral

- tnh-gen's existing 5-level config precedence continues to work; this ADR affects the *default* value, not the override chain.

---

## Alternatives Considered

### A. Keep Module Constants, Make Them Optional

Make `TNH_DEFAULT_PROMPT_DIR` gracefully handle missing directories instead of raising at import.

**Rejected**: Doesn't solve the package-install problem or provide three-layer discovery.

### B. Environment Variable Only

Require users to set `TNH_PROMPT_DIR` explicitly; no default discovery.

**Rejected**: Poor UX; `tnh-setup` already installs to a standard location that should "just work."

### C. Prompt Discovery in GenAISettings Only

Add discovery logic to `GenAISettings` without extending TNHContext.

**Rejected**: Duplicates the discovery pattern already established in TNHContext for registries. Violates DRY.

---

## Open Questions

1. **Which prompts are "essential" for built-in fallback?** Need to identify the minimal set that enables basic tnh-gen functionality without tnh-setup.

2. **Should workspace prompts require a marker file?** Currently workspace discovery uses `.tnh-scholar` or `.git` markers. Should prompt directories require explicit opt-in (e.g., `.tnh-prompts` marker)?

3. **PromptSystemSettings deprecation timeline**: When should we fully deprecate `PromptSystemSettings.tnh_prompt_dir` in favor of the unified approach?

---

## Implementation Phases

### Phase 1: Extend TNHContext (High Priority)

- Add `PromptPathBuilder` class to `context.py`
- Add `get_prompt_search_paths()` and `get_primary_prompt_dir()` to `TNHContext`
- Create `src/tnh_scholar/runtime_assets/prompts/` with minimal built-in set
- Unit tests for prompt path resolution

### Phase 2: Migrate GenAISettings (High Priority)

- Update `GenAISettings.prompt_dir` to use lazy TNHContext resolution
- Remove `from tnh_scholar import TNH_DEFAULT_PROMPT_DIR` dependency
- Update tnh-gen config_loader to work with new resolution

### Phase 3: Clean Up Module Constants (Medium Priority)

- Remove `TNH_DEFAULT_PROMPT_DIR`, `TNH_CONFIG_DIR`, `TNH_LOG_DIR` from `__init__.py`
- Update all import sites across codebase
- Remove `FileNotFoundError` raises at import time

### Phase 4: Consolidate Settings Classes (Medium Priority)

- Deprecate `PromptSystemSettings.tnh_prompt_dir`
- Document the unified prompt directory strategy
- Update CLI tools to use consistent resolution

---

## References

- [ADR-CF01: Runtime Context & Configuration Strategy](/architecture/configuration/adr/adr-cf01-runtime-context-strategy.md) - Parent three-layer model
- [ADR-A08: Config/Params/Policy Taxonomy](/architecture/gen-ai-service/adr/adr-a08-config-params-policy-taxonomy.md) - Settings vs Config distinction
- [tnh-prompts repository](https://github.com/aaronksolomon/patterns) - External prompt catalog
