---
title: "ADR-VSC01: VS Code Integration Strategy (TNH-Scholar Extension v0.1.0)"
description: "Strategy ADR defining a CLI-first VS Code integration built on the unified tnh-gen interface for extension v0.1.0."
owner: "UI/UX Working Group"
author: "Aaron Solomon"
status: accepted
created: "2025-01-28"
updated: "2026-01-02"
---
# ADR-VSC01: VS Code Integration Strategy (TNH-Scholar Extension v0.1.0)

Defines the CLI-first integration strategy for the TNH-Scholar VS Code extension v0.1.0, using `tnh-gen` as the sole interface into GenAI Service capabilities.

- **Status:** Accepted
- **Date:** 2025-01-28
- **Updated:** 2026-01-02
- **Owner:** UI/UX Working Group
- **Author:** Aaron Solomon
- **Tags:** strategy, vscode, genai, architecture, integration
- **Context:** Long-term TNH-Scholar UX roadmap; GenAIService maturity; PromptCatalog stability.
- **Related ADRs:** [GenAI Service Strategy](/architecture/gen-ai-service/design/genai-service-design-strategy.md), [UI/UX Strategy: VS Code as Platform](/architecture/ui-ux/design/vs-code-as-ui-platform.md)

---

## 1. Context

TNH-Scholar is evolving into a multi-layer system with:

- a structured corpus,
- data-processing pipelines,
- a pattern/prompt-driven GenAIService,
- provenance-first transformations,
- and a growing collection of CLI tools and automation flows.

A next logical frontier is **developer-facing integration** within **VS Code**, enabling:

- fast interaction with patterns,
- file-level and selection-level transformations,
- agent-assisted workflows,
- clearer UX pathways for developers, researchers, and contributors,
- and eventually: semi-autonomous loops for corpus processing or code maintenance.

This ADR establishes the **strategic foundation** for VS Code integration and describes the intended shape of v0.1.0 of the TNH-Scholar VS Code Extension.

It is **not** an implementation ADR — it defines the approach, boundaries, responsibilities, and rationale behind the first integration.

### **1.1 Relationship to GenAI Service**

The GenAI Service (see [GenAI Service Strategy](/architecture/gen-ai-service/design/genai-service-design-strategy.md)) provides:

- Pattern-driven transformations via `GenAIService.generate()`
- Rich domain model (`RenderRequest`, `CompletionEnvelope`, `PromptCatalog`)
- Provenance tracking, fingerprinting, policy enforcement
- Model routing, cost estimation, observability

The VS Code extension is a **consumer** of GenAI Service capabilities, not a reimplementation. The CLI acts as a **transport adapter**, exposing GenAI Service functionality through a stable command-line interface.

---

## 2. Problem / Motivation

Developers and contributors currently:

- run patterns via scattered CLI tools (`tnh-fab`, domain-specific scripts) or Python directly,
- manually open and inspect results,
- must jump between terminal + editor + documentation,
- have no discoverability for the PromptCatalog,
- cannot easily apply transformations to the currently open file or selection,
- lack real-time feedback during long-running operations.

Desired improvements:

1. **Simple UX slice:**
   Selecting a prompt → running it → producing an output file → opening it automatically.

2. **Discoverability:**
   QuickPick-like interfaces to browse prompt metadata (names, descriptions, tags, required variables).

3. **Developer ergonomics:**
   Minimize friction; enable quick prototyping and evaluation of patterns.

4. **Clear architecture seam:**
   VS Code should be a thin client — not aware of Python internals — and communicate via well-defined, stable interfaces.

5. **Long-term extensibility:**
   Future support for:
   - selections and inline replacements,
   - streaming token-by-token output,
   - multi-file batch operations,
   - progress feedback for long operations,
   - agent-assisted loops,
   - fully autonomous flows.

This ADR sets the direction for achieving these goals.

---

## 3. Decision

### **3.1 Core Architectural Boundary: CLI-First Integration**

The VS Code Extension will communicate with TNH-Scholar **exclusively via a unified CLI interface** in v0.1.0.

The extension will **not**:

- import Python modules directly,
- embed Python interpreters,
- run Python LSP servers,
- invoke TNH-Scholar internals through ad hoc mechanisms.

Instead, we define a **stable CLI integration seam** using the new `tnh-gen` command-line tool.

**Rationale:**

- **Simplicity**: CLI is the fastest path to shipping a working integration.
- **Stability**: Isolates VS Code from Python implementation changes.
- **Testability**: CLI can be tested independently of the extension.
- **Replaceability**: Future transports (HTTP, MCP) can be added without breaking the extension contract.

---

### **3.2 The `tnh-gen` CLI Tool**

`tnh-gen` is a **new, unified CLI** that:

- **Replaces** the legacy `tnh-fab` CLI and scattered domain-specific scripts.
- **Wraps** the GenAI Service, exposing its rich feature set via command-line interface.
- **Serves** as the public contract for VS Code integration.

**Design Principles:**

1. **GenAI Service parity**: Match the GenAI Service's capabilities as closely as possible.
2. **Flexible variable passing**: Support both JSON file and inline parameter styles.
3. **Rich metadata**: Expose PromptCatalog metadata for discoverability.
4. **Structured output**: JSON-formatted responses for programmatic consumption.
5. **Error taxonomy**: Clear exit codes and error messages aligned with GenAI Service error types.

---

### **3.3 The `tnh-gen` CLI: Core Capabilities**

The `tnh-gen` CLI provides three primary commands:

#### **`tnh-gen list`** - Discover Prompts

Lists all available prompts with rich metadata (names, descriptions, tags, required variables).

```bash
tnh-gen list --api
```

Enables VS Code extension to build dynamic QuickPick interfaces without hardcoding prompt metadata.

#### **`tnh-gen run`** - Execute Patterns

Executes a prompt pattern with flexible variable passing:

```bash
# Inline variables (with --api for VS Code)
tnh-gen run --api --prompt translate \
  --input-file teaching.md \
  --var source_lang=vi \
  --var target_lang=en

# JSON file variables (with --api for VS Code)
tnh-gen run --api --prompt translate \
  --input-file teaching.md \
  --vars variables.json
```

**Key Features:**

- Supports both JSON file and inline parameter styles
- Auto-injects file content as `input_text` variable
- With `--api`: Outputs structured JSON for programmatic consumption
- Provides clear exit codes for error handling (0-5 per ADR-TG01)
- Generates provenance markers in output files (YAML frontmatter)

#### **`tnh-gen config`** - Manage Configuration

Configuration discovery with precedence: CLI flags > workspace > user > environment > defaults.

```bash
tnh-gen config show
tnh-gen config set max_dollars 0.25
```

**See ADR-VSC02 for complete CLI implementation details** (command signatures, output schemas, error handling, etc.).

---

### **3.4 VS Code Extension Commands (v0.1.0)**

The extension provides minimal commands that wrap `tnh-gen`:

#### Command 1: "TNH Scholar: Run Prompt on Active File"

Workflow:

1. Execute `tnh-gen list --api`
2. Show QuickPick with prompt names + descriptions
3. For selected prompt, show input form for required variables
4. Save active document to a temp file, then execute `tnh-gen run --api --prompt <key> --input-file <temp_file> --vars <temp.json>`
5. Parse JSON response
6. Write output to `<basename>.<prompt_key>.<ext>`
7. Open output file in split editor

#### Command 2: "TNH Scholar: Refresh Prompt Catalog"

- Re-executes `tnh-gen list --api`
- Clears extension cache
- Shows notification with prompt count

This is a **walking skeleton**: minimal, end-to-end, testable.

---

### **3.5 Output Strategy (v0.1.0)**

**File Naming:**

Never overwrite the original file. Use deterministic naming:

```plaintext
<basename>.<prompt_key>.<ext>

Examples:
  teaching.md → teaching.translate.md
  teaching.md → teaching.summarize.md
  notes.txt → notes.extract_quotes.txt
```

**Provenance Markers:**

GenAI Service automatically prepends provenance metadata to output files as YAML frontmatter:

```yaml
---
provenance:
  pattern: translate
  version: "1.0"
  model: gpt-4o
  fingerprint: "sha256:abc123..."
  correlation_id: "01HQXYZ123ABC"
  generated: "2025-01-28T10:30:03Z"
---

[Generated content follows...]
```

**Editor Integration:**

- Open output file automatically in split editor (right pane)
- Keep original file focused (left pane)
- Enable side-by-side comparison

**Future:** Diff view, inline replacements, overwrite confirmations (v0.2.0+).

---

### **3.6 Error Handling**

**VS Code Extension Error Display:**

| Error Type      | Display Method                                                      |
|-----------------|---------------------------------------------------------------------|
| Policy Error | Error notification with budget/limit details |
| Transport Error | Error notification + "Check API key" hint |
| Provider Error | Error notification + "Try different model" hint |
| Format Error | Warning notification + save partial output with `.partial` suffix |

**Partial Results:**

If JSON parsing fails but text is available:

- Save to `<basename>.<prompt_key>.partial.<ext>`
- Show warning notification
- Log full error to extension output channel

**Logging:**

All CLI invocations and responses are logged to the "TNH Scholar" output channel for debugging.

---

### **3.7 PromptCatalog Metadata Source of Truth**

PromptCatalog (via `PromptsAdapter`) remains the **only authoritative source** for:

- Prompt keys and versions
- Human-readable names and descriptions
- Tags and categorization
- Required/optional variables
- Recommended filetypes
- Default model hints
- Expected output modes (text/json)

The extension must **never duplicate** prompt metadata. All metadata is fetched dynamically via `tnh-gen list`.

**Note:** PromptCatalog metadata schema is defined in [ADR-TG02](/architecture/tnh-gen/adr/adr-tg02-prompt-integration.md).

---

### **3.8 Workspace Configuration Discovery**

For v0.1.0, the extension assumes `tnh-gen` is on `$PATH`.

**Configuration Sources (per ADR-CF01):**

```json
// .vscode/settings.json (workspace-level)
{
  "tnhScholar.cliPath": "/path/to/tnh-gen",
  "tnhScholar.promptDirectory": "./prompts",
  "tnhScholar.defaultModel": "gpt-4o-mini",
  "tnhScholar.maxCostUsd": 0.10
}
```

**Future (v0.2.0+):**

- Auto-detect Poetry virtualenv
- Discover in-project venv
- Fallback to system Python

See [ADR-CF01](/architecture/configuration/adr/adr-cf01-runtime-context-strategy.md) for detailed configuration strategy.

---

## 4. Rationale

### **4.1 Stability**

The CLI boundary isolates VS Code from Python implementation changes. The GenAI Service can refactor internals without breaking the extension.

### **4.2 Replaceability**

The CLI is the **v0.1.0 transport**. Future versions can add:

- **HTTP/FastAPI service** (v0.2.0) for streaming, progress updates, session management
- **Hybrid approach** (v1.0.0) with HTTP preferred, CLI fallback
- **MCP integration** (v2.0.0+) for agent-native workflows

The extension can auto-detect and prefer faster transports while maintaining CLI compatibility.

### **4.3 Discoverability & UX**

Developers can browse prompt metadata without manual file digging. The QuickPick interface surfaces:

- Human-readable names (not just file paths)
- Descriptions (understanding prompt purpose)
- Tags (finding related patterns)
- Required variables (knowing what inputs are needed)

### **4.4 Future-Agent Compatibility**

Agent loops require:

- Explicit boundaries (CLI provides clear input/output contract)
- Reproducible inputs/outputs (provenance + fingerprinting)
- Structured error handling (status envelopes + diagnostics)

The CLI seam provides all three and maps cleanly to future MCP/agent protocols.

### **4.5 GenAI Service Parity**

By matching GenAI Service's feature set (`tnh-gen` as a thin wrapper), we:

- Avoid impedance mismatch between Python API and CLI
- Enable future features (streaming, batch, policy overrides) without redesign
- Maintain consistency across consumption patterns (Python, CLI, VS Code)

### **4.6 Unified CLI (`tnh-gen` replaces `tnh-fab`)**

Consolidating scattered CLI tools into `tnh-gen`:

- Reduces cognitive load (one tool to learn vs. many)
- Simplifies documentation and onboarding
- Provides consistent UX across all GenAI operations
- Enables future expansion (corpus management, validation, etc.)

---

## 5. Alternatives Considered

### **5.1 Embedding Python in the extension** ❌

**Approach:** Use `python-shell` or `pyodide` to call GenAI Service directly from Node.js.

**Rejected because:**

- Too fragile (Python environment discovery, virtualenv management)
- Platform-specific issues (different Python versions, missing dependencies)
- Not web-compatible (can't run in vscode.dev)
- High maintenance burden

### **5.2 Language Server Protocol (LSP)** ❌

**Approach:** Implement TNH-Scholar as a language server.

**Rejected because:**

- Protocol mismatch: LSP is designed for language features (diagnostics, hover, completion), not general compute
- Heavyweight: Requires persistent server + complex protocol implementation
- Limited discoverability: LSP doesn't have primitives for "list all patterns" or "apply transformation"
- Over-engineering for v0.1.0 needs

### **5.3 Direct HTTP service (v0.1.0)** ⏸️

**Approach:** Launch FastAPI service, have extension call HTTP endpoints.

**Deferred to v0.2.0 because:**

- Adds daemon management complexity
- Requires port management, health checks
- Higher setup friction for users
- CLI is simpler and sufficient for initial validation

**Note:** HTTP service is planned for v0.2.0 (see ADR-VSC02).

### **5.4 Direct Node <-> Python RPC** ❌

**Approach:** Custom IPC/socket protocol between extension and Python service.

**Rejected because:**

- Adds unnecessary coupling
- Reinvents HTTP without benefits
- Harder to test and debug than standard protocols

---

## 6. Impact

### **On developers**

✅ **Benefits:**

- Easy access to GenAI patterns from editor
- Intuitive prompt discovery and selection
- Automatic file handling and provenance
- Reduced context switching (terminal ↔ editor)

⚠️ **Considerations:**

- Must have `tnh-gen` installed and on PATH
- Initial setup requires API key configuration

### **On codebase**

✅ **Required Work:**

- Implement `tnh-gen` CLI (new)
- Expand `PromptsAdapter.introspect()` for rich metadata
- Define PromptCatalog metadata schema
- Create VS Code extension scaffold

♻️ **Refactoring:**

- Migrate `tnh-fab` functionality to `tnh-gen`
- Deprecate legacy CLI tools

### **On documentation**

📚 **New Docs Required:**

- `tnh-gen` CLI reference
- VS Code extension user guide
- Configuration guide
- Prompt authoring guide (for catalog contributors)

---

## 7. Phased Transport Evolution

This ADR defines **v0.1.0** using CLI. Future versions will evolve the transport:

### **v0.1.0: CLI (Current ADR)** ✅

- **Transport:** `tnh-gen` CLI subprocess
- **Goal:** Ship walking skeleton, validate UX
- **Scope:** TypeScript extension + unit/integration tests
- **Capabilities:** Basic file transformations, prompt discovery
- **Documentation/Packaging:** Separate task after walking skeleton validation

### **v0.2.0: Add HTTP Service** 🔄

- **Transport:** FastAPI HTTP service (preferred) + CLI fallback
- **Goal:** Rich UX with streaming, progress, sessions
- **Capabilities:** Token-by-token output, real-time progress, conversation history
- **See:** ADR-VSC02 for HTTP service design

### **v1.0.0: Hybrid (HTTP + CLI)** 🎯

- **Transport:** Auto-detect HTTP, gracefully fall back to CLI
- **Goal:** Best UX when service available, always works offline
- **Capabilities:** Full feature parity across transports

### **v2.0.0+: MCP Integration** 🔮

- **Transport:** Model Context Protocol for agent-native workflows
- **Goal:** Enable semi-autonomous corpus processing loops
- **Capabilities:** Multi-step agent chains, approval gates, batch orchestration
- **Timing:** Evaluate when MCP ecosystem matures (2026+)

---

## 8. Prerequisites & Dependencies

Before implementing the VS Code extension, these must be completed:

### **P0: Blocking**

1. **Implement `tnh-gen` CLI** ✅ COMPLETE
   - **ADR**: [ADR-TG01](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md), [ADR-TG01.1](/architecture/tnh-gen/adr/adr-tg01.1-human-friendly-defaults.md)
   - Wrap GenAI Service with CLI interface
   - Support JSON and inline variable passing (`--api` flag)
   - Add to Poetry scripts as entry point
   - **Status**: Implemented (v0.2.2+)

2. **Define PromptCatalog Metadata Schema** ✅ COMPLETE
   - **ADR**: [ADR-TG02](/architecture/tnh-gen/adr/adr-tg02-prompt-integration.md)
   - Formalize metadata fields (name, description, tags, required_variables, optional_variables)
   - Extend `PromptsAdapter.introspect()` to return metadata
   - Create metadata validation
   - **Status**: Implemented in tnh-gen CLI

3. **Define Configuration Strategy** ✅ COMPLETE
   - **ADR**: [ADR-TG01](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md) §4 (Configuration)
   - Specify config file formats and locations
   - Define precedence rules (CLI flags > workspace > user > env > defaults)
   - Handle API key discovery and secrets management
   - **Status**: Implemented in tnh-gen CLI

### **P1: High Priority**

1. **Create Error Taxonomy Mapping**
   - Map GenAI Service errors to CLI exit codes
   - Define JSON error response schema
   - Document error handling best practices

2. **Define Output File Format Strategy**
   - Specify provenance marker format
   - Define file extension mapping rules
   - Handle special cases (JSON output, binary formats)

---

## 9. Follow-up ADRs

The following ADRs will detail implementation:

### **ADR-TG01: `tnh-gen` CLI Architecture** ✅ Implemented

**Status:** Implemented (see [ADR-TG01](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md))

**Satisfied prerequisites:**
- CLI implementation with `--api` flag for machine-readable output
- Configuration strategy (precedence, file formats, API keys)
- Error handling and exit codes (0-5 taxonomy)
- Provenance generation

### **ADR-TG01.1: Human-Friendly CLI Defaults** ✅ Implemented

**Status:** Implemented (see [ADR-TG01.1](/architecture/tnh-gen/adr/adr-tg01.1-human-friendly-defaults.md))

**Satisfied prerequisites:**
- `--api` flag for VS Code integration (JSON output)
- Human-friendly defaults for interactive use

### **ADR-TG02: Prompt System Integration** ✅ Implemented

**Status:** Implemented (see [ADR-TG02](/architecture/tnh-gen/adr/adr-tg02-prompt-integration.md))

**Satisfied prerequisites:**
- PromptCatalog metadata schema (required_variables, optional_variables, tags, etc.)
- PromptsAdapter integration
- Variable precedence rules

### **ADR-VSC02: VS Code Extension Architecture** 🟡 Proposed

**Status:** Proposed (see [adr-vsc02-tnh-gen-cli-implementation.md](/architecture/ui-ux/vs-code-integration/adr-vsc02-tnh-gen-cli-implementation.md))

**Scope:** TypeScript extension architecture consuming tnh-gen CLI

### **ADR-VSC05: VS Code Extension Implementation** 🟢 Future

**Scope:**

- Extension architecture and command structure
- QuickPick UI implementation
- Variable input forms (dynamic based on prompt metadata)
- File output handling and editor integration
- Error display and notification strategy
- Extension settings and preferences
- Testing strategy (unit, integration, E2E)

### **ADR-VSC06: HTTP Service for Rich UX** 🟢 Future (v0.2.0)

**Scope:**

- FastAPI service architecture
- API endpoint design (REST, SSE for streaming)
- Auto-start mechanism from VS Code extension
- Health checks and daemon management
- Session management for multi-turn conversations
- Hybrid transport strategy (HTTP preferred, CLI fallback)

### **ADR-VSC07: Selection-Level Transformations** 🟢 Future (v0.3.0)

**Scope:**

- Inline text replacement
- Diff view and preview
- Undo/redo integration
- Multi-cursor support

### **ADR-VSC08: Batch & Multi-File Operations** 🟢 Future (v0.4.0)

**Scope:**

- Bulk pattern application
- Progress tracking
- Cancellation and retry
- Result aggregation

### **ADR-VSC09: Agent-Assisted Workflows** 🔮 Future (v2.0.0+)

**Scope:**

- MCP integration
- Approval gates and human-in-the-loop
- Semi-autonomous corpus processing
- Audit logging and provenance chains

---

## 10. Decision Summary

TNH-Scholar will integrate with VS Code via a **minimal, stable CLI boundary** using the new **`tnh-gen`** unified CLI tool.

**v0.1.0 Walking Skeleton:**

- `tnh-gen list` — Discover prompts with rich metadata
- `tnh-gen run` — Execute patterns with flexible variable passing
- `tnh-gen config` — Manage configuration

**Key Principles:**

- ✅ CLI-first for simplicity (v0.1.0)
- ✅ GenAI Service feature parity (match rich domain model)
- ✅ Flexible variable passing (JSON file + inline params)
- ✅ Rich error handling (structured responses, exit codes)
- ✅ Provenance-first (automatic markers, fingerprinting)
- ✅ Transport evolution path (CLI → HTTP → Hybrid → MCP)
- ✅ Unified CLI (`tnh-gen` replaces `tnh-fab`)

The extension acts as a **thin client**, delegating all GenAI logic to the CLI/service layer.

---

## 11. Acceptance Criteria (v0.1.0)

**CLI Implementation:**

- [x] `tnh-gen list --api` returns prompt metadata ✅ (ADR-TG01.1)
- [x] `tnh-gen run` supports JSON file variable passing ✅ (ADR-TG02)
- [x] `tnh-gen run` supports inline `--var` parameter passing ✅ (ADR-TG02)
- [x] `tnh-gen run` injects `--input-file` content as variable ✅ (ADR-TG02)
- [x] CLI outputs structured JSON with `--api` flag ✅ (ADR-TG01.1)
- [x] CLI exits with appropriate error codes (0-5) ✅ (ADR-TG01)
- [x] CLI respects configuration precedence ✅ (ADR-CF01)
- [x] `tnh-gen` is installable via Poetry scripts ✅ (v0.2.2+)

**VS Code Extension:**

- [ ] "Run Prompt on Active File" command works end-to-end
- [ ] QuickPick shows prompt names + descriptions
- [ ] Variable input form dynamically adapts to selected prompt
- [ ] Output file opens automatically in split editor
- [ ] Errors display user-friendly notifications
- [ ] Extension logs CLI invocations to output channel
- [ ] Extension respects workspace configuration

**Documentation:**

- [ ] `tnh-gen` CLI reference published
- [ ] VS Code extension user guide published
- [ ] Configuration guide published
- [ ] Migration guide from `tnh-fab` published

---

## 12. Status

**Current:** Proposed (awaiting approval)

**Prerequisites Complete:**

1. ✅ ADR-TG01: `tnh-gen` CLI architecture (implemented v0.2.2+)
2. ✅ ADR-TG01.1: `--api` flag for machine-readable output (implemented)
3. ✅ ADR-TG02: Prompt system integration (implemented)
4. ✅ ADR-CF01: Configuration strategy (accepted)

**Next Steps:**

1. 🟡 Review and approve ADR-VSC01 (this document) + ADR-VSC02
2. 🟡 Implement VS Code extension (walking skeleton)
3. 🟢 Ship v0.1.0

---

## Appendix: Example Workflow

**User Story:** Developer wants to translate a Vietnamese teaching to English.

1. Open `teaching.md` in VS Code
2. Cmd+Shift+P → "TNH Scholar: Run Prompt on Active File"
3. QuickPick shows:

   ```text
   Vietnamese-English Translation
   Translate Vietnamese dharma texts to English
   Tags: translation, dharma
   ```

4. User selects "Vietnamese-English Translation"
5. Extension shows input form:

   ```text
   Source Language: [vi]
   Target Language: [en]
   Context (optional): [Dharma talk on mindfulness]
   ```

6. User fills form, clicks "Run"
7. Extension executes:

   ```bash
   tnh-gen run --api --prompt translate \
     --input-file teaching.md \
     --var source_lang=vi \
     --var target_lang=en \
     --var context="Dharma talk on mindfulness"
   ```

8. Output file `teaching.translate.md` opens in split pane with provenance header
9. Success notification: "Translation completed (gpt-4o, $0.08, 3.4s)"

**Developer experience:** 10 seconds from intent to result, zero context switching.
