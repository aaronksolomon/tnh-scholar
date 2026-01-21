---
title: "ADR-OA02: Phase 0 Protocol Layer Spike"
description: "De-risking spike to prove headless agent capture and safety controls for tnh-conductor"
type: "implementation-guide"
owner: "aaronksolomon"
author: "Aaron Solomon, GPT 5.2, Claude Opus 4.5"
status: accepted
created: "2026-01-19"
updated: "2026-01-19"
parent_adr: "adr-oa01-agent-orchestration-strategy.md"
---

# ADR-OA02: Phase 0 Protocol Layer Spike — Headless Capture + Safety Controls

De-risking spike to prove headless agent invocation, transcript capture, and safety controls work reliably.

- **Status**: Accepted
- **Type**: Implementation ADR (De-risking Spike)
- **Date**: 2026-01-19
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, GPT 5.2, Claude Opus 4.5
- **Parent ADR**: [ADR-OA01](/architecture/agent-orchestration/adr/adr-oa01-agent-orchestration-strategy.md)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

ADR-OA01 establishes `tnh-conductor` as a **Prompt-Program Runtime**: behavior is defined in versioned prompts and workflows; code exists primarily for **capture, enforcement, and execution**.

The highest technical risk is the **Protocol Layer**: reliably invoking sub-agent tools headlessly (Claude Code / Codex), capturing their **full transcripts** and **workspace effects**, and handling failure modes (hangs, interactive prompts, timeouts) deterministically.

If this layer is fragile, the entire architecture collapses into "works only when watched."

This spike is **not** a full orchestrator. It is a de-risking prototype with pass/fail criteria that must be satisfied before proceeding to Phase 1.

---

## Decision

We will implement a Phase 0 spike that proves, end-to-end, that we can:

1. Invoke a sub-agent in headless mode (at least one target surface)
2. Capture a complete transcript (PTY when required)
3. Capture workspace effects (git status + diff before/after)
4. Emit progress events (heartbeats) independent of filesystem writes
5. Detect and safely terminate negative paths (hangs, unexpected prompts)
6. Persist a minimal provenance record in the `tnh-gen` ledger

### Spike Scope

**In Scope:**

- CLI wrapper for one sub-agent surface (preferred order):
  - Claude Code headless mode (if available)
  - Claude Code via PTY wrapper
  - Codex CLI (if easiest to automate)
- Transcript capture (raw + normalized)
- Git workspace capture (pre/post)
- Heartbeat monitoring + inactivity timeout kill
- Minimal provenance event emission into `tnh-gen`
- A short Spike Report documenting constraints, gotchas, and recommended approach

**Out of Scope:**

- Full workflow engine (YAML opcodes)
- Full prompt library system (beyond one task prompt)
- VS Code integration
- Sandboxing beyond git work-branch isolation
- Prompt regression testing harness

### Success Criteria (Pass/Fail)

The spike is considered successful only if **all** of the following hold:

1. **Headless run completes** without manual interaction for at least one agent surface
2. **Transcript is complete** (not truncated; includes agent output and prompts)
3. **Workspace effects captured**:
   - `git status --porcelain` before/after
   - unified diff patch (or empty patch if no changes)
4. **Progress events emitted** even if no files change
5. **Negative-path handling works**:
   - hang/inactivity triggers kill
   - interactive prompt triggers kill (best-effort detection)
   - non-zero exit captured as blocked
6. **Provenance record written** containing:
   - agent identifier + version (best-effort)
   - prompt id/version (or task id)
   - timestamps, exit code, termination reason
   - artifact paths (transcript, diff, stdout/stderr)
7. **Work is isolated on a work branch**, never touching `main`

If any criterion fails, this ADR blocks Phase 1 until resolved or alternative approach chosen.

### Design Constraints

- **Primary artifacts are Transcript + Diff** (dual-channel output)
- Transcript capture must handle interactive/ANSI output (PTY/TTY)
- Protocol Layer must not depend on the agent emitting structured JSON
- Rollback/recovery is git-based and must be deterministic for the spike:
  - create a work branch
  - reset/discard changes on failure
  - return to original branch

### Target Surfaces

| Agent | Invocation Method | Capture Method |
|-------|-------------------|----------------|
| Claude Code | `claude --print` mode | stdout capture |
| Claude Code | PTY wrapper | PTY session log |
| Codex | CLI invocation | stdout/PTY |

---

## Minimal Interface

### CLI Entry Point (Spike Tool)

One command that runs a single "step" end-to-end:

**Inputs:**

- `--agent` (e.g., `claude-code`, `codex`)
- `--task` (string) or `--prompt-id` (optional)
- `--timeout-seconds` (wall clock)
- `--idle-timeout-seconds` (heartbeat)
- `--work-branch` (optional; otherwise generated)

**Outputs** (paths printed to stdout):

- transcript file (raw + normalized)
- diff patch file
- run metadata json
- provenance event bundle path

**Example:**

```bash
tnh-conductor-spike run --agent claude-code --task "List files in src/"
```

### Output Artifacts

Required outputs in a run directory, e.g. `.tnh-gen/runs/<run_id>/`:

| Artifact | Description |
|----------|-------------|
| `transcript.raw.log` | Raw PTY output with ANSI codes |
| `transcript.md` | Normalized, ANSI-stripped transcript |
| `stdout.log` / `stderr.log` | Standard streams (if applicable) |
| `git_pre.json` | Git status summary before run |
| `git_post.json` | Git status summary after run |
| `diff.patch` | Unified diff of workspace changes |
| `run.json` | Run metadata |
| `events.ndjson` | Event stream (newline-delimited JSON) |

---

## Provenance Event Model (Minimal)

The spike must write a minimal event stream (newline-delimited JSON) that `tnh-gen` can ingest.

### Required Event Types

- `RUN_STARTED`
- `AGENT_STARTED`
- `HEARTBEAT`
- `AGENT_OUTPUT` (chunked transcript capture; optional if too heavy)
- `WORKSPACE_CAPTURED_PRE`
- `WORKSPACE_CAPTURED_POST`
- `DIFF_EMITTED`
- `RUN_BLOCKED` (with reason)
- `RUN_COMPLETED`

### Required Fields (Minimum)

- `run_id`
- `timestamp`
- `event_type`
- `agent`
- `work_branch`
- `artifact_paths` (where applicable)
- `reason` / `exit_code` (where applicable)

---

## Negative-Path Handling Requirements

### Hang / Inactivity

- Implement an **idle timeout**: if no PTY output and no explicit progress events for N seconds, kill the agent process.
- On kill:
  - capture last N lines of transcript into run metadata
  - mark status `blocked` with reason `idle_timeout`
  - write `RUN_BLOCKED` event

### Unexpected Interactive Prompt

Best-effort detection only (do not overfit):

- **Heuristics:**
  - patterns like `y/n`, `confirm`, `press enter`, `2fa`, `otp`, `password`
  - repeated prompt lines without progress
- **Response:**
  - kill process
  - status `blocked` reason `interactive_prompt_detected`
  - queue for human review (by provenance record; spike can just mark)

### Non-zero Exit

- Capture exit code
- Preserve stderr/stdout
- Mark status `blocked` reason `nonzero_exit`

### Wall-Clock Timeout

- Kill process if total runtime exceeds `timeout-seconds`
- Mark status `blocked` reason `wall_clock_timeout`

---

## Implementation Notes

The spike will be implemented in Python 3.12.4 (project standard).

Key implementation choices (pick one path; document results in spike report):

### PTY Capture

- Use a pseudo-terminal to wrap interactive CLIs
- Store raw bytes; separately store a normalized, ANSI-stripped transcript for planner/human consumption

### Workspace Capture

- Use `git` as ground truth (status + diff)
- Always capture pre/post summaries

### Branch Isolation

- Create `work/<run_id>` branch (or similar)
- Never commit; leave changes staged/unstaged as artifacts
- On blocked/unsafe: reset hard to the pre-run checkpoint (or discard branch)

---

## Alternatives Considered

### 1. SDK/API-only integration (no CLI wrapping)

- **Pros:** structured outputs, fewer TTY issues
- **Cons:** may not match Claude Code/Codex capabilities; increased integration scope

### 2. VS Code extension as the runtime

- **Pros:** easy UI integration
- **Cons:** heavy lift; brittle; blocks CLI-first strategy

### 3. Require agents to output strict JSON

- **Pros:** easier parsing
- **Cons:** unreliable; conflicts with transcript-first valuation

We choose the CLI/PTY capture spike because it directly tests the critical risk while preserving the Prompt-Program Runtime architecture.

---

## Consequences

### Positive

- De-risks the only architecture-blocking dependency (Protocol Layer)
- Produces concrete operational knowledge about agent CLIs
- Establishes a repeatable capture-and-record pattern compatible with `tnh-gen`

### Negative / Tradeoffs

- Requires real experimentation with brittle tools
- Might reveal that one agent surface is unsuitable for headless use
- May force selecting a single "Phase 1 executor" (Codex or Claude Code) early

---

## Deliverables

| Artifact | Description |
|----------|-------------|
| `tnh_conductor_spike.py` | CLI module implementing the spike |
| `.tnh-gen/runs/<run_id>/` | Example run outputs |
| `SPIKE_REPORT.md` | Findings document |

**SPIKE_REPORT.md must include:**

- What worked / failed
- Failure modes observed
- Recommended agent surface(s) for Phase 1
- Required kernel features to proceed
- Known limitations and proposed mitigations

---

## Decision Gate

Proceed to ADR-OA03 / Phase 1 only if Phase 0 passes success criteria.

If Phase 0 fails:

- document the failure class (TTY, auth, tool constraints)
- choose an alternative approach (SDK/API, different agent surface, or modified constraints)
- record the updated strategy in a follow-up ADR addendum

---

## Open Questions

### 1. Claude Code Headless Mode Availability

**Question:** Does Claude Code support a reliable headless/non-interactive mode?

**Options:** `--print` flag, PTY wrapper, SDK

**Decision needed by:** During spike execution

### 2. ANSI Stripping Strategy

**Question:** How aggressive should ANSI stripping be for normalized transcripts?

**Options:** Full strip, preserve structure markers, configurable

**Decision needed by:** During spike implementation

---

## Appendix: Example Run Metadata Schema

This is illustrative; exact fields may evolve.

```yaml
# run.json
run_id: "2026-01-19-001"
started_at: "2026-01-19T10:00:00Z"
ended_at: "2026-01-19T10:02:30Z"
agent: "claude-code"
agent_version: "1.0.0"  # best-effort
task: "List files in src/"
prompt_id: null
work_branch: "work/2026-01-19-001"
exit_code: 0
termination_reason: "completed"
artifact_paths:
  transcript_raw: "transcript.raw.log"
  transcript_normalized: "transcript.md"
  diff: "diff.patch"
  events: "events.ndjson"
git_pre_summary:
  branch: "main"
  clean: true
  staged: 0
  unstaged: 0
git_post_summary:
  branch: "work/2026-01-19-001"
  clean: true
  staged: 0
  unstaged: 0
```

---

## As-Built Notes & Addendums

*Reserved for post-implementation updates. Never edit the original Context/Decision/Consequences sections — always append addendums here.*

### Addendum 2026-01-19: Spike Safety Gate Decision

We will implement a kernel-level command filter for the Phase 0 spike. This filter applies only to commands that the sub-agent explicitly requests user confirmation for; for other actions, we rely on sandboxing and post-run diff capture. Policy-prompt enforcement is deferred to later phases.

**Command filter implementation:** regex match against the full command string.

**Blocked patterns (regex):**
- `\brm\s+-r(f)?\b`
- `\bgit\s+reset\s+--hard\b`
- `\bgit\s+clean\s+-fdx?\b`
- `\bgit\s+checkout\s+--\b`
- `\bgit\s+restore\s+--(worktree|staged)\b`
- `\bgit\s+branch\s+-D\b`
- `\bgit\s+rebase\b`
- `\bgit\s+merge\b`
- `\bgit\s+push\s+--force(-with-lease)?\b`
- `\bgit\s+commit\b`
- `\bgit\s+push\b`
- `\bmv\b.*(\s|/)\.git(/|\s|$)`
- `\bcp\b.*(\s|/)\.git(/|\s|$)`
- `\b(curl|wget|ssh|scp|rsync)\b`
- `\b(pip|poetry|npm|brew)\b`

### Addendum 2026-01-20: Worktree Preflight Check

Phase 0 runs must fast-fail if the repository is not clean. The spike should exit before branch creation and provide a short suggestion to run in a dedicated git worktree to avoid contaminating active development branches. The sandbox root defaults to `<repo>-sandbox` (override via `SPIKE_SANDBOX_ROOT`), and the runner must fail if the current repo root does not match the sandbox root.

---

## Related ADRs

- [ADR-OA01: Agent Orchestration Strategy](/architecture/agent-orchestration/adr/adr-oa01-agent-orchestration-strategy.md) — Parent strategy ADR
- `adr-pv01-provenance-tracing-strat.md` — Foundation provenance infrastructure
- `adr-tg01-cli-architecture.md` — CLI patterns for tnh-gen
