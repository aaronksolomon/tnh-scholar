---
title: "ADR-OA03.1: Claude Code Runner"
description: "Claude Code execution path — headless print mode only, no interactive/PTY automation"
owner: "aaronksolomon"
author: "Aaron Solomon, GPT 5.2, Claude Opus 4.5"
status: proposed
created: "2026-01-22"
updated: "2026-01-22"
parent_adr: "adr-oa03-agent-runner-architecture.md"
---

# ADR-OA03.1: Claude Code Runner

Claude Code execution path for tnh-conductor — headless print mode as the sole automation surface, with explicit rejection of interactive/PTY automation.

- **Status**: Proposed
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

OA03 establishes the runner architecture: a shared kernel handling cross-agent invariants, with per-agent adapters handling surface-specific mechanics. This ADR specifies the **Claude Code runner adapter**.

### Claude Code Has Multiple Control Surfaces

Claude Code CLI presents **distinct control surfaces** that should be treated as separate products:

| Surface | Invocation | Interaction Model | Persistence |
|---------|------------|-------------------|-------------|
| **Headless/print mode** | `claude --print` | Stateless (stdin → stdout) | None |
| **Interactive REPL/UI** | `claude` (no `--print`) | Terminal-driven session | Session-scoped |

**Critical insight:** These are fundamentally different automation targets with different requirements, stability characteristics, and viability for orchestration.

### Why Interactive Mode is Not Viable for Automation

Interactive Claude Code is **explicitly out of scope** for this runner:

| Issue | Impact |
|-------|--------|
| **Auth + internet login flows** | Requires human intervention, cannot be automated headlessly |
| **Complex UI/prompts** | Unstable target; small upstream changes break automation |
| **TTY-gated behaviors** | Requires PTY with all its complexity (ANSI, sizing, prompt detection) |
| **No structured output** | Progress/completion only visible via terminal scraping |

**Decision:** We do not attempt to automate interactive Claude Code. The runner supports **headless print mode only**.

---

## Decision

### Supported Automation Surface

The Claude Code runner supports **one surface only**:

```
claude --print [options] [prompt]
```

This is a **Unix-filter style** surface:

- Stateless: each run is independent
- IO: stdin → stdout (or argument prompt → stdout)
- No session persistence
- Structured output available

### Explicit Non-Goals

| Non-Goal | Rationale |
|----------|-----------|
| Interactive REPL automation | Unstable, auth-gated, PTY-dependent |
| PTY transcript capture | Not needed for `--print` mode; adds failure modes |
| Terminal prompt detection | Native permission controls are superior |
| Auth handling | Out of scope; assume pre-authenticated environment |

**PTY is explicitly unsupported** for the Claude Code runner. PTY infrastructure may exist in the codebase (from OA02 spike) but is not used by this runner.

---

## Control Surface Mapping

**Required by OA03 ADR Gate.**

### Authoritative Documentation

- Claude Code CLI: [Claude Code Overview](https://docs.anthropic.com/en/docs/claude-code/overview)
- GitHub: [anthropics/claude-code](https://github.com/anthropics/claude-code)

### Invocation Modes

#### 1. Headless / Print Mode (SUPPORTED)

| Aspect | Value |
|--------|-------|
| Invoke | `claude -p` / `claude --print` |
| Interaction model | Stateless |
| IO | stdin → stdout |
| Persistence | None (each run independent) |
| Intended use | Automation, orchestration, batch runs |

#### 2. Interactive Mode (NOT SUPPORTED)

| Aspect | Value |
|--------|-------|
| Invoke | `claude` (no `--print`) |
| Interaction model | Terminal-driven session |
| IO | TTY/UI |
| Persistence | Session-scoped only |
| Intended use | Human-in-the-loop coding |
| **Runner support** | **None — out of scope** |

### Output Formats (Print Mode)

| Format | Flag | Description | Use Case |
|--------|------|-------------|----------|
| `text` | `--output-format text` | Human-readable | Not recommended (fragile parsing) |
| `json` | `--output-format json` | Single structured result | Batch runs, simple tasks |
| `stream-json` | `--output-format stream-json` | Incremental structured events (ndjson) | **Recommended** — live progress/heartbeat |

**Default for runner:** `--output-format stream-json`

### Permission Modes

| Mode | Flag | Behavior | Orchestration Suitability |
|------|------|----------|---------------------------|
| `plan` | `--permission-mode plan` | Analysis only, no edits/commands | Good for review/design steps |
| `default` | `--permission-mode default` | Prompts on first tool use | **Bad** — breaks headless |
| `acceptEdits` | `--permission-mode acceptEdits` | Auto-accept edits, still gate commands | Partial |
| `dontAsk` | `--permission-mode dontAsk` | Deny by default unless allowed | **Recommended** for orchestration |
| `bypassPermissions` | `--permission-mode bypassPermissions` | Skip prompts entirely | Only in sandboxed environments |

**Default for runner:** `--permission-mode dontAsk` with explicit allow rules

### Tool Surface Restriction

Claude Code provides **native tool gating**:

- `--tools` flag restricts available built-in tools
- Settings files (`.claude/settings.json`) define allow/deny rules
- Permission rules are ordered and composable

**Principle:** Encode policy in native allow/deny rules, not ad-hoc regex filters in the orchestrator. Native rules have less drift and closer-to-native semantics.

### Settings as Control Surface

Claude Code supports project/user settings files:

- `.claude/settings.json` (project-level)
- User-level settings
- CLI flags to choose settings sources

**Runner requirement:** Treat "settings + flags" as the effective invocation contract. Record both in provenance.

---

## Capture Strategy

### Default (Headless Automation)

```bash
claude --print \
  --output-format stream-json \
  --permission-mode dontAsk \
  [--tools <allowed-tools>] \
  "<prompt>"
```

| Aspect | Approach |
|--------|----------|
| Output capture | Structured JSON events from stdout |
| Progress/heartbeat | Derive from stream-json events |
| PTY | **Not used** |
| Failure detection | Exit code + structured output |

### Fallback (Batch Only)

```bash
claude --print \
  --output-format json \
  --permission-mode dontAsk \
  "<prompt>"
```

- Single capture at completion
- No incremental progress
- Simpler but less visibility

### Interactive (NOT SUPPORTED)

PTY transcript capture is **not implemented** in this runner. If a future use case requires interactive automation, it would need a separate runner or significant architectural work.

---

## Output Contract

### Stream-JSON Event Model

Claude `--output-format stream-json` emits newline-delimited JSON events:

```json
{"type": "start", "timestamp": "..."}
{"type": "content", "text": "..."}
{"type": "tool_use", "tool": "Read", "input": {...}}
{"type": "tool_result", "tool": "Read", "output": "..."}
{"type": "complete", "result": {...}}
```

*(Exact schema TBD — validate against actual CLI output)*

### Runner Output Normalization

The runner normalizes Claude output to kernel-compatible artifacts:

| Artifact | Source |
|----------|--------|
| Transcript | Accumulated `content` events |
| Tool calls | `tool_use` / `tool_result` events |
| Final result | `complete` event |
| Exit status | Process exit code |

### Failure Handling

| Condition | Runner Response |
|-----------|-----------------|
| Non-zero exit code | Mark step `error` |
| Unparseable output | Mark step `unsafe` |
| Timeout | Mark step `killed_timeout` |
| Interactive prompt detected | Mark step `blocked`, reason `interactive_prompt` |

**Any non-parseable or interactive output → hard fail** (`blocked` or `unsafe`, `needs_human`).

---

## Permission & Safety

### Layered Approach

| Layer | Mechanism | Owner |
|-------|-----------|-------|
| **Native Claude controls** | `--permission-mode`, `--tools`, settings rules | Claude Code |
| **Kernel blocklist** | Regex command filter (defense-in-depth) | OA03 kernel |
| **Post-hoc diff policy** | OA01 policy prompt enforcement | OA01 kernel |

### Recommended Configuration

```bash
--permission-mode dontAsk
```

Plus settings rules:

```json
{
  "permissions": {
    "allow": [
      "Read(*)",
      "Glob(*)",
      "Grep(*)",
      "Edit(src/**)",
      "Edit(tests/**)"
    ],
    "deny": [
      "Bash(*)",
      "Edit(*.lock)",
      "Edit(.env*)"
    ]
  }
}
```

**Principle:** Use native permission/tool gating as primary safety mechanism. Terminal prompt detection is a failsafe only, not primary defense.

---

## Kernel Integration

### Adapter Responsibilities

| Responsibility | Implementation |
|----------------|----------------|
| CLI invocation | Subprocess with `--print` + configured flags |
| Output parsing | Parse stream-json or json format |
| Event emission | Translate Claude events to kernel event stream |
| Failure detection | Monitor exit code + output structure |

### Kernel Responsibilities (Unchanged from OA03)

| Responsibility | Description |
|----------------|-------------|
| Workspace isolation | Git worktree setup before Claude invocation |
| Pre/post capture | Git status + diff before and after |
| Policy enforcement | Check diff against RunPolicy |
| Provenance recording | Write run record with all artifacts |

### Provenance Requirements

Record in provenance:

- CLI flags used
- Settings file path (if any)
- Effective permission mode
- Tool restrictions
- Full stdout (stream-json events)
- Exit code
- Workspace diff

---

## Relationship to Codex Runner (OA03.2)

| Aspect | Claude Code (OA03.1) | Codex (OA03.2) |
|--------|----------------------|----------------|
| Invocation | CLI (`--print` mode) | API (Responses API) |
| Workspace access | Filesystem-native | Tool-mediated |
| Output format | stream-json / json | Structured JSON |
| Best for | Exploration, refactoring, review | Implementation, mechanical coding |
| Session model | Single-shot CLI | Single-shot API |
| PTY requirement | None (explicitly unsupported) | None (API-based) |

Both are first-class sub-agents under the same conductor, planner, and policy system.

---

## Experiment Matrix

**Required to validate control surface mapping before `accepted` status.**

| Test Case | Command | Expected Result | Status |
|-----------|---------|-----------------|--------|
| Basic headless run | `claude --print --output-format json "List files"` | Structured JSON output | **TODO** |
| Stream-json events | `claude --print --output-format stream-json "Describe codebase"` | Incremental ndjson events | **TODO** |
| Permission mode plan | `claude --print --permission-mode plan "Edit file.py"` | No edits attempted | **TODO** |
| Permission mode dontAsk | `claude --print --permission-mode dontAsk "Run tests"` | Denied without prompt | **TODO** |
| Tool restriction | `claude --print --tools Read,Glob "Edit file.py"` | Edit tool unavailable | **TODO** |
| Exit code on failure | `claude --print "Invalid task"` | Non-zero exit | **TODO** |

---

## Consequences

### Positive

- Clean, stable automation surface (Unix-filter model)
- Structured output enables reliable parsing and progress tracking
- Native permission controls provide robust safety without PTY heuristics
- No auth handling complexity
- Aligns with OA03 principle: prefer structured streams over PTY

### Negative / Tradeoffs

- Cannot automate interactive Claude Code sessions
- Limited to capabilities available in `--print` mode
- Requires pre-authenticated environment (out of scope for runner)
- PTY infrastructure from OA02 spike becomes dead code for this runner

---

## Alternatives Considered

### 1. Support Interactive Mode via PTY

**Approach:** Wrap interactive Claude Code in PTY for full session automation.

**Rejected because:**

- Auth flows require human intervention
- UI/prompts are unstable automation targets
- PTY adds complexity (ANSI, sizing, prompt detection) without proportional benefit
- Native `--print` mode provides everything needed for orchestration

### 2. Terminal Prompt Detection as Primary Safety

**Approach:** Detect Y/N prompts in transcript to gate dangerous operations.

**Rejected because:**

- Native permission controls (`--permission-mode dontAsk`) prevent prompts entirely
- Prompt detection is fragile (format changes, false positives)
- Defense-in-depth: use prompt detection as failsafe only

### 3. Support Multiple Output Formats Dynamically

**Approach:** Let workflow choose between text/json/stream-json per step.

**Deferred:** May add later, but default to stream-json for now. Simplifies runner implementation.

---

## Open Questions

### 1. Exact Stream-JSON Schema

**Question:** What is the precise schema for Claude `--output-format stream-json` events?

**Action:** Validate against actual CLI output; document schema in addendum.

**Decision needed by:** Implementation start

### 2. Settings File Management

**Question:** Should the runner manage `.claude/settings.json` or expect it pre-configured?

**Options:**

- Runner generates settings per-run (flexible, more complex)
- Runner expects pre-configured settings (simpler, less flexible)
- Hybrid: runner can override specific settings

**Decision needed by:** Implementation

### 3. Tool Restriction Granularity

**Question:** What level of tool restriction is appropriate for different task types?

**Options:**

- Strict: minimal tools per task type
- Moderate: category-based (read-only vs read-write)
- Permissive: broad access with post-hoc diff policy

**Decision needed by:** Phase 1 workflow design

---

## Related ADRs

- [ADR-OA03: Agent Runner Architecture](/architecture/agent-orchestration/adr/adr-oa03-agent-runner-architecture.md) — Parent architecture
- [ADR-OA03.2: Codex Runner](/architecture/agent-orchestration/adr/adr-oa03.2-codex-runner.md) — Sibling runner specification
- [ADR-OA01: Agent Orchestration Strategy](/architecture/agent-orchestration/adr/adr-oa01-agent-orchestration-strategy.md) — Parent strategy
- [ADR-OA02: Phase 0 Protocol Spike](/architecture/agent-orchestration/adr/adr-oa02-phase-0-protocol-spike.md) — Spike that produced initial Claude runner infrastructure

---

## As-Built Notes & Addendums

*Reserved for post-implementation updates. Never edit the original Context/Decision/Consequences sections — always append addendums here.*
