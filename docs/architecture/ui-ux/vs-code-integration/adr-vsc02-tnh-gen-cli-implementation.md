---
title: "ADR-VSC02: VS Code Extension Architecture"
description: "VS Code extension architecture for consuming tnh-gen CLI - components, flow of control, and data contracts"
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Sonnet 4.5"
status: accepted
created: "2025-01-28"
updated: "2026-01-02"
---

# ADR-VSC02: VS Code Extension Architecture

This ADR defines the architecture of the VS Code extension that integrates with the `tnh-gen` CLI to provide GenAI-powered text processing capabilities within the editor.

- **Status**: Accepted
- **Date**: 2025-01-28
- **Updated**: 2026-01-02
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, Claude Sonnet 4.5

## Context

TNH Scholar users work primarily in VS Code for text editing and translation workflows. The VS Code extension needs to provide:

1. **Prompt Discovery**: Browse available prompts without leaving the editor
2. **Text Processing**: Execute prompts on selected text or open files
3. **Configuration Management**: Configure prompt directories and GenAI settings
4. **Provenance Tracking**: Show metadata about generated content

### Walking Skeleton Scope

**v0.1.0 includes:**

- TypeScript extension implementation
- Unit and integration tests
- One working command: "Run Prompt on Active File"

**Separate tasks (post-validation):**

- Extension packaging for VS Code Marketplace
- User-facing documentation and guides

### Design Constraints

- **No Direct GenAI Integration**: Extension should not directly call OpenAI/Anthropic APIs
- **CLI as Contract**: Extension consumes `tnh-gen` CLI as stable interface
- **JSON Protocol**: Structured JSON I/O enables programmatic consumption
- **Error Handling**: Extension must gracefully handle CLI errors with user-friendly messages
- **CF01 Compliance**: Configuration resolution follows ADR-CF01 ownership-based precedence; precedence is per-setting (owner category), not a single global order.
- **OS01 Compliance**: Implementation follows the object-service pattern (protocols/abstractions, stateful service objects, and composed collaborators instead of procedural sprawl).

### Related Work

- **[ADR-VSC01: VS Code Integration Strategy](/architecture/ui-ux/vs-code-integration/adr-vsc01-vscode-integration-strategy.md)** - Establishes CLI-based architecture
- **[ADR-TG01: CLI Architecture](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md)** - CLI command structure, error codes, configuration
- **[ADR-TG01.1: Human-Friendly CLI Defaults](/architecture/tnh-gen/adr/adr-tg01.1-human-friendly-defaults.md)** - `--api` flag for machine-readable contract output
- **[ADR-TG02: Prompt System Integration](/architecture/tnh-gen/adr/adr-tg02-prompt-integration.md)** - CLI ↔ prompt system integration patterns
- **[ADR-OS01: Object-Service Architecture](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md)** - Layered design, protocols, separation of concerns
- **[ADR-CF01: Runtime Context Strategy](/architecture/configuration/adr/adr-cf01-runtime-context-strategy.md)** - Configuration discovery and precedence

#### Pattern→Prompt Migration (Pending, Non-Blocking)

The codebase is undergoing a Pattern→Prompt terminology migration (ADR-PT04). Current state:

- **Code**: Still references `TNH_PATTERN_DIR` and `~/.config/tnh_scholar/patterns/`
- **CLI**: `tnh-gen` uses prompt terminology but reads from patterns directory
- **Docs**: Use "prompt" terminology consistently

**Impact on Extension**: None. The extension calls `tnh-gen list/run` via `--api` flag, which abstracts the underlying directory structure. The CLI will continue working during and after the migration.

**Sequencing Strategy**: Pattern→Prompt migration is Priority 1 but deferred until after VS Code extension walking skeleton complete (see TODO.md). This allows:

1. Extension validation without simultaneous major changes
2. Dogfooding: Use working extension to test migrated prompts
3. Risk minimization: Avoid breaking extension during prompt migration

See [ADR-PT04: Prompt System Refactor](/architecture/prompt-system/adr/adr-pt04-prompt-system-refactor.md) for migration details.

## Decision

### 1. Extension Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                   VS Code Extension                         │
│  (TypeScript, VSCode API, UI components)                    │
└────────────────┬────────────────────────┬───────────────────┘
                 │                        │
         ┌───────▼───────┐          ┌──────▼────────┐
         │ CLI Adapter   │          │ UI Components │
         │ (spawn tnh-gen│          │ (prompts list,│
         │  parse JSON)  │          │  progress,    │
         │               │          │  config)      │
         └───────┬───────┘          └───────────────┘
                 │
         ┌───────▼───────┐
         │  tnh-gen CLI  │
         │  (Python)     │
         └───────────────┘
```

### 2. CLI Invocation Strategy

**Architecture:**

The extension spawns `tnh-gen` as a child process and communicates via JSON using the `--api` flag (ADR-TG01.1).

**Component: `TnhGenCliAdapter`**

**Responsibilities:**

- Spawn `tnh-gen` subprocess with appropriate arguments
- Parse JSON responses from stdout
- Handle process lifecycle (spawn, monitor, cleanup)
- Throw structured errors on non-zero exit codes

**Key methods:**

- `listPrompts(options?): Promise<PromptListResponse>` - Invokes `tnh-gen list --api`
- `runPrompt(request): Promise<RunPromptResponse>` - Invokes `tnh-gen run --api`
- `getVersion(): Promise<VersionInfo>` - Invokes `tnh-gen version --api`

**Protocol contract:**

- **Always pass `--api`** flag for machine-readable output
- **Parse stdout as JSON** - Contains response data
- **stderr** - Diagnostics only (warnings, trace IDs, debug info); log to Output channel, not used for UX logic
- **Exit codes** - 0 (success), 1-5 (error categories per ADR-TG01)
- **Success payload schemas** - `ListApiPayload`, `RunSuccessPayload`, `VersionPayload` in `src/tnh_scholar/cli_tools/tnh_gen/types.py:120`
- **Error parsing** - On non-zero exit, attempt JSON parse for structured error; if missing/unparseable, show a generic failure and log stderr tail

### 3. Error Handling

**Component: `CliError`**

**Responsibilities:**

- Parse JSON error responses from CLI stdout (ADR-TG01.1 §3.4)
- Map exit codes to user-friendly messages (ADR-TG01 §5)
- Extract diagnostics and suggestions from structured errors
- Provide fallback messages when JSON parsing fails

**Exit code mapping:**

- **0**: Success
- **1**: Policy error (budget exceeded, validation failed)
- **2**: Transport error (API failure, network issue)
- **3**: Provider error (model unavailable, rate limit)
- **4**: Format error (invalid JSON, schema validation)
- **5**: Input error (invalid arguments, missing variables)

**Error response format (from `--api`):**

```json
{
  "status": "failed",
  "error": "Human-readable error message",
  "diagnostics": {
    "suggestion": "Try X to resolve",
    "trace_id": "correlation-id",
    "exit_code": 2
  }
}
```

**User-facing error display:**

- Show `error` field in VS Code notification
- Optionally append `diagnostics.suggestion` if present
- Log `stderr` and `trace_id` to Output channel for debugging

### 4. Command Flow

**Command: "Run Prompt on Active File":**

**Flow of control:**

1. **Initialize CLI adapter** with configured `tnh-gen` path
2. **Read VS Code settings** (user + workspace)
3. **Resolve effective values** per CF01 ownership for each setting
4. **Build temp config** from effective values and pass `--config <temp.json>` per call
5. **List prompts** via `tnh-gen --api --config <temp.json> list`
6. **Show QuickPick** with prompt metadata (name, description, tags)
7. **Collect required variables** via input boxes (one per required variable from metadata)
8. **Get active document** content and save to temp file
9. **Execute prompt** via `tnh-gen --api --config <temp.json> run` with input file and variables
10. **Parse JSON response** from stdout
11. **Open output file** in split editor pane
12. **Show success notification** with execution metadata (model, cost, time)

**Error handling at each step:**

- CLI spawn failure → show error notification, check CLI installation
- User cancellation → abort silently
- CLI error (non-zero exit) → parse structured error, show user-friendly message
- JSON parse failure → show generic error, log details to Output channel

**Single invocation resolution (summary):**

1. Read VS Code settings (user + workspace)
2. Resolve effective values per CF01 ownership
3. Write temp config JSON
4. Call `tnh-gen --api --config <temp.json> list/run`
5. Render results or errors

### 5. Configuration Management

**Component: `ConfigManager`**

**Responsibilities:**

- Discover candidate `tnh-gen` CLI paths
- Integrate with VS Code Python extension for virtualenv detection
- Manage extension settings via VS Code configuration API
- Materialize a temp `tnh-gen` config file per invocation (no persistent mutation)
- Resolve setting values per CF01 ownership precedence

**Candidate discovery** (for `cliPath`):

1. **Workspace setting** (`tnhScholar.cliPath` in `.vscode/settings.json`)
2. **User setting** (`tnhScholar.cliPath` in global VS Code settings)
3. **Python extension** (detect active interpreter's venv, derive tnh-gen path)
4. **PATH** (fallback to system `tnh-gen`)

**Configuration source**: VS Code settings API only (`.vscode/settings.json` or global settings, JSONC). No separate `tnh-scholar.json` file.

**Settings mapping** (VS Code → `tnh-gen` config):

- `tnhScholar.promptDirectory` → `prompt_catalog_dir`
- `tnhScholar.defaultModel` → `default_model`
- `tnhScholar.maxCostUsd` → `max_dollars`

The adapter writes these to a temp JSON config and passes it via the global `--config` flag (see ADR-TG01, implemented in `src/tnh_scholar/cli_tools/tnh_gen/tnh_gen.py:25`).

**Ownership & precedence** (per ADR-CF01):

| Setting | Ownership | Effective precedence |
| --- | --- | --- |
| `tnhScholar.promptDirectory` | Project-owned | Workspace → User → Built-in |
| `tnhScholar.defaultModel` | User-owned | User → Workspace → Built-in |
| `tnhScholar.maxCostUsd` | User-owned | User → Workspace → Built-in |
| `tnhScholar.cliPath` | Project-owned | Workspace → User → Auto-detect → PATH |

**Rationale for `cliPath` ownership**: Project-owned to keep team workspaces reproducible and avoid per-user drift in multi-user environments.

**Non-duplication rule**: Extension does not read `TNH_*` env vars or infer registry semantics; it writes a temp config and calls `tnh-gen`. Env merging and TNHContext resolution remain inside the CLI per ADR-CF01.

**Component: `CliValidator`**

**Responsibilities:**

- Validate CLI executable existence and executability
- Check minimum version compatibility
- Provide actionable error messages for misconfiguration
- Enforce minimum compatible CLI version via `tnh-gen --api version`

### 6. Extension Configuration Schema

```json
// package.json (contributes.configuration)
{
  "contributes": {
    "configuration": {
      "title": "TNH Scholar",
      "properties": {
        "tnhScholar.cliPath": {
          "type": "string",
          "default": null,
          "description": "Path to tnh-gen CLI executable (auto-detected if not set)"
        },
        "tnhScholar.promptDirectory": {
          "type": "string",
          "default": null,
          "description": "Path to prompt directory (overrides TNH_PROMPT_DIR)"
        },
        "tnhScholar.defaultModel": {
          "type": "string",
          "default": "gpt-4o-mini",
          "description": "Default GenAI model for prompts"
        },
        "tnhScholar.maxCostUsd": {
          "type": "number",
          "default": 0.10,
          "description": "Maximum cost per request (USD)"
        }
      }
    }
  }
}
```

## Consequences

### Positive

- **Stable Contract**: Extension depends only on CLI JSON protocol via `--api` flag, not Python internals
- **Version Independence**: Extension and CLI can evolve independently
- **Error Transparency**: CLI exit codes and structured JSON errors (ADR-TG01.1) enable rich error handling
- **Full Metadata Access**: `--api` provides complete prompt metadata, provenance, usage stats
- **Testability**: CLI can be mocked for extension unit tests
- **Reusability**: CLI implementation (ADR-TG01/TG01.1/TG02) serves both VS Code and command-line users
- **Human-Friendly CLI**: Interactive CLI users get readable output by default, while extension gets full API metadata via `--api`

### Negative

- **Process Overhead**: Spawning Python process for each operation introduces latency (mitigated by keeping CLI operations fast)
- **Version Synchronization**: Extension must validate CLI version compatibility
- **Error Mapping**: Extension must parse CLI JSON errors and present user-friendly messages

### Risks

- **CLI Path Discovery**: Auto-detection may fail in complex Python environments (mitigated by explicit configuration)
- **Breaking Changes**: CLI protocol changes require coordinated extension updates (mitigated by semantic versioning)

## Alternatives Considered

### Alternative 1: Direct Python Integration (via Python Extension)

**Approach**: Extension imports TNH Scholar Python modules directly via VS Code Python extension API.

**Rejected**: Tight coupling to Python implementation. Extension would need to handle Python environment activation, dependency resolution, and version compatibility.

### Alternative 2: Language Server Protocol (LSP)

**Approach**: Create TNH Scholar language server that VS Code extension communicates with via LSP.

**Rejected**: Overengineering for initial MVP. LSP is designed for language features (completion, diagnostics), not GenAI operations.

### Alternative 3: REST API

**Approach**: Run TNH Scholar as HTTP server, extension makes REST calls.

**Rejected**: Adds complexity (server lifecycle management, port conflicts). CLI spawn model is simpler for single-user desktop usage.

## Open Questions

1. **Streaming Support**: How should extension handle streaming CLI output (future `--streaming` flag)?
2. **Multi-Root Workspaces**: How to handle different prompt directories per workspace folder?
3. **Offline Mode**: Should extension cache prompt list to avoid repeated CLI calls?

## Next Increment (Post v0.1.0)

- Add an optional pre-run UI to override a small subset of user-owned settings (e.g., model, max cost) for that invocation only.
- Overrides are ephemeral: written into the temp config and never persisted to VS Code settings.

## References

### Related ADRs

- **[ADR-VSC01: VS Code Integration Strategy](/architecture/ui-ux/vs-code-integration/adr-vsc01-vscode-integration-strategy.md)** - Overall VS Code strategy
- **[ADR-TG01: CLI Architecture](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md)** - CLI command structure, error codes, configuration
- **[ADR-TG01.1: Human-Friendly CLI Defaults](/architecture/tnh-gen/adr/adr-tg01.1-human-friendly-defaults.md)** - `--api` flag for machine-readable contract output
- **[ADR-TG02: Prompt System Integration](/architecture/tnh-gen/adr/adr-tg02-prompt-integration.md)** - CLI ↔ prompt system integration
- **[ADR-AT03: AI Text Processing Refactor](/architecture/ai-text-processing/adr/adr-at03-object-service-refactor.md)** - ai_text_processing refactor

### External Resources

- [VS Code Extension API](https://code.visualstudio.com/api)
- [VS Code Python Extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- [Typer CLI Framework](https://typer.tiangolo.com/)

---

## Changelog

### 2025-12-27: Updated for ADR-TG01.1 `--api` flag

- Changed all CLI invocations to use `--api` flag (replacing earlier `--verbose` design)
- `--api` is the machine-readable API contract mode for structured output (ADR-TG01.1)
- Updated error handling to parse structured JSON errors from `--api` mode
- Updated version checking to use `--api` flag
- Added reference to ADR-TG01.1 in Related Work and References sections
- Interactive CLI users now get human-friendly output by default
- Extension receives full API metadata via `--api` flag
- This is a breaking change from the initial `--verbose` design, done while ADR is still in proposed status

---

*This ADR focuses on VS Code extension architecture. CLI implementation details are defined in ADR-TG01, ADR-TG01.1, and ADR-TG02.*
