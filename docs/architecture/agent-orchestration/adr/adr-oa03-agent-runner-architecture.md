---
title: "ADR-OA03: Agent Runner Architecture"
description: "Phase 1 architecture for agent execution — kernel + adapter pattern based on OA02 spike learnings"
owner: "aaronksolomon"
author: "Aaron Solomon, GPT 5.2, Claude Opus 4.5"
status: proposed
created: "2026-01-21"
updated: "2026-01-22"
parent_adr: "adr-oa01-agent-orchestration-strategy.md"
---

# ADR-OA03: Agent Runner Architecture

Phase 1 architecture for agent execution — establishing a durable runner architecture that separates cross-agent invariants (kernel) from surface-specific mechanics (adapters), based on evidence gathered in OA02.

- **Status**: Proposed
- **Type**: Architecture ADR
- **Date**: 2026-01-21
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, GPT 5.2, Claude Opus 4.5
- **Parent ADR**: [ADR-OA01](/architecture/agent-orchestration/adr/adr-oa01-agent-orchestration-strategy.md)
- **Informed By**: [ADR-OA02](/architecture/agent-orchestration/adr/adr-oa02-phase-0-protocol-spike.md) (Phase 0 spike evidence)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Relationship to OA01

This ADR operates within the **Prompt-Program Runtime** valuation established in ADR-OA01:

- **Kernel** = capture, enforcement, execution substrate
- **Behavior** = versioned prompts and workflow definitions
- **Intelligence** = Planner evaluation, not runner logic

OA03 defines the **execution substrate for the `RUN_AGENT` opcode** — specifically, how the kernel invokes sub-agents, captures their outputs, and normalizes results for Planner consumption.

**Scope boundaries:**

| Concern | Owned By |
|---------|----------|
| Agent invocation + capture | OA03 (this ADR) |
| Workflow sequencing + opcodes | OA01 / future OA04 |
| Planner evaluation logic | OA01 / future OA05 |
| Prompt library management | OA01 / future OA04 |
| Policy enforcement (post-hoc diff) | OA01 kernel layer |

OA03 does **not** redefine OA01's kernel responsibilities — it refines how agent execution specifically works within that kernel.

---

## Context

ADR-OA02 was explicitly a **Phase 0 de-risking spike** whose goal was to answer a single question:

> Can we reliably invoke agents headlessly, capture their behavior and workspace effects, and enforce safety constraints?

That spike **succeeded** — but not in the way originally anticipated.

### What We Actually Learned in OA02

The spike set out to build PTY-based capture infrastructure for headless agent control. What we discovered instead:

1. **PTY wasn't needed.** Claude Code's `--print` mode provides single-shot headless execution with structured output. The spike captured terminal output via PTY, but this was unnecessary overhead — stdout capture suffices.

2. **We never validated complex PTY interaction.** The spike did not test real interactive exchanges (Y/N prompts, auth flows, multi-turn terminal sessions). We only captured output from what is effectively a single-state CLI command.

3. **The real insight was "read the docs."** The spike's value came from discovering that control surface mapping (understanding what modes and flags an agent actually provides) matters more than building sophisticated capture infrastructure for assumed interaction models.

4. **The spike did produce working infrastructure.** We have a functional runner for Claude Code CLI execution, workspace isolation via git worktrees, and provenance capture. This is valuable, even if the PTY layer is likely unnecessary.

### Honest Assessment of PTY Implementation

The PTY implementation from OA02 remains in the codebase but should be understood as:

- **Not validated** for complex interactive agent control
- **Likely unnecessary** for both Claude Code (`--print` mode) and Codex (SDK-based)
- **Potentially dead code** as the system evolves toward structured/headless modes

We retain it for now as a fallback for hypothetical agents that truly require terminal interaction, but expect it may be deprecated/removed in future phases if no such use case materializes.

### Why PTY-First Was Naive

The original assumption — that agents are terminal programs requiring PTY capture — reflected a misunderstanding of modern agent control surfaces:

| Surface Type | Example | Actual Capture Need |
|--------------|---------|---------------------|
| SDK event streams | Codex SDK, future Claude SDK | Structured events, no terminal |
| Headless CLI modes | Claude Code `--print` | stdout/stderr, JSON output |
| Interactive REPL | Claude Code default (no `--print`) | PTY — but we don't need this mode |

**Key insight:** Architecture must follow *documented capabilities*, not *assumed terminal interaction models*. The spike's greatest value was proving this principle, not the PTY code itself.

---

## Decision

We adopt a **Runner Architecture** that cleanly separates:

1. **A shared Agent Runner Kernel** (stable, cross-agent)
2. **Per-agent Runner Adapters** (surface-specific)

We explicitly do **not** attempt to normalize agent invocation mechanics.
Instead, we normalize **outputs, safety semantics, and provenance artifacts**.

### Core Principle

> We standardize *deliverables and safety guarantees*, not *control surfaces*.

Runner adapters are free to use whatever invocation mechanics their agent surface requires. The kernel cares only that adapters produce conforming artifacts and events.

---

## Architecture

### 1. Agent Runner Kernel (Shared)

The kernel is responsible for all cross-agent invariants:

| Responsibility | Description |
|----------------|-------------|
| **Run directory management** | Create run directory layout, manage artifact paths |
| **Workspace isolation** | Git worktree / branch isolation |
| **Workspace capture** | Pre/post git status + diff capture |
| **Transcript capture** | Delegate to adapter; normalize output (PTY only when required) |
| **Event stream emission** | Common event format for provenance |
| **Timeout enforcement** | Idle timeout + wall-clock timeout |
| **Termination classification** | Kernel-level states (see below) |
| **Provenance record writing** | Write run records to tnh-gen ledger |

The kernel is **agent-agnostic**. It delegates invocation mechanics entirely to adapters.

**Clarification from OA01:** OA01 lists "PTY transcript capture" as a kernel duty. OA03 refines this to: *transcript capture (PTY only when required; prefer structured streams/stdout when available)*. PTY is a tool, not a default.

### Kernel Termination States

The kernel classifies run termination using a small set of **mechanical states**:

| State | Meaning |
|-------|---------|
| `completed` | Agent exited normally (exit code 0) |
| `error` | Agent exited with non-zero exit code |
| `killed_timeout` | Wall-clock timeout exceeded |
| `killed_idle` | Idle timeout exceeded (no output/events) |
| `killed_policy` | Kernel-level policy violation detected |

**Note:** Semantic classification (`success`, `partial`, `blocked`, `unsafe`, `needs_human`) belongs to the **Planner**, not the kernel. The kernel reports mechanical outcomes; the Planner interprets meaning.

### 2. Runner Adapters (Per Agent Surface)

Each agent surface implements a dedicated runner adapter that:

- **Declares supported surfaces** — runners explicitly state which control surfaces they support (and which are out of scope)
- Maps native invocation mechanics to the kernel contract
- Selects an appropriate capture strategy (following the capture priority rule)
- Translates native events/output into the common event model
- Applies policy using native controls when available (e.g., `--allowedTools`, `--permission-mode`)

**Key principle:** A single agent (e.g., Claude Code) may expose multiple control surfaces (headless CLI, interactive REPL). Runners declare which surfaces they support. Unsupported surfaces are explicitly out of scope, not implicit failures.

Examples:

- **Claude CLI runner** — supports `--print` mode only; interactive mode explicitly unsupported
- **Codex SDK runner** — uses Responses API; VS Code extension explicitly unsupported
- **Future:** Additional runners as control surfaces are mapped

### Adapter Registration

Adapters are registered by agent identifier (e.g., `claude-code`, `codex`). The kernel resolves adapter selection based on the `agent` field in workflow step definitions:

```yaml
# OA01 workflow example
- id: implement
  opcode: RUN_AGENT
  agent: claude-code  # Kernel resolves to ClaudeCliRunner adapter
  prompt: task.implement_adr.v2
```

Registration mechanism: explicit import in kernel module (compile-time). Plugin discovery deferred to future phases if needed.

---

## Required Runner Interface

Each runner adapter must implement the following interface:

```python
class RunnerProtocol(Protocol):
    """Contract between kernel and runner adapters."""

    def run(
        self,
        plan: RunPlan,
        workspace: WorkspaceContext,
        policy: RunPolicy,
        limits: RunLimits,
    ) -> RunResult:
        """Execute agent task and return normalized result."""
        ...
```

Where:

| Type | Purpose |
|------|---------|
| `RunPlan` | Task/prompt reference, inputs, expected outputs |
| `WorkspaceContext` | Isolated git context (worktree path, branch, base commit) |
| `RunPolicy` | Tool/permission constraints (see Policy Layering below) |
| `RunLimits` | Wall-clock timeout, idle timeout |
| `RunResult` | Artifact paths, termination state, captured events |

### Policy Layering

`RunPolicy` operates at multiple levels:

| Layer | Mechanism | Example |
|-------|-----------|---------|
| **Native agent controls** | Pass-through to agent flags | `--allowedTools`, `--disallowedTools` |
| **Kernel blocklist** | Regex command filter (OA02 spike pattern) | Block `rm -rf`, `git push --force` |
| **Post-hoc diff policy** | OA01 policy prompt enforcement | Forbidden paths, allowed operations |

Adapters apply native controls when available. Kernel blocklist provides defense-in-depth. Post-hoc diff policy (OA01) provides semantic enforcement after execution.

---

## Capture Strategy Rule (Mandatory)

Runner adapters MUST choose capture mechanisms in the following order of preference:

1. **Native structured streams** (e.g., SDK events, `--output-format stream-json`)
2. **Plain stdout/stderr capture** (e.g., `--print` mode)
3. **PTY/TTY capture** (only when required for interactive/TTY-gated modes)

**PTY is explicitly optional**, not foundational. It is a tool for specific situations, not a default architectural assumption.

### Why This Order

| Mechanism | Pros | Cons |
|-----------|------|------|
| Structured streams | Clean parsing, typed events, designed for automation | Not all agents support |
| stdout/stderr | Simple, portable, no terminal complexity | May lose formatting/progress |
| PTY | Full fidelity for interactive modes | ANSI noise, terminal sizing, prompt detection complexity |

---

## OA02 Defaults Now Retired

The following OA02 spike defaults are **retired** (not banned — available when explicitly needed):

| OA02 Default | OA03 Position |
|--------------|---------------|
| PTY-first headless capture | Use structured streams or stdout first; PTY only when required |
| Heartbeat primarily from PTY output | Use native events when available; fall back to output monitoring |
| Terminal prompt-detection as primary safety | Use native permission/tool gating when surface provides it |

These mechanisms remain available for adapters that need them (e.g., wrapping an interactive-only agent). They are not the default architectural assumption.

---

## ADR Gate: Control Surface Mapping Requirement

**Mandatory requirement:**

> No ADR proposing an agent runner (OA03.x) may be written until the agent's control surface is fully mapped and documented.

This mapping MUST include:

| Required Element | Description |
|------------------|-------------|
| **Authoritative documentation** | Links to official CLI/SDK docs |
| **Invocation modes and flags** | All relevant modes (`--print`, `--output-format`, etc.) |
| **IO model** | Stateless vs persistent, session handling |
| **Permission/safety controls** | `--allowedTools`, sandboxing, confirmation prompts |
| **Output formats** | JSON, stream-JSON, plain text, etc. |
| **Experiment matrix** | Minimal tests validating documented claims |

This mapping becomes an appendix or prerequisite artifact to any OA03.x ADR.

**Rule:** ADR authors must treat undocumented behavior as **unknown**, not assumed. If official docs don't describe a capability, don't architect around it.

---

## OA03.x Follow-Ons

This ADR authorizes the following children:

| ADR | Target Surface | Best For | Invocation Model |
|-----|----------------|----------|------------------|
| **ADR-OA03.1** | Claude Code CLI | Exploration, refactoring, review | CLI (`--print` mode) |
| **ADR-OA03.2** | Codex | Implementation, mechanical coding | API (Responses API) |
| **Additional** | As needed | Task-dependent | Surface-dependent |

### Agent Positioning

The two primary agents have complementary strengths:

| Agent | Invocation | Workspace Access | Optimal Tasks |
|-------|------------|------------------|---------------|
| **Claude Code** | CLI, filesystem-native | Direct filesystem | Exploratory work, refactoring, code review, analysis |
| **Codex** | API, tool-driven | Explicit tool calls | Implementation, ADR execution, mechanical coding |

This division reflects each agent's design, not a hard constraint. The Planner may route tasks based on capability metadata and task characteristics.

### OA03.x ADR Requirements

Each OA03.x ADR:

- Targets one control surface
- Includes full control surface mapping as appendix (per ADR Gate requirement)
- Describes how it satisfies the kernel contract
- Documents capture strategy selection rationale
- Specifies tool surface (if applicable)

---

## Consequences

### Positive

- Prevents architecture built on false interaction assumptions
- Allows each agent surface to evolve independently
- Preserves OA02 learnings as valid experimental evidence
- Keeps the kernel small, testable, and durable
- Makes capture strategy explicit and justified per-adapter

### Negative / Tradeoffs

- Requires upfront documentation discipline (control surface mapping)
- Higher ADR count (one per agent surface)
- Runners are not interchangeable at the invocation level
- Must update OA03.x ADRs when agent surfaces change

---

## Alternatives Considered

### 1. Unified Runner with Feature Flags

**Approach:** Single runner class with conditional logic for each agent surface.

**Rejected because:**

- Creates a monolithic component that grows with each new agent
- Feature flag sprawl makes testing difficult
- Harder to reason about individual agent behaviors
- Violates single-responsibility principle

### 2. Normalize All Agent Invocation to PTY

**Approach:** Force all agents through PTY wrapper for uniform capture.

**Rejected because:**

- OA02 spike proved PTY is unnecessary for Claude Code `--print` mode
- Adds complexity where simpler capture suffices
- PTY has portability concerns (Windows, containers)
- Conflicts with agents that provide structured output natively

### 3. Defer Architecture Until More Agents Tested

**Approach:** Continue spike-style ad-hoc integration; formalize later.

**Rejected because:**

- Risk of accumulating technical debt
- Harder to refactor once multiple runners exist
- Phase 1 requires stable foundation now

---

## Open Questions

### 1. Kernel Protocol Definition

**Question:** Should the kernel-adapter interface be defined as a Python Protocol, ABC, or duck-typed convention?

**Options:** Protocol (explicit contract), ABC (shared implementation), duck-typed (flexible)

**Recommendation:** Protocol — aligns with project style guide, provides explicit contract without inheritance

**Decision needed by:** Phase 1 implementation start

### 2. Event Stream Schema

**Question:** Should event streams use strict common schema, or allow adapter-specific extensions?

**Options:**

- Strict common schema (all events identical across adapters)
- Common base + typed extensions (shared fields + adapter-specific)
- Fully adapter-specific (kernel only requires minimal fields)

**Recommendation:** Common base + typed extensions — balances consistency with flexibility

**Decision needed by:** Phase 1 implementation

### 3. Workspace Isolation Mechanism

**Question:** Should the kernel mandate git worktrees, or allow adapters to choose isolation mechanisms?

**Options:**

- Kernel-mandated worktrees (consistent, kernel controls)
- Adapter-chosen isolation (flexible, adapter controls)
- Configurable policy (kernel provides options, workflow chooses)

**Recommendation:** Kernel-mandated worktrees — simplifies kernel, proven in OA02 spike

**Decision needed by:** Phase 1 implementation

### 4. RunPolicy Enforcement Timing

**Question:** Should kernel blocklist be checked before invocation, during (via PTY monitoring), or both?

**Options:**

- Pre-invocation only (validate plan)
- Runtime monitoring (PTY/event stream)
- Both (defense-in-depth)

**Recommendation:** Pre-invocation for native controls; runtime monitoring only when PTY is used

**Decision needed by:** OA03.1 (Claude Runner) design

---

## Relationship to OA02

ADR-OA02 remains a **valid and successful Phase 0 spike**. It is not rejected or superseded in the deprecation sense.

OA03 defines **Phase 1 architecture** based on improved understanding from OA02. The relationship:

| OA02 Role | Description |
|-----------|-------------|
| **Experimental evidence** | Proved headless capture works; identified what works and what doesn't |
| **Architectural justification** | Learnings directly inform OA03 decisions |
| **Historical context** | Documents why PTY-first was attempted and why it's not the default |
| **Reference implementation** | Spike code informs Phase 1 implementation |

OA02's status remains `accepted` (spike completed successfully). OA03 does not supersede OA02 — it builds on OA02's evidence to define production architecture.

---

## Related ADRs

- [ADR-OA01: Agent Orchestration Strategy](/architecture/agent-orchestration/adr/adr-oa01-agent-orchestration-strategy.md) — Parent strategy ADR (Prompt-Program Runtime valuation)
- [ADR-OA02: Phase 0 Protocol Spike](/architecture/agent-orchestration/adr/adr-oa02-phase-0-protocol-spike.md) — Spike that informed this architecture
- [ADR-PV01: Provenance Tracing Strategy](/architecture/provenance/adr/adr-pv01-provenance-tracing-strat.md) — Foundation provenance infrastructure

---

## As-Built Notes & Addendums

*Reserved for post-implementation updates. Never edit the original Context/Decision/Consequences sections — always append addendums here.*
