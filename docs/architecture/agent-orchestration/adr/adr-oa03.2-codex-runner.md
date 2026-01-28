---
title: "ADR-OA03.2: Codex Runner"
description: "Codex execution path — API-first, tool-driven runner for implementation tasks"
owner: "aaronksolomon"
author: "Aaron Solomon, GPT 5.2, Claude Opus 4.5"
status: paused
created: "2026-01-22"
updated: "2026-01-22"
parent_adr: "adr-oa03-agent-runner-architecture.md"
---

# ADR-OA03.2: Codex Runner

Codex execution path for tnh-conductor — an API-first, tool-driven runner optimized for implementation and mechanical coding tasks.

- **Status**: Paused
- **Date**: 2026-01-22
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, GPT 5.2, Claude Opus 4.5
- **Parent ADR**: [ADR-OA03](/architecture/agent-orchestration/adr/adr-oa03-agent-runner-architecture.md)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

OA03 establishes the runner architecture: a shared kernel handling cross-agent invariants, with per-agent adapters handling surface-specific mechanics. This ADR specifies the **Codex runner adapter**.

### What is Codex?

**Codex** refers to OpenAI's GPT-Codex model family — specialized versions of GPT models optimized for agentic coding tasks. These are accessed via the standard OpenAI Responses API.

**Available GPT-Codex models:**

- `gpt-5.2-codex` — Most advanced agentic coding model
- `gpt-5.1-codex` / `gpt-5.1-codex-max` — Project-scale work with context compaction
- `gpt-5-codex` / `gpt-5-codex-mini` — Standard and cost-effective variants
- `codex-mini-latest` — Low-latency, optimized for code Q&A and editing

These are first-class models in the OpenAI API, not a separate product. The runner invokes them via the Responses API with tool definitions.

### Codex Positioning

Codex is positioned as the **primary engine for code implementation tasks**:

| Task Type | Preferred Agent | Rationale |
|-----------|-----------------|-----------|
| Implementation (new features, ADR execution) | **Codex** | Strong reasoning, large context, structured output |
| Exploratory / refactoring | Claude Code | Filesystem-native, interactive exploration |
| Code review / analysis | Claude Code | Conversational, nuanced assessment |
| Documentation | Either | Task-dependent |

This division reflects each agent's strengths, not a hard constraint. The Planner may route tasks based on capability metadata.

### Why Not the VS Code Extension?

Codex offers a VS Code extension with rich IDE integration. We explicitly **do not** attempt to drive or replicate this:

- Rebuilding IDE semantics is out of scope and unnecessary
- Codex's strength comes from reasoning + large context, not UI interactivity
- Tool-driven Codex recovers most IDE affordances with far lower complexity
- Aligns with prompt-program runtime model: behavior defined in prompts, execution via kernel + tools

---

## Decision

### Execution Model

Codex is invoked **headlessly via API**, not via VS Code extension and not via PTY.

```
TaskSpec + RepoSnapshot + Policy
        ↓
   Codex (Responses API)
        ↓
 Structured Output (patch + reasoning)
```

**Execution constraints:**

| Constraint | Value | Rationale |
|------------|-------|-----------|
| Single-shot execution | Per step | No multi-turn within a step |
| Clarifying questions | Disallowed | Must emit output or block |
| Conversational memory | None | Stateless per invocation |
| Parameters | Deterministic | Set by workflow, not runtime negotiation |

### Core Principle

> Expose the minimum viable IDE as explicit tools. No implicit workspace access.

Codex receives workspace context only through explicit tool calls. This makes all workspace interaction auditable and policy-enforceable.

---

## Tool Surface Contract

### Required Tools (v1)

| Tool | Signature | Purpose |
|------|-----------|---------|
| `read_file` | `read_file(path: str) -> str` | Read file contents |
| `search_repo` | `search_repo(query: str) -> list[Match]` | Search codebase (grep-like) |
| `list_files` | `list_files(path: str) -> list[str]` | List directory contents |
| `apply_patch` | `apply_patch(diff: str) -> PatchResult` | Apply unified diff |
| `run_tests` | `run_tests(command: str) -> TestResult` | Execute test command |

### Non-Goals (Explicit Exclusions)

| Exclusion | Rationale |
|-----------|-----------|
| Terminal emulation | Not needed; tools provide structured access |
| Interactive retries | Single-shot model; retry is Planner's decision |
| Hidden filesystem state | All access via explicit tools |
| UI events | No VS Code extension integration |

### Tool Policy Enforcement

Tools are subject to `RunPolicy` constraints:

- `read_file` / `list_files` — restricted to allowed paths
- `apply_patch` — diff checked against forbidden paths before application
- `run_tests` — command validated against allowed test commands

Policy violations result in tool call rejection, not step failure. Codex may retry with different parameters.

---

## Output Contract

Codex must emit **schema-validated structured output**:

```yaml
# Codex step output schema
output:
  patch: str | null          # Unified diff or null if no changes
  file_operations: list      # Create/delete/rename operations
    - operation: "create" | "delete" | "rename"
      path: str
      content: str | null    # For create only
      target: str | null     # For rename only
  rationale: str             # Why this change addresses the task
  risk_flags: list[str]      # Concerns requiring attention
  open_questions: list[str]  # If blocked, what needs clarification
  status: "complete" | "partial" | "blocked"
```

### Output Validation Rules

| Condition | Result |
|-----------|--------|
| Valid schema, `status: complete` | Kernel applies patch, marks step complete |
| Valid schema, `status: partial` | Kernel applies patch, Planner decides next step |
| Valid schema, `status: blocked` | No patch applied, Planner evaluates blockers |
| Invalid schema | Step marked `unsafe`, no changes applied |
| No output (timeout) | Step marked `blocked`, reason `timeout` |

**Failure to emit valid structure → step marked `unsafe`.**

---

## Kernel Integration

### Adapter Responsibilities

The Codex runner adapter handles:

| Responsibility | Implementation |
|----------------|----------------|
| API invocation | Codex Responses API with tool definitions |
| Tool execution | Dispatch tool calls to kernel utilities |
| Output parsing | Validate against schema, extract artifacts |
| Event emission | Translate API events to kernel event stream |

### Kernel Responsibilities (Unchanged from OA03)

| Responsibility | Description |
|----------------|-------------|
| Workspace isolation | Git worktree setup before Codex invocation |
| Pre/post capture | Git status + diff before and after |
| Patch application | Apply validated diff from Codex output |
| Policy enforcement | Check diff against RunPolicy |
| Provenance recording | Write run record with all artifacts |

### Dual-Channel Output

Consistent with OA01/OA03, Codex produces dual-channel output:

| Channel | Content | Source |
|---------|---------|--------|
| **Workspace** | Proposed diff, file operations | `patch`, `file_operations` fields |
| **Semantic** | Reasoning, risk assessment | `rationale`, `risk_flags`, `open_questions` |

The Planner consumes both channels for evaluation. Contradictions (e.g., `status: complete` but empty patch for implementation task) trigger `partial` or `unsafe` classification.

---

## Control Surface Mapping

**Required by OA03 ADR Gate.**

### Authoritative Documentation

- Codex Models: [OpenAI GPT-5-Codex](https://platform.openai.com/docs/models/gpt-5-codex)
- Responses API: [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses)
- Codex Overview: [OpenAI Codex](https://openai.com/codex/)

### Invocation Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| Responses API | Stateless, tool-enabled | Primary execution mode |
| Chat Completions | Multi-turn, no native tools | Not used |

### IO Model

- **Stateless**: Each invocation is independent
- **No session persistence**: Context provided per-call via system prompt + tools
- **Structured output**: JSON schema enforcement available

### Permission / Safety Controls

| Control | Mechanism |
|---------|-----------|
| Tool restriction | Only declared tools available |
| Output schema | Enforced via API response_format |
| Token limits | Set per invocation |
| No network access | Tools don't expose network operations |

### Output Formats

- JSON (structured output mode)
- Tool calls (function calling format)

### Experiment Matrix

| Test Case | Expected Result |
|-----------|-----------------|
| Simple file read | Returns file content |
| Search repo | Returns matching locations |
| Apply valid patch | Patch applied successfully |
| Apply patch to forbidden path | Tool call rejected |
| Invalid output schema | Step marked unsafe |
| Timeout | Step marked blocked |

**Validation requirement:** All test cases must pass before moving to `accepted` status. See Open Questions for validation tracking.

---

## Relationship to Claude Code Runner (OA03.1)

| Aspect | Claude Code (OA03.1) | Codex (OA03.2) |
|--------|---------------------|----------------|
| Invocation | CLI (`--print` mode) | API (Responses API) |
| Workspace access | Filesystem-native | Tool-mediated |
| Output format | stdout/JSON stream | Structured JSON |
| Best for | Exploration, refactoring, review | Implementation, mechanical coding |
| Session model | Single-shot CLI | Single-shot API |

Both are first-class sub-agents under the same conductor, planner, and policy system. No special-case kernel logic beyond agent capability metadata.

---

## Consequences

### Positive

- Clean API-first model avoids VS Code extension complexity
- Explicit tool surface makes all workspace access auditable
- Structured output enables reliable Planner evaluation
- Aligns with prompt-program runtime: tools are the "IDE", prompts define behavior

### Negative / Tradeoffs

- Limited to capabilities expressible via tool surface
- No real-time feedback during execution (single-shot)
- Requires maintaining tool implementations in kernel
- API costs per invocation

---

## Alternatives Considered

### 1. Drive VS Code Extension

**Approach:** Automate the Codex VS Code extension UI.

**Rejected because:**

- Rebuilding IDE semantics is massive scope
- Brittle (UI changes break automation)
- Unnecessary — tool surface provides required capabilities

### 2. Multi-Turn Conversational Mode

**Approach:** Allow Codex to ask clarifying questions mid-step.

**Rejected because:**

- Violates single-shot step model
- Complicates Planner evaluation
- Clarification is Planner's job, not sub-agent's

### 3. Shared Tool Surface with Claude Code

**Approach:** Same tool definitions for both agents.

**Rejected because:**

- Claude Code is filesystem-native; forcing tool indirection adds complexity
- Different agents have different optimal interfaces
- OA03 principle: normalize outputs, not control surfaces

---

## Open Questions

### 1. Experiment Matrix Validation

**Question:** Have all control surface mapping tests been validated?

**Tests required:**

- [ ] Simple file read returns content
- [ ] Search repo returns matching locations
- [ ] Apply valid patch succeeds
- [ ] Apply patch to forbidden path is rejected
- [ ] Invalid output schema marks step unsafe
- [ ] Timeout marks step blocked

**Decision needed by:** Before moving to `accepted` status

### 2. Codex Model Selection

**Question:** Which Codex model variant for implementation tasks?

**Options:**

- `gpt-5.2-codex` — Most capable, higher cost
- `gpt-5.1-codex-max` — Good for project-scale work
- `codex-mini-latest` — Cost-effective for simpler tasks
- Model routing based on task complexity

**Decision needed by:** Implementation start

### 3. Tool Expansion

**Question:** What additional tools are needed beyond v1 set?

**Candidates:**

- `get_symbols(path)` — LSP-like symbol extraction
- `get_references(symbol)` — Find usages
- `run_lint(path)` — Lint specific file

**Decision needed by:** After v1 validation

### 4. Context Window Management

**Question:** How to handle tasks requiring more context than fits in single invocation?

**Options:**

- Chunked execution (multiple steps)
- Summarization of large files
- Selective context based on task analysis

**Decision needed by:** Implementation

---

## Related ADRs

- [ADR-OA03: Agent Runner Architecture](/architecture/agent-orchestration/adr/adr-oa03-agent-runner-architecture.md) — Parent architecture
- [ADR-OA03.1: Claude Code Runner](/architecture/agent-orchestration/adr/adr-oa03.1-claude-code-runner.md) — Sibling runner specification
- [ADR-OA01: Agent Orchestration Strategy](/architecture/agent-orchestration/adr/adr-oa01-agent-orchestration-strategy.md) — Parent strategy

---

## As-Built Notes & Addendums

*Reserved for post-implementation updates. Never edit the original Context/Decision/Consequences sections — always append addendums here.*

### Addendum 2026-01-25: Spike Findings — Development Suspended

**Author**: Claude Opus 4.5
**Status Change**: `proposed` → `suspended`

#### Summary

A proof-of-concept harness was built and tested against the Responses API. The spike revealed that **the core assumption of this ADR is invalid**: GPT-Codex models do not reliably produce structured output after tool-calling rounds.

#### Key Findings

1. **No Final Text Output**: When tools are available, the model treats tool calls as the "output" and stops. The API returns `status: completed` with only function_call blocks — no text/JSON response.

2. **API Parameter Limitations**: The Responses API does not support `response_format` for schema enforcement, rejects `temperature` settings, and has no `tool_choice: none` equivalent to force text output.

3. **VS Code Extension Architecture**: The Codex VS Code extension does **not** rely on model-generated summaries. It tracks tool calls client-side and synthesizes summaries from observed behavior. This is a fundamentally different architecture than the harness approach.

4. **Cost Implications**: Without VS Code's interactive feedback loop, API costs accumulate without proportional productivity gain.

#### Invalid Assumptions

| ADR Assumption | Reality |
|----------------|---------|
| "Codex must emit schema-validated structured output" | Model emits tool calls only, no text response |
| "Output Validation Rules" would classify responses | Responses have no text to validate |
| "Structured output enables reliable Planner evaluation" | No structured output is produced |

#### Recommendation

**Suspend development** until one of the following conditions is met:

1. OpenAI adds forced-text-output mode to Responses API
2. Business need justifies building VS Code-style client orchestration
3. Chat Completions API proves more suitable for this use case

#### Preserved Artifacts

The spike produced working code that can be resumed:

- Harness package: `src/tnh_scholar/agent_orchestration/codex_harness/`
- CLI entrypoint: `src/tnh_scholar/cli_tools/tnh_codex_harness/`
- Tool tests: `tests/agent_orchestration/test_codex_harness_tools.py`
- Detailed findings: `/architecture/agent-orchestration/notes/codex-harness-spike-findings.md`

#### Impact on Parent ADRs

- **ADR-OA03 (Agent Runner Architecture)**: Codex runner is not viable as specified. Claude Code runner (OA03.1) should be prioritized.
- **ADR-OA01 (Orchestration Strategy)**: Multi-agent approach remains valid, but Codex cannot serve as the primary implementation engine until API constraints are resolved.
