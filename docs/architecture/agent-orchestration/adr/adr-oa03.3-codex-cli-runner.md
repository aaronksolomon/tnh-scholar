---
title: "ADR-OA03.3: Codex CLI Runner"
description: "Codex execution path via CLI — headless exec mode, superseding API-based approach"
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Opus 4.5"
status: proposed
created: "2026-02-07"
updated: "2026-02-07"
parent_adr: "adr-oa03-agent-runner-architecture.md"
supersedes: "adr-oa03.2-codex-runner.md"
---

# ADR-OA03.3: Codex CLI Runner

Codex execution path for tnh-conductor via CLI — headless `codex exec` mode with JSONL output capture, superseding the API-based approach in ADR-OA03.2.

- **Status**: Proposed
- **Type**: Implementation ADR (De-risking Spike)
- **Date**: 2026-02-07
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, Claude Opus 4.5
- **Parent ADR**: [ADR-OA03](/architecture/agent-orchestration/adr/adr-oa03-agent-runner-architecture.md)
- **Supersedes**: [ADR-OA03.2](/architecture/agent-orchestration/adr/adr-oa03.2-codex-runner.md) (API-based approach)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

### Background

ADR-OA03.2 attempted to drive Codex via the OpenAI Responses API. The spike revealed fundamental constraints:

1. **No final text output**: Model treats tool calls as completion — no structured JSON response
2. **API parameter limitations**: `response_format`, `temperature`, `tool_choice: none` not supported
3. **VS Code extension architecture**: Uses proprietary "app server" with client-side orchestration

These constraints led to suspending OA03.2 on 2026-01-25.

### New Development: Codex CLI

The Codex CLI is now available with headless execution capabilities. Reference: https://developers.openai.com/codex/cli/reference

Key capabilities:

| Capability | CLI Flag/Command | Description |
|------------|------------------|-------------|
| Headless execution | `codex exec` | Run Codex non-interactively |
| JSONL output | `--json` | Newline-delimited JSON events |
| Final response capture | `--output-last-message <path>` | Write final response to file |
| Approval bypass | `--full-auto` | Low-friction automation preset |
| Approval control | `--ask-for-approval` | `untrusted`, `on-failure`, `on-request`, `never` |
| Sandbox policy | `--sandbox` | `read-only`, `workspace-write`, `danger-full-access` |
| Session resume | `codex exec resume` | Continue prior sessions |
| MCP server mode | `codex mcp-server` | Agent-to-agent consumption |

This provides a CLI-based execution model **analogous to Claude Code's `--print` mode**, which is the foundation of ADR-OA03.1.

### Why CLI Over API

| Concern | API Approach (OA03.2) | CLI Approach (OA03.3) |
|---------|----------------------|----------------------|
| Final output capture | Model doesn't emit text after tools | `--output-last-message` captures response |
| Structured events | Limited API response format | `--json` provides JSONL event stream |
| Tool execution | Must implement tool providers | Native filesystem access |
| Approval/safety | Manual implementation | Built-in `--sandbox` and `--ask-for-approval` |
| Architecture alignment | Different from Claude Code | Same pattern as OA03.1 |

---

## Decision

### Spike Objectives

This ADR defines a de-risking spike to validate Codex CLI as a viable execution surface for tnh-conductor. The spike must prove:

1. **Headless execution works**: `codex exec "task"` completes without interaction
2. **Output is capturable**: `--json` + `--output-last-message` provide parseable results
3. **Automation controls work**: `--full-auto` or `--ask-for-approval never` bypass prompts
4. **Sandbox policy is enforceable**: `--sandbox workspace-write` restricts access
5. **Pattern matches OA03.1**: Same capture/parse patterns as Claude Code runner

### Evaluation Questions

The spike should also answer these higher-level questions:

1. Can Codex CLI reliably perform multi-step code edits in a repo?
2. Where and how are run transcripts and summaries stored?
3. Can Codex be run deterministically with project-local configuration?
4. What artifacts can be harvested post-run without UI integration?
5. Is the CLI behavior functionally equivalent to Codex in VS Code?

### Execution Model

Codex CLI is invoked **headlessly via subprocess**, matching the OA03.1 pattern:

```
TaskSpec + WorkingDirectory
        |
   codex exec --json --output-last-message <path> --full-auto -m gpt-5.2-codex "task"
        |
 Captured Outputs (JSONL events + final response + workspace diff)
```

**Execution constraints:**

| Constraint | Value | Rationale |
|------------|-------|-----------|
| Single-shot execution | Per step | No multi-turn within a step |
| Approval mode | `--full-auto` or configured | Automation preset |
| Sandbox | `workspace-write` | Match work branch isolation |
| Output capture | JSONL + final message file | Dual-channel capture |
| Model | `-m gpt-5.2-codex` | Consistent model selection |
| Session resume | **Not used in spike** | Keep parity with OA03.1 |
| MCP | **Out of scope** | ADR-OA01.1 CLI-first, no MCP in spike |

### Claude Parity (OA03.1 Alignment)

The Codex CLI spike should mirror the Claude Code runner capture contract:

- Same artifact set (transcript, final response, git diff, run metadata)
- Same workflow expectations (single-shot execution, headless CLI only)
- Same PTY posture (fallback only; primary capture via stdout/stderr)

### Core Principle (from OA03)

> Normalize outputs, not control surfaces.

The Codex CLI adapter handles CLI-specific mechanics; the kernel receives normalized `AgentRunResult` regardless of which runner produced it.

---

## Spike Deliverables

### Pass/Fail Criteria

| Test Case | Expected Result | Status |
|-----------|-----------------|--------|
| Basic execution | `codex exec "list files in src/"` completes | [ ] |
| JSONL capture | `--json` produces parseable event stream | [ ] |
| Final response | `--output-last-message` contains summary | [ ] |
| Full-auto mode | `--full-auto` bypasses approval prompts | [ ] |
| Sandbox enforcement | `--sandbox read-only` prevents writes | [ ] |
| Workspace write | `--sandbox workspace-write` allows project writes | [ ] |
| Error handling | Non-zero exit code on failure | [ ] |
| Timeout handling | Process can be killed on timeout | [ ] |

### Artifacts

| Artifact | Description |
|----------|-------------|
| `codex_cli_spike.py` | Spike implementation |
| `events.ndjson` | Captured JSONL event stream |
| `response.txt` | Final response from `--output-last-message` |
| `run.json` | Run metadata |
| `SPIKE_REPORT.md` | Findings, gotchas, recommendations |

### Decision Point

If spike passes → proceed to full Codex CLI adapter implementation under OA03.

If spike fails → document constraints, evaluate alternatives (e.g., wait for CLI improvements).

---

## Output Contract

Codex CLI runner must produce the same `AgentRunResult` structure as Claude Code runner (OA03.1):

```python
@dataclass
class AgentRunResult:
    """Normalized output from any agent runner."""
    status: Literal["success", "partial", "blocked", "timeout", "error"]
    transcript: str          # Full JSONL event stream or formatted output
    final_response: str      # Content from --output-last-message
    workspace_diff: str      # Git diff of changes
    exit_code: int
    duration_seconds: float
    metadata: dict           # Agent-specific metadata (model, tokens, etc.)
```

### Dual-Channel Output

Consistent with OA01/OA03:

| Channel | Content | Source |
|---------|---------|--------|
| **Transcript** | JSONL event stream | `--json` stdout |
| **Semantic** | Final response | `--output-last-message` file |
| **Workspace** | Git diff | Post-run `git diff` |

---

## Control Surface Mapping

**Required by OA03 ADR Gate.**

### Authoritative Documentation

- Codex CLI Reference: https://developers.openai.com/codex/cli/reference
- OpenAI Codex Overview: https://openai.com/codex/

### Invocation Modes

| Mode | Command | Use Case |
|------|---------|----------|
| Headless exec | `codex exec` | Primary execution mode |
| Interactive | `codex` | Not used for automation |
| MCP server | `codex mcp-server` | Out of scope for spike |

### IO Model

- **Stateless per invocation**: Each `codex exec` is independent
- **Session resume available**: `codex exec resume` (not used in spike)
- **Dual output**: JSONL to stdout, final response to file

### Permission / Safety Controls

| Control | Mechanism |
|---------|-----------|
| Approval control | `--ask-for-approval` flag |
| Sandbox policy | `--sandbox` flag |
| Directory access | `--add-dir` for additional paths |
| Model selection | `-m` / `--model` flag |

### Experiment Matrix

| Test Case | Expected Result |
|-----------|-----------------|
| Headless execution completes | Exit code 0, output captured |
| JSONL events parseable | Valid JSON per line |
| Final response captured | Non-empty file content |
| Sandbox read-only enforced | Write attempts blocked |
| Sandbox workspace-write works | Project files writable |
| Timeout kills process | Process terminates, partial output captured |
| Model pinning | `-m gpt-5.2-codex` honored in run metadata |

---

## Relationship to OA03.2 (API Runner)

This ADR **supersedes** ADR-OA03.2. The relationship:

| OA03.2 Role | Description |
|-------------|-------------|
| **Historical context** | Documents API constraints and why that approach failed |
| **Spike evidence** | Learnings inform what to avoid in CLI approach |
| **Preserved artifacts** | Harness code may inform CLI adapter design |

OA03.2's status is `superseded`. This ADR (OA03.3) provides the viable Codex execution path.

---

## Consequences

### Positive

- **Proven pattern**: Matches Claude Code runner (OA03.1) architecture
- **Native capabilities**: CLI handles tool execution, sandbox, approvals
- **Simpler adapter**: No custom tool providers needed (unlike API approach)
- **Dual-channel capture**: JSONL events + final response + git diff
- **Client-driven agent**: Outputs are harvested, not synthesized — aligns with OA01.1's principle that orchestration owns provenance and lifecycle, not the agent loop itself

### Negative / Tradeoffs

- **CLI dependency**: Requires Codex CLI installed and configured
- **Less control**: Cannot customize tool surface (CLI provides fixed tools)
- **Output parsing**: Must handle JSONL event stream format
- **External process**: Subprocess management vs API call

### Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| CLI behavior differs from docs | Spike validates actual behavior |
| Output format changes | Version-pin CLI, document format |
| Approval prompts leak through | Test `--full-auto` thoroughly |
| Sandbox insufficient | Combine with git worktree isolation |

---

## Open Questions

### 1. JSONL Event Schema

**Question:** What is the exact schema of `--json` output events?

**Action:** Capture and document during spike.

**Decision needed by:** Spike completion

### 2. Model Selection

**Question:** Which Codex model variant for implementation tasks?

**Options:**
- Default (let CLI choose)
- Explicit `-m gpt-5.2-codex` for consistency
- Task-based selection

**Decision needed by:** Implementation

---

## Related ADRs

- [ADR-OA03: Agent Runner Architecture](/architecture/agent-orchestration/adr/adr-oa03-agent-runner-architecture.md) — Parent architecture
- [ADR-OA03.1: Claude Code Runner](/architecture/agent-orchestration/adr/adr-oa03.1-claude-code-runner.md) — Sibling runner (pattern reference)
- [ADR-OA03.2: Codex Runner (API)](/architecture/agent-orchestration/adr/adr-oa03.2-codex-runner.md) — Superseded API approach
- [ADR-OA01.1: Conductor Strategy v2](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md) — Parent strategy

## Archived Versions

- [adr-oa03.3-codex-cli-spike-2026-01-29.md](/architecture/agent-orchestration/archive/adr-oa03.3-codex-cli-spike-2026-01-29.md) — Earlier draft from branch (preserved for reference)

---

## As-Built Notes & Addendums

*Reserved for post-implementation updates. Never edit the original Context/Decision/Consequences sections — always append addendums here.*
