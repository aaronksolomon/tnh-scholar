---
title: "ADR-CF01: Runtime Context & Configuration Strategy"
description: "Establishes unified project-wide strategy for configuration layers, data scoping, and runtime context resolution across all TNH Scholar subsystems"
type: "strategy"
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Sonnet 4.5"
status: proposed
created: "2025-12-31"
related_adrs: ["/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md", "/architecture/gen-ai-service/adr/adr-a14-file-based-registry-system.md", "/architecture/provenance/adr/adr-pv01-provenance-tracing-strat.md"]
---

# ADR-CF01: Runtime Context & Configuration Strategy

Establishes a uniform, predictable strategy for how TNH Scholar locates, merges, and resolves configuration, registries, and project data across built-in, workspace, and user layers—providing shared mental models and guardrails for all current and future subsystems.

- **Filename**: `adr-cf01-runtime-context-strategy.md`
- **Heading**: `# ADR-CF01: Runtime Context & Configuration Strategy`
- **Status**: Proposed
- **Date**: 2025-12-31
- **Authors**: Aaron Solomon, Claude Sonnet 4.5
- **Owner**: aaronksolomon
- **Related ADRs**:
  - [ADR-OS01: Object-Service Architecture V3](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md)
  - [ADR-A14: File-Based Registry System](/architecture/gen-ai-service/adr/adr-a14-file-based-registry-system.md)
  - [ADR-PV01: Provenance & Tracing Infrastructure Strategy](/architecture/provenance/adr/adr-pv01-provenance-tracing-strat.md)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip` status**: Coding has begun. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

**Rationale**: Once implementation begins, the original decision must be preserved for historical context.

---

## Context

### Discovery: Implicit Assumptions About Data Locations

During review of [ADR-A14: File-Based Registry System](/architecture/gen-ai-service/adr/adr-a14-file-based-registry-system.md), we discovered implicit assumptions about where data lives in TNH Scholar:

- ADR-A14 assumes registries exist at `runtime_assets/registries/` and `~/.config/tnh-scholar/registries/`
- Pattern catalogs reference `TNH_PATTERN_DIR` environment variable (legacy)
- Workspace-specific data has no standard discovery mechanism
- No uniform precedence rules across subsystems

**The problem**: Each subsystem makes independent assumptions about configuration scope and precedence, leading to:

1. **Inconsistent mental models** - GenAI service uses different scoping than tnh-gen CLI
2. **No workspace isolation** - Can't have project-specific registries or settings
3. **Hardcoded path dependencies** - Global constants like `TNH_ROOT` scattered across modules
4. **Conflicting precedence** - No consensus on user vs. workspace vs. built-in priority

### Current State: Fragmented Configuration Patterns

**Existing configuration locations across TNH Scholar:**

1. **Built-in defaults** (shipped with package, target layout):
   - Repo root `patterns/` (current)
   - `src/tnh_scholar/runtime_assets/` (planned migration target)
   - Module-level constants - scattered hardcoded values
   - Pydantic `BaseSettings` defaults

2. **User-level config** (personal overrides):
   - `~/.config/tnh-scholar/` - user settings (partially implemented)
   - Environment variables - API keys, feature flags
   - Some subsystems support, others don't

3. **Workspace/Project config** (nonexistent):
   - No standard location for project-specific data
   - No workspace discovery mechanism
   - No version-controlled project settings

**Example inconsistencies:**

- **GenAI Service**: Looks for registries in user config, then package bundled
- **Pattern System**: Uses `TNH_PATTERN_DIR` environment variable (deprecated)
- **tnh-gen CLI**: Generates output but has no workspace-scoped settings
- **Provenance**: Needs correlation IDs but no standard context object to carry them

### Architectural Gap: No Runtime Context Object

Current subsystems access configuration via:

- Direct imports of module constants (tight coupling)
- Environment variable lookups (scattered, implicit)
- Ad-hoc path construction (brittle, assumes structure)

**Missing**: A unified `TNHContext` object that encapsulates:

- Resolved configuration (merged from all layers)
- Discovered workspace root (if present)
- Registry search paths
- Runtime metadata (correlation IDs, session info)

This gap violates [ADR-OS01](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md) principle: avoid global state, inject dependencies.

### Motivation: VS Code-Inspired Mental Model

TNH Scholar aims to be editor-agnostic but draw inspiration from VS Code's layered configuration:

**VS Code's three-layer model:**

1. **Default Settings** - Shipped with VS Code
2. **User Settings** - `~/.config/Code/User/settings.json`
3. **Workspace Settings** - `.vscode/settings.json` (project-specific)

**Precedence**: Depends on setting ownership

- User preferences (theme, font): User > Workspace > Default
- Project requirements (linter rules): Workspace > User > Default

**Why this model fits TNH Scholar:**

- Clear, well-understood mental model for developers
- Supports both personal customization and project reproducibility
- Enables workspace isolation (multiple projects on one machine)
- Aligns with future VS Code extension integration

### References in Prior Work

- **ADR-A14** (lines 696-708): Registry path configuration mentions user config + package bundled fallback
- **ADR-OS01** (§1.1): "No global state" - configuration must be injected
- **ADR-PV01** (lines 42-50): Mentions correlation IDs need standard context object
- **tnh-configuration-management.md**: Older doc proposes YAML config, mentions precedence but incomplete

---

## Decision

### Core Design Principles

TNH Scholar adopts the following principles for all configuration and data location:

#### 1. No Global Path or Configuration Constants

**Rule**: All filesystem paths, defaults, and resolved settings MUST be determined at runtime.

**Rationale**:

- Eliminates brittle hardcoded paths
- Enables testing with custom locations
- Supports multiple workspace isolation
- Allows package installation in any location

**Anti-pattern (forbidden)**:

- Module-level constants for paths (e.g., `TNH_ROOT = Path(__file__).parent.parent`)
- Hardcoded registry directory construction
- Any global path computation at module import time

**Correct pattern**:

- Runtime discovery via `TNHContext.discover()`
- Path resolution via context methods (`get_registry_search_paths()`, etc.)
- No assumptions about package installation location

#### 2. Layered Configuration with Explicit Ownership

**Rule**: Precedence is NOT universal—it is determined by WHO owns the decision.

**Three configuration layers:**

1. **Built-in (System Defaults)**
   - Shipped with TNH Scholar package
   - Defines baseline behavior and schemas
   - Read-only, always available
   - Accessed via `importlib.resources` (not filesystem assumptions)

2. **Workspace / Project**
   - Lives inside repository at `.tnh-scholar/`
   - Defines project-specific defaults
   - Intended to be version-controlled and shared
   - Optional: absence of workspace config is valid

3. **User (Personal Overrides)**
   - Lives in OS-appropriate user config directories
   - Allows personal customization without modifying repositories
   - Safe for experimentation and local tuning
   - Standard location via `platformdirs` library

**Rationale**: VS Code proves this model scales from individual users to enterprise teams.

#### 3. Ownership-Based Precedence (Not Global)

**Rule**: Precedence order varies based on setting category.

**User-owned settings** (user preferences, personal workflow):

- **Examples**: Preferred models, cost thresholds, cache locations, logging verbosity, performance tuning
- **Precedence**: User → Workspace → Built-in
- **Rationale**: "How I prefer the system to behave on my machine"

**Project-owned settings** (correctness, reproducibility):

- **Examples**: Pattern sets, corpus-specific registries, chunking strategies, language pairs, evaluation rules, annotation schemas
- **Precedence**: Workspace → User → Built-in
- **Rationale**: "How this project must behave to be correct"

**System-owned settings** (invariants, safety):

- **Examples**: Schema versions, internal compatibility constraints, hard safety limits
- **Precedence**: Built-in only (or explicit opt-in override)
- **Rationale**: "Required for correctness or safety"

**Implementation**: Each setting declares its ownership category in schema metadata.

#### 4. VS Code-Inspired, Editor-Agnostic

**Rule**: Configuration mirrors VS Code's mental model without coupling to editor internals.

**What we adopt from VS Code:**

- Three-layer architecture (built-in, user, workspace)
- JSONC format for human-editable configs
- Ownership-based precedence
- Workspace discovery via marker files

**What we avoid:**

- Dependency on VS Code extensions or APIs
- Editor-specific configuration formats
- VS Code-only features (settings sync, profiles, etc.)

**Rationale**: Provide familiar patterns for developers while remaining usable in any environment (CLI, notebooks, other IDEs).

#### 5. Minimal but Extensible

**Rule**: Prefer simple, deterministic mechanisms over implicit behavior or magic.

**Design constraints:**

- Default behavior requires zero configuration
- Common cases work without config files
- Extension points explicit and documented
- No auto-discovery of arbitrary locations

**Rationale**: Complexity is added only when justified by real use cases.

---

## Configuration Layers (Detailed)

### Built-in (System Defaults)

**Location**: Package-bundled resources (target), repository assets (current)

```text
src/tnh_scholar/
  runtime_assets/
    registries/
      providers/
        openai.jsonc
        schema.json
    patterns/
      default-patterns.jsonc
    templates/
      default-prompts.jsonc
```

**Characteristics**:

- Shipped with `pip install tnh-scholar` (target layout)
- Read-only (users cannot modify package files)
- Always available (no network/filesystem dependencies)
- Accessed via `importlib.resources` (Python 3.9+)

**Current state (prototype)**:

- Assets live outside the package (for example, repo root `patterns/`)
- `runtime_assets/` is planned but not yet present in the repo
- `TNHContext` treats repo-root assets as built-in when running from source
- Prompt assets are in transition: `patterns/` is expected to move to a `prompts/` location per prompt-system ADRs

**Discovery**: Via `importlib.resources.files()` for package resource access (Python 3.9+)

**Use cases**:

- Default provider registries
- Baseline prompt templates
- System schemas and validators
- Fallback values when no user/workspace config exists

---

### Workspace / Project

**Location**: `.tnh-scholar/` directory in project root

```text
my-research-project/
  .tnh-scholar/
    config.jsonc           # Project settings
    registries/
      custom-models.jsonc  # Project-specific model overrides
    patterns/
      domain-patterns.jsonc
    .gitignore             # Exclude secrets, caches
  .git/                    # Workspace root marker
  src/
  docs/
```

**Characteristics**:

- Version-controlled (committed to git)
- Shared across team members
- Defines project-specific behavior
- Optional (absence is valid)

**Discovery strategy**:

1. **Explicit override** (highest priority):
   - CLI flag: `--workspace-root /path/to/project`
   - Environment variable: `TNH_WORKSPACE_ROOT=/path/to/project`

2. **Automatic discovery** (walk upward from CWD):
   - Search for `.tnh-scholar/` directory
   - Or search for `.git/` directory (workspace root marker)
   - Stop at filesystem root or home directory

**Discovery algorithm**:

- Walk upward from `start_path` (default: CWD) toward filesystem root
- Stop when finding `.tnh-scholar/` directory (explicit marker)
- Or stop when finding `.git/` directory (implicit workspace root)
- Stop at home directory boundary (don't search system-wide)
- Return `None` if no workspace found

**Use cases**:

- Corpus-specific model registries
- Research project configuration
- Team-shared prompt patterns
- Reproducible analysis settings

---

### User (Personal Overrides)

**Location**: OS-standard user config directory

**Platform-specific paths** (via `platformdirs`):

- **Linux**: `~/.config/tnh-scholar/`
- **macOS**: `~/Library/Application Support/tnh-scholar/`
- **Windows**: `%APPDATA%\tnh-scholar\`

```text
~/.config/tnh-scholar/
  config.jsonc              # User preferences
  registries/
    pricing-overrides.jsonc  # Local price adjustments
  secrets/
    api-keys.json           # Never committed to git
  cache/                    # Local caches
```

**Characteristics**:

- Machine-local (not version-controlled)
- User-specific preferences
- Safe for experimentation
- Can override workspace settings for user-owned categories
- User-facing directories use hyphen (`tnh-scholar`); underscores are reserved for Python package names

**Discovery**: Via `platformdirs.user_config_dir("tnh-scholar")` for OS-appropriate paths

**Use cases**:

- Personal API keys and credentials
- Local cache directories
- Preferred models and providers
- Logging verbosity preferences
- Cost threshold overrides

---

## Runtime Context Object: `TNHContext`

### Purpose

`TNHContext` represents the **fully resolved operational environment** of TNH Scholar at runtime.

**Responsibilities**:

- Encapsulate discovered roots (built-in, workspace, user)
- Provide resolved configuration views (merged by ownership)
- Expose registry search paths
- Carry runtime metadata (correlation IDs, session info)
- Eliminate reliance on module-level globals

**All subsystems MUST consume configuration via `TNHContext`, not by importing constants.**

---

### TNHContext API (Architecture)

**Class**: `TNHContext` (immutable dataclass)

**Core attributes**:

- `builtin_root: Path` - Package-bundled resources
- `workspace_root: Path | None` - Project-specific config (if discovered)
- `user_root: Path` - OS-standard user config directory
- `correlation_id: str` - Per-invocation tracing ID (from ADR-PV01)
- `session_id: str` - Per-session tracking

**Key methods**:

`TNHContext.discover(workspace_root=None, user_root=None, correlation_id=None) -> TNHContext`

- Class method for context construction
- Auto-discovers workspace root via upward walk (unless overridden)
- Resolves user root via `platformdirs` (unless overridden)
- Generates correlation ID if not provided

`get_config(key: str, ownership: Literal["user", "project", "system"], default=None) -> Any`

- Retrieves configuration value with ownership-based precedence
- `key` uses dotted-path notation (e.g., `"genai.default_model"`)
- `ownership` determines layer precedence order
- Returns resolved value or default

`get_registry_search_paths(registry_type: str) -> list[Path]`

- Returns ordered list of paths for registry type
- Example: `["workspace/.tnh-scholar/registries/providers", "user/registries/providers", "builtin/runtime_assets/registries/providers"]`
- Order respects layer precedence for project-owned data

`get_cache_dir() -> Path`

- Returns user-local cache directory (never workspace)

`get_secrets_dir() -> Path`

- Returns user-local secrets directory (never committed)

`has_workspace() -> bool`

- Checks if workspace context is available

---

### Context Lifecycle

**Discovery (per-invocation)**:

- CLI entry point calls `TNHContext.discover()`
- Auto-discovers workspace root, user root, generates correlation ID
- Passes context to application layer

**Explicit override (testing, custom scenarios)**:

- Tests provide explicit `workspace_root` or `user_root` parameters
- Bypasses auto-discovery for controlled test environments

**Injection into subsystems**:

- Service constructors receive `TNHContext` as dependency
- Services query context for configuration, paths, metadata
- Follows ADR-OS01 dependency injection pattern

---

## Standard Locations Summary

| Layer | Location | Discovery Method | Version Control |
|-------|----------|------------------|-----------------|
| **Built-in** | `<package>/runtime_assets/` | `importlib.resources` | Yes (package) |
| **Workspace** | `<project>/.tnh-scholar/` | Upward walk for `.tnh-scholar/` or `.git/` | Yes (project repo) |
| **User** | OS config dir (via `platformdirs`) | `platformdirs.user_config_dir("tnh-scholar")` | No (local only) |

**Prototype note**: When running from source, `TNHContext` may resolve built-in assets from repo-root directories (e.g., `patterns/`) until `runtime_assets/` is packaged.

**Workspace markers** (in precedence order):

1. `.tnh-scholar/` directory (explicit)
2. `.git/` directory (implicit, stops at repo root)

**Search boundaries**:

- Stop at home directory (don't search system-wide)
- Explicit overrides bypass discovery

---

## Secrets and Credentials

**Critical rule**: Secrets are NEVER merged from JSONC config files.

**Approved secret sources**:

1. **Environment variables** - `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
2. **OS keychain / secret manager** - Platform-specific secure storage
3. **User secrets directory** - `<user_root>/secrets/` (gitignored)

**Forbidden**:

- Secrets in workspace config (would be committed)
- Secrets in JSONC files (plaintext, accident-prone)

**Workspace and user config files MUST remain safe to commit or share.**

---

## Migration Guidance

### For Existing Code

**Legacy pattern (forbidden)**:

- Direct import of module-level constants (`TNH_ROOT`, `DEFAULT_MODEL`)
- Hardcoded path construction from global constants
- Direct environment variable lookups scattered throughout code

**New pattern (required)**:

- Accept `TNHContext` parameter in function/class signatures
- Query context for configuration via `get_config()`
- Query context for paths via `get_registry_search_paths()`, `get_cache_dir()`
- No direct path construction or global constant access

### Incremental Migration Strategy

**Phase 1: Core infrastructure**

- Implement `TNHContext` class
- Add workspace discovery mechanism
- Create config file loaders (JSONC)

**Phase 2: Update new subsystems**

- All NEW code must use `TNHContext`
- No new global constants

**Phase 3: Refactor legacy code**

- Incrementally update existing modules
- Remove global constants one subsystem at a time

**Legacy code may be adapted incrementally—no big-bang rewrite required.**

---

## Integration with ADR-A14 (Registry System)

ADR-A14 defined registry paths but lacked workspace support. This ADR completes the picture:

**ADR-A14 original approach**: Single `registry_root` path in `GenAISettings`

**ADR-CF01 enhancement**:

- `RegistryLoader` receives `TNHContext` instead of single path
- Queries context for multi-layer search paths via `get_registry_search_paths("providers")`
- Searches in order: workspace → user → built-in
- Returns first match found, raises error if not found in any layer

**Breaking changes allowed (see [ADR-PP01: Rapid Prototype Versioning](/architecture/project-policies/adr/adr-pp01-rapid-prototype-versioning.md))**:

- ADR-A14 will be updated to conform to `TNHContext` without backward compatibility
- GenAIService modules will be updated in-place during the rapid prototype phase
- No compatibility shims required for `GenAISettings.registry_root`

---

## Consequences

### Positive

1. **Uniform Mental Model**: All subsystems use same three-layer architecture
2. **Workspace Isolation**: Multiple projects can have separate configs on one machine
3. **No Hardcoded Paths**: Runtime discovery eliminates brittle constants
4. **Testability**: Easy to inject custom context for testing
5. **Familiar Patterns**: VS Code users understand the model immediately
6. **Reproducibility**: Workspace config enables project-specific settings in git
7. **Personal Customization**: User layer supports individual preferences
8. **Editor-Agnostic**: Works in CLI, notebooks, VS Code, PyCharm, etc.
9. **Explicit Precedence**: Ownership-based rules eliminate confusion
10. **ADR-OS01 Compliance**: Dependency injection, no global state

### Negative

1. **Migration Burden**: Existing code using global constants must be refactored
2. **Context Threading**: `TNHContext` must be passed through call chains
3. **Learning Curve**: Developers must understand ownership-based precedence
4. **Additional Complexity**: Three layers more complex than single config file
5. **Discovery Overhead**: Workspace discovery adds minimal startup cost

### Mitigations

- **Migration**: Incremental refactoring, no big-bang rewrite
- **Context Threading**: Use dependency injection at service boundaries
- **Learning Curve**: Clear documentation, examples in ADRs
- **Complexity**: Default behavior requires zero configuration
- **Discovery Overhead**: Cache workspace root after first discovery

---

## Alternatives Considered

### Alternative 1: Single User Config File Only

**Approach**: Only support `~/.config/tnh-scholar/config.yaml`, no workspace layer

**Rejected because**:

- No project-specific configuration (breaks team workflows)
- Can't version-control project settings
- Forces all config into user directory (not reproducible)
- Doesn't support multi-project isolation

### Alternative 2: Environment Variables for Everything

**Approach**: Use `TNH_*` environment variables for all configuration

**Rejected because**:

- Poor discoverability (hidden settings)
- No structured validation (strings only)
- Hard to manage complex nested config
- No support for JSONC comments and IDE tooling

### Alternative 3: Global Config Object Singleton

**Approach**: `from tnh_scholar.config import CONFIG` singleton

**Rejected because**:

- Violates ADR-OS01 (no global state)
- Hard to test (global mutable state)
- No workspace isolation (one config per process)
- Can't have different contexts in same process

### Alternative 4: Per-Subsystem Config Files

**Approach**: Each subsystem manages its own config file separately

**Rejected because**:

- Config fragmentation (genai.json, patterns.json, etc.)
- No unified precedence rules
- Duplicate discovery logic
- Poor user experience (many files to manage)

---

## Open Questions

1. **Config Format**: Should we support YAML in addition to JSONC?
   - **Lean toward**: JSONC only for ecosystem consistency (VS Code, ADR-A14)
   - **Revisit**: If community strongly prefers YAML

2. **Secret Management**: Should we integrate with OS keychains directly?
   - **V1**: Environment variables only
   - **Future**: Consider `keyring` library integration

3. **Config Validation**: How strictly should we validate config files?
   - **Lean toward**: Pydantic validation with clear error messages
   - **Trade-off**: Strict validation vs. forward compatibility

4. **Workspace Marker Precedence**: Should `.tnh-scholar/` always win over `.git/`?
   - **Current proposal**: Yes (explicit marker > implicit)
   - **Alternative**: Make configurable

5. **Multi-Workspace Scenarios**: How to handle monorepos with multiple projects?
   - **V1**: Single workspace root per invocation
   - **Future**: Nested workspace support if needed

6. **Schema Evolution**: How to handle config schema upgrades?
   - **Lean toward**: Schema version field + migration helpers
   - **Defer**: Until we have v1 config schema stabilized

---

## Implementation Plan

### Phase 1: Core Context Infrastructure

- [ ] Implement `TNHContext` class with discovery logic
- [ ] Add workspace root discovery (upward walk algorithm)
- [ ] Integrate `platformdirs` for OS-appropriate user config paths
- [ ] Create JSONC config file loader
- [ ] Unit tests for context discovery and layer precedence

### Phase 2: Configuration Schema

- [ ] Define Pydantic models for config schema
- [ ] Create JSON Schema for VS Code IntelliSense
- [ ] Implement ownership-based precedence resolver
- [ ] Add config validation with clear error messages
- [ ] Document config file format and available options

### Phase 3: Subsystem Integration

- [ ] Update GenAI Service to accept and use `TNHContext`
- [ ] Refactor `RegistryLoader` to use context search paths
- [ ] Update tnh-gen CLI to discover and inject context
- [ ] Migrate pattern system from `TNH_PATTERN_DIR` environment variable to context
- [ ] Remove legacy global constants incrementally (one subsystem at a time)

### Phase 4: Documentation & Tooling

- [ ] Write user guide for three-layer configuration model
- [ ] Document workspace setup and `.tnh-scholar/` structure
- [ ] Create config file examples for common use cases
- [ ] Add VS Code settings schema for `.tnh-scholar/config.jsonc`
- [ ] Update ADRs referencing old configuration patterns

### Phase 5: Testing & Validation

- [ ] Integration tests for multi-layer precedence scenarios
- [ ] Test workspace discovery edge cases (nested git repos, monorepos)
- [ ] Validate secret isolation (never leaked into workspace config)
- [ ] Performance testing for discovery overhead
- [ ] End-to-end testing with sample research projects

---

## Related Documentation

- [ADR-OS01: Object-Service Architecture V3](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md) - Dependency injection requirements
- [ADR-A14: File-Based Registry System](/architecture/gen-ai-service/adr/adr-a14-file-based-registry-system.md) - Registry path configuration
- [ADR-PV01: Provenance & Tracing Infrastructure](/architecture/provenance/adr/adr-pv01-provenance-tracing-strat.md) - Correlation ID context
- [TNH Configuration Management](/architecture/configuration/tnh-configuration-management.md) - Earlier configuration design (superseded)

---

## As-Built Notes & Addendums

*This section will be populated during implementation. Never edit the original Context/Decision/Consequences sections - always append addendums here.*
