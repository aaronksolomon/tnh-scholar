---
title: "ADR-OA01.1: TNH-Conductor — Provenance-Driven AI Workflow Coordination (v2)"
description: "Strategic architecture for coordinating external AI agents through bounded, auditable, human-supervised workflows with CLI opcode tooling"
type: "strategy"
owner: "aaronksolomon"
author: "Aaron Solomon, GPT 5.2, Claude Opus 4.5"
status: accepted
created: "2026-01-29"
updated: "2026-02-07"
parent_adr: "adr-oa01-agent-orchestration-strategy.md"
---

# ADR-OA01.1: TNH-Conductor — Provenance-Driven AI Workflow Coordination (v2)

Strategic architecture for coordinating external AI agents through bounded, auditable, human-supervised workflows.

- **Status**: Accepted
- **Type**: Strategy ADR
- **Date**: 2026-01-29
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, GPT 5.2, Claude Opus 4.5
- **Supersedes**: [ADR-OA01](/architecture/agent-orchestration/adr/adr-oa01-agent-orchestration-strategy.md)

---

## Context

TNH-Scholar is a long-lived system for AI-assisted study, translation, and analysis of the teachings of Thich Nhat Hanh and the Plum Village tradition. The project explicitly embraces **AI leverage not only for content work, but for building and evolving the system itself**.

The possibility exists to coordinate **AI coding agents exposed via official CLI interfaces** (e.g., **Claude Code CLI**, **Codex CLI**) in a way that:

- Enables semi-autonomous progress
- Preserves human authority and review
- Avoids brittle "autonomous agent" designs
- Produces auditable, intelligible work products
- Fits naturally into an engineering workflow (git, branches, reviews)

These agents are treated not as APIs to be wrapped, but as **already-agentic systems invoked through stable command-line surfaces**, consistent with standard developer tooling.

### The Problem: "Agents are Hard"

Early experimentation — and industry analysis (see Armin Ronacher's *"Agents are Hard"*) — shows that treating LLMs as either:

- purely conversational assistants, or
- fully autonomous agents

both fail at scale.

Autonomous agents fail because they:

1. **Lose the "vibe"** — Context drift over long sessions  
2. **Get stuck in loops** — Recursive hallucination without external grounding  
3. **Lack visibility** — No way to understand why decisions were made  
4. **Cannot recover** — No rollback when things go wrong  

Traditional agent systems store state in chat history, making debugging impossible and recovery unreliable.

### The Opportunity: Provenance-First Coordination

TNH-Scholar's existing `tnh-gen` infrastructure provides the hardest prerequisite for reliable agent coordination: **provenance tracking**. Every transformation is logged with *why*, *what*, *who*, and *what changed*.

This makes TNH-Scholar uniquely positioned to introduce a coordinating component whose role is **interpretation, supervision, and sequencing** — not execution or autonomy.

### The Insight: "You Might Not Need MCP"

Mario Zechner's analysis (*"What if you don't need MCP?"*) identifies a complementary principle: **prefer repo-local CLI tools over heavyweight tool servers** as the agent integration surface.

- Tool servers (like MCP) add lifecycle complexity, schema maintenance, and runtime dependencies
- CLI commands are composable, versioned in git, self-documenting via `--help`, and testable like normal software
- CLI invocations + generated artifacts become the durable, auditable contract — not server state

This insight shapes how tnh-conductor integrates with sub-agents: **Claude Code CLI and Codex CLI are invoked as command-line tools**, and their transcripts, diffs, and artifacts form the stable handoff for supervision, evaluation, and provenance — rather than long-lived tool servers or UI-bound integrations.

---

## Core Valuation: The System is Written in English

> **tnh-conductor is a minimal enforcement kernel that executes versioned prompt-programs. The system's behavior is defined in English; code exists only for capture, enforcement, and execution.**

This valuation optimizes for:

- **Bootstrapped semi-autonomy** — Prompt libraries enable rapid iteration without code changes
- **Fast experimentation** — New workflows, policies, and evaluation criteria are prompt edits, not deployments
- **Auditability** — Humans can read and understand system behavior by reading prompts
- **Leverage** — AI agents can help write and improve the prompts that govern them

### What This Means in Practice

Traditional orchestration systems encode behavior in code: routing logic, validation rules, decision trees, output formatting. This creates a high barrier to iteration and makes the system opaque to non-programmers.

tnh-conductor inverts this: **behavior lives in versioned prompts; code provides the execution substrate**.

| Traditional Orchestration | Prompt-Program Runtime |
|---------------------------|------------------------|
| Routing logic in code | Triage prompts select workflows |
| Hardcoded validation rules | Policy prompts define allowed/forbidden behaviors |
| Decision trees in conditionals | Evaluation prompts determine status and next steps |
| Template-based output | Generation prompts produce journals and reports |
| Fixed agent selection | Capability prompts guide agent routing |

The kernel becomes small (300-1k lines) and stable. The prompt library becomes the "standard library" of system behavior — versioned, auditable, and evolvable.

### Tools as Commands, Not Servers

> "Prefer a small, composable CLI opcode surface (repo-local tools) over tool servers; treat CLI invocations + artifacts as the durable contract."

The same principle extends to agent tooling. Rather than building heavyweight tool servers (like MCP), we prefer **repo-local CLI commands** as the agent-facing tool surface:

| Property | Description |
|----------|-------------|
| **Composable** | Pipe-friendly, Unix-style; can chain with other tools |
| **Versioned** | Tools live in-repo and evolve with the codebase |
| **Low token overhead** | Agent doesn't need full tool schemas—just CLI help text |
| **Stable and testable** | Normal CLI software with tests, not ephemeral server state |

This is the "bash equivalent" of MCP: tools exist as code + help text, not as long-lived server interfaces. Tools are documented via `--help`, not separate schema files.

---

## Decision

We introduce a new strategic component called **tnh-conductor**.

> **tnh-conductor is a provenance-driven workflow coordinator that supervises bounded AI agents, evaluates their outputs (including conversational transcripts), and advances work through explicit, human-reviewable steps.**

It is not an autonomous agent.
It does not "do the work."
It does not replace human judgment.

### Core Thesis

> We will not ask an LLM to "do the work." We will ask an LLM to **emit a plan**, execute that plan via CLI tools (Claude Code, Codex), and validate the outputs.

This separation of **Conductor** (supervisor) and **Sub-Agent** (performer) is critical. The conductor reasons about intent, sequences steps, evaluates results, and records everything — while humans remain responsible authors of the system.

---

## Design Intent

### tnh-conductor Does

- Coordinate AI agents as skilled but bounded performers
- Execute predefined workflows step-by-step
- Capture full conversational transcripts and workspace effects
- Evaluate outcomes using a trusted planner model
- Queue work for periodic human review
- Record all actions and decisions in provenance (tnh-gen)

### tnh-conductor Does NOT

- Perform open-ended task discovery
- Maintain conversational memory across runs
- Make irreversible decisions
- Guarantee reproducibility (we claim "auditable," not "deterministic")
- Bypass git-based review and rollback
- Own project-level decisions
- Build or maintain heavyweight tool servers (prefer CLI opcodes)
- Attempt to capture agent UI panes (VS Code panels, Claude UI)

---

## Kernel vs Prompt-Program Layer

The system splits cleanly into two layers with distinct responsibilities:

### Kernel Layer (Code — Minimal, Stable)

The kernel handles **hard requirements** that cannot be expressed in prompts:

| Responsibility | Description |
|----------------|-------------|
| **Work-branch management** | Create/switch branches; prevent commits to main |
| **Transcript capture** | stdout/stderr capture (primary); PTY fallback for interactivity |
| **Workspace diff/status** | Capture git state before/after each step |
| **Policy enforcement** | Post-hoc diff checks against allowed/forbidden paths (code-based) |
| **Validator execution** | Run tests, lint, typecheck; capture results |
| **Event/provenance writes** | Record all actions to tnh-gen ledger |
| **Schema validation** | Validate workflow, prompt, and policy definitions |
| **Opcode execution** | Execute workflow steps sequentially per definition |

The kernel is **enforcement and capture**. It does not decide; it executes and records.

### Prompt-Program Layer (English — Expressive, Evolvable)

All system intelligence lives in versioned prompts:

| Prompt Type | Purpose |
|-------------|---------|
| **Task prompts** | Instructions for sub-agents (the "work") |
| **Policy prompts** | Allowed/forbidden behaviors, workspace constraints |
| **Evaluation prompts** | Planner criteria for success/partial/blocked/needs_human |
| **Triage prompts** | Route tasks to appropriate workflows |
| **Risk assessment prompts** | Classify changes by risk level |
| **Journal prompts** | Generate human-readable daily summaries |
| **Agent capability prompts** | Describe agent strengths for routing decisions |

Prompts are **versioned artifacts** stored in-repo. Workflows reference prompts by `id.version`. The planner can only select next steps from the allowed set — no open-ended branching.

### The Split in Action

```
User submits task: "Implement ADR-AT03"
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  PROMPT-PROGRAM LAYER                                       │
│                                                             │
│  triage.route_task.v1 → selects workflow: implement_adr     │
│  planner.evaluate_step.v1 → determines status               │
│  risk.assess_changes.v1 → flags breaking API change         │
│  journal.generate_daily.v1 → produces review summary        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  KERNEL LAYER                                               │
│                                                             │
│  Creates work branch: task/adr-at03-impl                    │
│  Executes opcode: RUN_AGENT(claude-code, prompt_id)         │
│  Captures: transcript.md, git diff, test results            │
│  Enforces: diff only touches allowed paths                  │
│  Records: all events to provenance ledger                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture

### High-Level Flow

```
Intent / ADR / Task
    ↓
tnh-conductor (workflow coordinator)
    ↓
Sub-Agent Invocation (Claude Code / Codex / Gemini)
    ↓
Captured Outputs (Transcript + Workspace Effects)
    ↓
Planner Evaluation
    ↓
Provenance Ledger (tnh-gen)
    ↓
Daily / Periodic Human Review
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      tnh-conductor                              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐    │
│  │   Workflow    │  │    Prompt     │  │     Planner       │    │
│  │  Definitions  │  │    Library    │  │    Evaluator      │    │
│  └───────────────┘  └───────────────┘  └───────────────────┘    │
│                              │                                  │
│  ┌───────────────────────────┴───────────────────────────────┐  │
│  │                  Protocol Layer                           │  │
│  │     (stdout/stderr capture, git diff/status, progress)    │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   Claude Code   │   │     Codex       │   │     Gemini      │
│   (Sub-Agent)   │   │   (Sub-Agent)   │   │   (Sub-Agent)   │
└─────────────────┘   └─────────────────┘   └─────────────────┘
         │                     │                     │
         └─────────────────────┴─────────────────────┘
                               │
         ┌─────────────────────┴─────────────────────┐
         ▼                                           ▼
┌─────────────────────────┐           ┌─────────────────────────┐
│    Validation Layer     │           │   Provenance Ledger     │
│  (tests, lints, checks) │           │      (tnh-gen)          │
└─────────────────────────┘           └─────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Conductor** | Workflow sequencing, step coordination, human escalation |
| **Planner Evaluator** | Interprets sub-agent outputs, determines status, proposes next steps |
| **Protocol Layer** | Captures transcript + workspace effects; emits progress events |
| **Sub-Agents** | Perform bounded tasks; emit artifacts (diffs, reviews, transcripts) |
| **Validation Layer** | Runs tests/lints; feeds errors to Planner (not sub-agent) |
| **Provenance Ledger** | Records everything; enables audit, replay, and rollback |

---

## Core Concept: Dual-Channel Sub-Agent Output

Sub-agents (Claude Code, Codex) are treated as **already-agentic systems**. Their output is therefore **not reduced to file diffs alone**.

Each sub-agent run produces two first-class outputs:

### Transcript Channel

- Full conversational log
- Self-reported success or failure
- Discovered blockers
- Suggested side paths
- Risk or uncertainty statements

This channel is treated as **semantic signal**, not noise.

### Workspace Channel

- Git diff (patch)
- New or modified files
- Tool and test output

**The system never assumes success based on either channel alone.**

The Planner Evaluator interprets both channels to determine actual status.

### Contradiction Detection

The Planner Evaluator must explicitly check for **consistency between channels**:

| Contradiction Type | Example | Classification |
|--------------------|---------|----------------|
| Transcript claims success, diff is empty | "Completed refactor" but no files changed | `partial` or `unsafe` |
| Transcript claims tests run, no validation artifacts | "All tests pass" but no test output captured | `partial` with `risk_flags` |
| Workspace shows changes outside stated scope | Diff includes files not mentioned in transcript | `unsafe` or `needs_human` |
| Transcript reports error, workspace shows commits | "Encountered blocker" but files modified | `needs_human` with `risk_flags` |

**Rule:** When the Planner detects contradictions between transcript claims and workspace reality, it must flag the status as `partial` or `unsafe` and emit `risk_flags` describing the discrepancy.

---

## Planner Evaluation Loop

After each sub-agent step, tnh-conductor invokes a **planner evaluation** using a trusted, higher-level model.

### Planner is Stateless (No Conversational Memory)

The Planner does **not** maintain conversational memory across evaluations. Each evaluation is independent — the Planner does not "remember" previous interactions or accumulate context over time.

However, to support multi-step workflows and prevent retry loops, the Planner receives a **provenance window**: explicit historical context from the last K steps (typically 2–3).

| Input | Source | Purpose |
|-------|--------|---------|
| `provenance_ids` | Last 2–3 step records | Prevent retry loops, understand multi-step context |
| `prior_statuses` | Previous step outcomes | Detect repeated failures |
| `prior_blockers` | Blockers from recent steps | Avoid re-attempting known blockers |

**This is not memory** — it is explicit, bounded context fed as structured inputs. The Planner cannot access arbitrary history; it receives only what the kernel explicitly provides.

### Planner Consumes

- Step intent (what we asked for)
- Transcript channel (what the agent said/did)
- Workspace diff summary (filesystem changes)
- Validation results (tests, lints)
- Provenance window (last K step records, for multi-step context)

### Planner Emits

| Output | Description |
|--------|-------------|
| **status** | `success` / `partial` / `blocked` / `unsafe` / `needs_human` |
| **blockers** | What prevented completion |
| **side_paths** | Discoveries or alternatives found |
| **risk_flags** | Concerns requiring attention |
| **next_step** | Proposed next step ID |
| **review_entries** | Items for human review queue |

**This is the only decision-making locus in the system.** Sub-agents are performers; the Planner is the evaluator.

---

## Workflow Bytecode Model

Workflows are **compiled intent** — explicit, declarative sequences that the kernel executes step-by-step with full provenance.

They define:

- Ordered steps (opcodes)
- Which sub-agent is invoked per step
- Required validation
- Review or gating semantics

Workflows **do not self-modify** and **do not branch implicitly**. Intelligence lives in the prompts they reference; control lives in the kernel.

### Opcode Layers

The system distinguishes two opcode surfaces:

#### Kernel Opcodes (Orchestration Primitives)

The kernel executes a small, fixed set of orchestration opcodes:

| Opcode | Description |
|--------|-------------|
| `RUN_AGENT` | Invoke sub-agent with prompt; capture transcript + workspace |
| `RUN_VALIDATION` | Execute tests/lint/typecheck; capture results |
| `EVALUATE` | Invoke planner to assess status and determine next step |
| `GATE` | Queue for review or block for approval |
| `ROLLBACK` | Reset work branch to pre-step state (deterministic cleanup) |
| `STOP` | Halt workflow (success, failure, or needs_human) |

Workflow YAML compiles to this opcode sequence. The kernel executes opcodes; it does not interpret intent.

#### Agent-Facing CLI Opcodes (Tool Surface)

The agent-facing tool surface is a set of repo-local CLI commands that sub-agents (or the kernel on their behalf) can invoke:

| Command | Purpose |
|---------|---------|
| `tnh context` | Print minimal repo context + ADR pointers |
| `tnh diff` | Diff stat + key hunks for current changes |
| `tnh test` | Run canonical test suite |
| `tnh lint` | Run linting checks |
| `tnh typecheck` | Run type checker |
| `tnh adr open <id>` | Open/display ADR by ID |
| `tnh adr list` | List available ADRs |
| `tnh runlog append` | Append structured entry to run log |

These commands are:

- **Composable**: Pipe-friendly, Unix-style
- **Versioned**: Live in-repo, evolve with codebase
- **Self-documenting**: `--help` provides all context agents need
- **Testable**: Normal CLI testing patterns apply

**Rationale**: This keeps the tool surface small, auditable, and avoids the complexity of maintaining server-based tool interfaces.

### ROLLBACK Semantics

`ROLLBACK` is a **deterministic cleanup opcode** triggered when the Planner returns `unsafe` or when policy violations are detected. It is narrowly scoped to git operations:

| Trigger | ROLLBACK Action |
|---------|-----------------|
| `unsafe` status from Planner | Reset work branch to pre-step commit |
| Policy violation in diff | Discard worktree changes on work branch |
| Explicit workflow definition | Reset to specified checkpoint |

**Constraints:**

- ROLLBACK only affects the work branch — never main or protected branches
- ROLLBACK is deterministic: same inputs produce same git state
- ROLLBACK does not "undo" arbitrary state — it resets to a known git checkpoint
- All ROLLBACK actions are recorded in provenance

**Not a time machine:** ROLLBACK is a hygiene mechanism for recovering from unsafe steps, not a general-purpose "undo to any point" capability.

### Example Workflow Definition

```yaml
workflow: implement_adr
version: 1
description: "Implement an ADR with review and approval gates"

steps:
  - id: implement
    opcode: RUN_AGENT
    agent: claude-code
    prompt: task.implement_adr.v2
    inputs: [adr_id, target_paths]
    policy: policy.workspace_safety.v1

  - id: validate
    opcode: RUN_VALIDATION
    run: [tests, lint, typecheck]
    on_fail: STOP

  - id: evaluate
    opcode: EVALUATE
    prompt: planner.evaluate_step.v1
    # Planner determines: success → continue, blocked → STOP, needs_human → GATE

  - id: review
    opcode: RUN_AGENT
    agent: claude-code
    prompt: task.review_diff.v1
    inputs: [diff, adr_id]

  - id: approval
    opcode: GATE
    gate: queue_for_review
```

### Schema Versioning

Workflow and prompt schemas are explicitly:

- **Versioned** in the schema definition
- **Validated** before execution
- **Stored** (schema version) in provenance records

### Workflow as "Bytecode"

This framing clarifies responsibilities:

- **Workflow YAML** = source code (human-readable intent)
- **Opcode sequence** = bytecode (kernel-executable steps)
- **Prompts** = the "functions" called by opcodes
- **Kernel** = the runtime that executes bytecode
- **CLI opcodes** = the "syscalls" available to sub-agents

The system is auditable because you can read the workflow (what we intended), the prompts (how we instructed), and the provenance (what actually happened).

---

## Human-in-the-Loop Model

Human oversight is **periodic and asynchronous by default**.

- Sub-agent work accumulates in a daily or periodic review journal
- Humans review diffs, planner assessments, and risk flags
- Humans decide whether to merge, revise, discard, or redirect work

**Real-time approval is optional and explicit.**

### Gate Types

| Gate | Behavior |
|------|----------|
| `queue_for_review` | Non-blocking; continues workflow, adds to journal |
| `requires_daily_review` | Same as above, explicit naming |
| `blocking_approval` | Halts workflow until human approves |

### Daily Review Journal

```markdown
# TNH-Journal: 2026-01-14

## Completed Tasks
- [x] Implemented ADR-AT03 refactor (3 files changed)
- [x] Fixed type errors in text_object.py

## Pending Review
- [ ] Diff: src/tnh_scholar/ai_text_processing/ (142 lines)
- [ ] Risk flag: Breaking change to public API

## Planner Assessments
→ implement_adr.v1 / step: implement
  Status: partial
  Blocker: "Unclear which error handling pattern to use"
  Side path: "Suggested Result type over exceptions"

## Provenance
- Workflow: implement_adr.v1
- Agent: claude-code (claude-sonnet-4)
- Transcript: .tnh-gen/transcripts/2026-01-14-001.md
```

---

## Rollback and Safety Model

Rollback is defined **strictly via git**.

- All work occurs on designated work branches
- Code-level guardrails prevent commits to main
- Recovery uses standard git operations
- No additional snapshot or sandbox system is required

This keeps the safety model simple, reliable, and aligned with standard engineering practice.

---

## Role of tnh-gen

tnh-gen is the **provenance and narrative substrate** of the system.

It records:

- Workflow executions
- Sub-agent transcripts
- Workspace diffs
- Planner decisions
- Human review outcomes
- Human feedback events

It enables auditability, review generation, and long-term system memory **without agent memory**.

**tnh-gen does not make decisions.** It is the ledger, not the judge.

### HUMAN_FEEDBACK Event Type

To accumulate human preferences and decisions without introducing "agent memory," the provenance ledger includes a dedicated event type:

```yaml
event_type: HUMAN_FEEDBACK
timestamp: 2026-01-14T10:30:00Z
workflow_id: implement_adr.v1
step_id: review
content:
  decision: "approved_with_changes"
  comments: "Good approach, but prefer Result type over exceptions"
  rationale: "Aligns with project error-handling patterns"
  related_items:
    - provenance_id: abc123
    - provenance_id: def456
```

**Purpose:**

- Capture human decisions, comments, and rationale from daily journal reviews
- Provide structured feedback that can inform future triage and evaluation prompts
- Enable pattern discovery over time (e.g., "human frequently overrides X classification")
- Avoid agent memory while preserving institutional knowledge in the ledger

---

## Protocol Layer Specification

The Protocol Layer is explicitly bounded to:

| Responsibility | Description |
|----------------|-------------|
| **Transcript capture** | stdout/stderr capture (primary); PTY fallback for unexpected interactivity |
| **Workspace capture** | `git diff` / `git status` before/after |
| **Progress events** | Heartbeats, completion signals |
| **Heartbeat monitoring** | Detect stalled agents; kill and capture on timeout |
| **Negative path capture** | Handle hangs, prompts, crashes gracefully |

The Protocol Layer is **NOT** responsible for:

- Enforcing prompt contracts (post-hoc verification instead)
- Ensuring determinism (we claim "bounded," not "reproducible")
- Parsing structured output from agents (transcripts are semantic, not structured)
- Capturing agent UI panes (VS Code panels, Claude UI — too fragile)

**Rationale:** This avoids architectural collapse due to CLI idiosyncrasies across different agent tools.

### Artifact Contract

The integration point between conductor and sub-agents is **durable repo artifacts**, not UI scraping:

- **Required per run**: AGENTLOG entry + run summary + git diffs
- **Artifacts are the stable handoff** for meta-agent evaluation and journaling
- **CLI invocations are captured** in provenance alongside artifacts

This ensures the system remains portable across different agent UIs and versions.

### Negative Path Handling

The kernel must handle failure modes that prevent normal completion:

| Failure Mode | Detection | Response |
|--------------|-----------|----------|
| **Agent hang** | No stdout/stderr output for N seconds | Kill process, capture transcript tail, mark `blocked` |
| **Interactive prompt** | Detected Y/N, auth, 2FA, confirmation patterns | Kill process, mark `blocked`, flag for review |
| **Tool crash** | Non-zero exit code | Capture stderr, mark `blocked` with cause |
| **Timeout** | Wall-clock limit exceeded | Kill process, capture state, mark `blocked` |

### Heartbeat Monitor

The kernel implements a heartbeat monitor with the following behavior:

1. **Monitor interval:** Configurable timeout (default: 60 seconds)
2. **Signal:** Any stdout/stderr output or filesystem event resets the timer
3. **On timeout:**
   - Kill the sub-agent process
   - Capture last N lines of transcript
   - Write `blocked` provenance record with cause classification
   - Queue for human review

**Rule:** If no output or events for the configured interval, the kernel kills the process, marks the step as `blocked`, captures the transcript tail, and queues for review.

---

## Prompt Library as Standard Library

The prompt library is the **standard library** of system behavior. Just as a programming language's stdlib provides reusable functions, the prompt library provides reusable behavior definitions.

Prompts are **named, versioned artifacts** organized by type:

### Prompt Types

| Type | Namespace | Purpose |
|------|-----------|---------|
| **Task** | `task.*` | Instructions for sub-agents (the actual work) |
| **Policy** | `policy.*` | Allowed/forbidden behaviors, workspace constraints |
| **Evaluation** | `planner.*` | Criteria for assessing outcomes |
| **Triage** | `triage.*` | Route tasks to workflows |
| **Risk** | `risk.*` | Classify changes by risk level |
| **Journal** | `journal.*` | Generate human-readable summaries |
| **Agent** | `agent.*` | Agent capability descriptions for routing |

### Example: Task Prompt

```yaml
prompt: task.implement_adr
version: 2
type: task

inputs:
  - name: adr_id
    type: string
  - name: target_paths
    type: list[path]

instruction: |
  Implement the specified ADR according to its design decisions.

  Focus on:
  - Following existing code patterns in the target paths
  - Minimal changes to achieve the ADR's goals
  - Clear commit messages referencing the ADR

  Do NOT:
  - Expand scope beyond what the ADR specifies
  - Refactor unrelated code
  - Add features not in the ADR

outputs:
  - name: diff
    type: unified_diff
```

### Example: Policy Prompt

```yaml
prompt: policy.workspace_safety
version: 1
type: policy

description: |
  Defines allowed and forbidden workspace operations.

allowed_paths:
  - "src/tnh_scholar/**"
  - "tests/**"
  - "docs/**"

forbidden_paths:
  - "*.lock"
  - "pyproject.toml"
  - ".github/**"
  - "*.env*"

forbidden_operations:
  - "Creating new top-level directories"
  - "Deleting existing files without explicit instruction"
  - "Modifying CI/CD configuration"

# Kernel enforces via post-hoc diff check
```

### Example: Evaluation Prompt

```yaml
prompt: planner.evaluate_step
version: 1
type: evaluation

instruction: |
  Evaluate the sub-agent's work based on transcript and workspace diff.

inputs:
  - step_intent: "What we asked the agent to do"
  - transcript: "Full conversational output"
  - diff_summary: "Files changed, lines added/removed"
  - validation_results: "Test/lint/typecheck output"

criteria:
  success: |
    The diff directly addresses the step intent.
    Tests pass. No new lint warnings.
    Agent reported completion without uncertainty.

  partial: |
    Some progress toward intent, but not complete.
    Agent reported blockers or expressed uncertainty.
    Tests pass but work is incomplete.

  blocked: |
    Agent could not proceed.
    Hard blocker: missing information, architectural decision needed,
    dependency issue, or unclear requirements.

  needs_human: |
    Changes touch sensitive areas (public API, security, config).
    Agent expressed low confidence.
    Risk flags present in diff.

  unsafe: |
    Policy violations detected in diff.
    Forbidden paths modified.
    Scope expansion beyond intent.

outputs:
  status: "success | partial | blocked | needs_human | unsafe"
  blockers: "List of blocking issues"
  side_paths: "Discovered alternatives or opportunities"
  risk_flags: "Concerns requiring attention"
  next_step: "Proposed next step ID or STOP"
  review_entries: "Items for human review queue"
```

### Example: Triage Prompt

```yaml
prompt: triage.route_task
version: 1
type: triage

instruction: |
  Given a task description, determine which workflow applies.

routing_rules: |
  - If task references an ADR and asks to implement it → implement_adr
  - If task is a bug fix with clear reproduction → fix_bug
  - If task asks for code review → review_code
  - If task asks for analysis or research (no code changes) → research
  - If task involves documentation only → update_docs
  - If unclear or ambiguous → needs_human (queue for clarification)

outputs:
  workflow_id: "Selected workflow"
  confidence: "high | medium | low"
  reasoning: "Why this workflow was selected"
```

### Example: Risk Assessment Prompt

```yaml
prompt: risk.assess_changes
version: 1
type: risk

instruction: |
  Classify the risk level of proposed changes.

criteria:
  high_risk: |
    - Changes to authentication, authorization, or security code
    - Modifications to public API signatures
    - Database schema changes
    - Changes affecting data integrity or persistence
    - Dependency version changes

  medium_risk: |
    - Breaking changes to internal APIs
    - New dependencies added
    - Configuration changes
    - Changes to CLI interfaces

  low_risk: |
    - Documentation changes
    - Test additions or fixes
    - Internal refactoring with no API changes
    - Comment and docstring updates

outputs:
  risk_level: "high | medium | low"
  risk_factors: "List of specific concerns"
  recommended_review: "blocking | daily | none"
```

### Example: Journal Generation Prompt

```yaml
prompt: journal.generate_daily
version: 1
type: journal

instruction: |
  Generate a human-readable daily journal from workflow executions.

inputs:
  - executions: "Today's workflow runs with outcomes"
  - assessments: "Planner evaluations"
  - review_items: "Queued review entries"

format: |
  # TNH-Journal: {date}

  ## Completed Tasks
  [List tasks with status=success, one line each with file counts]

  ## In Progress
  [List tasks with status=partial, noting blockers]

  ## Pending Review
  [List items queued for review, with paths and risk levels]

  ## Blockers & Decisions Needed
  [List items with status=blocked or needs_human]

  ## Planner Assessments
  [Summarize key evaluations, especially for non-success outcomes]

  ## Provenance
  [Workflow IDs, agent versions, transcript paths]
```

### Verification is Post-Hoc

Prompts define intent and expectations. **Enforcement happens after execution**:

- Diff the filesystem before/after
- Check for policy violations (forbidden paths, operations)
- Validate outputs against expected structure
- Flag discrepancies for human review

No sandbox in Phase 1. Rely on branch isolation + diff-policy + human review.

### Policy Enforcement Model

Policy prompts are **English definitions** of allowed and forbidden behaviors. However, **enforcement is code-based**:

| Layer | Role |
|-------|------|
| **Policy prompts** | Human-readable definitions of constraints (the "what") |
| **Kernel enforcement** | Code that checks diffs against policy rules (the "how") |

**Enforcement flow:**

1. Sub-agent completes step, producing workspace diff
2. Kernel parses policy prompt's `allowed_paths`, `forbidden_paths`, `forbidden_operations`
3. Kernel checks diff against these rules (deterministic code check)
4. If violations detected: kernel auto-marks status as `unsafe` **before** Planner evaluation
5. Planner receives violation report as input; cannot override kernel safety decisions

**Key principle:** The kernel can autonomously mark a step `unsafe` when forbidden paths are touched — this happens before and independent of Planner/human review. Policy definitions are English; enforcement is code.

---

## Anti-Goals and Constraints

To prevent scope creep, the following are explicit **anti-goals**:

### Anti-Goal: No Heavyweight Tool Servers

Don't build or maintain heavyweight "tool servers" (like MCP) unless there is a clear win.

**Prefer "tools as commands" first.** Only escalate to server-based tooling when:

- Streaming/async is required
- Stateful service is unavoidable
- Performance demands it

### Anti-Goal: No UI Scraping

Don't attempt to capture agent UI panes (VS Code panels, Claude UI). This is fragile and non-portable. Rely on artifacts and transcripts instead.

### Anti-Goal: No Agent Memory

Don't introduce conversational memory that persists across runs. Use explicit provenance windows instead.

### Anti-Goal: No API Codex Runner

Don't build API-based Codex execution surfaces. Phase-0 targets CLI-based invocation (Codex CLI) for consistency with the "tools as commands" principle.

---

## Implementation Roadmap

### Phase 0: Protocol Layer Spike (De-risking)

**Goal:** Prove headless agent invocation + transcript capture works reliably

**Rationale:** The Protocol Layer is the highest-risk component. If we cannot reliably capture stdout/stderr and git diffs from headless agent sessions, the entire architecture is blocked. This spike de-risks before committing to full implementation. API-based Codex runner experiments are superseded; Phase-0 now explicitly targets Codex CLI as the production execution surface.

**Note on PTY:** Early spikes explored PTY capture for transcript completeness. Current findings show both Claude Code CLI and Codex CLI emit bounded, non-interactive stdout/stderr in normal operation. PTY is now a **fallback only** — retained to detect/kill unexpected interactive prompts (auth, Y/N), but not a primary dependency.

**Spike Scope:**

- Headless invocation of Claude Code CLI (`claude --print`) and Codex CLI
- Transcript capture (raw + normalized)
- Git diff capture before/after
- Heartbeat monitoring + inactivity timeout kill
- Minimal provenance event emission into `tnh-gen`
- Work-branch isolation for each run

**Target Surfaces:**

| Agent | Invocation Method | Capture Method |
|-------|-------------------|----------------|
| Claude Code CLI | `claude --print` mode | stdout/stderr (PTY fallback) |
| Codex CLI | CLI invocation | stdout/stderr (PTY fallback; confirm in spike) |

**Spike Deliverable:**

```bash
# Minimal CLI that proves the capture chain
tnh-conductor-spike run --agent claude-code --task "List files in src/"
# Outputs:
#   transcript.md (full session)
#   diff.patch (git changes, if any)
#   run.json (metadata)
#   events.ndjson (provenance stream)
```

**Success Criteria (Pass/Fail):**

- [ ] Headless invocation completes without manual interaction
- [ ] Full transcript captured (not truncated)
- [ ] Git diff accurately reflects workspace changes
- [ ] Provenance record written with correct metadata
- [ ] Handles agent hang: kills process after timeout
- [ ] Captures last N lines of transcript on failure
- [ ] Writes `blocked` provenance record with cause classification on failure
- [ ] Emits progress events independent of filesystem changes

**Spike Deliverables:**

| Artifact | Description |
|----------|-------------|
| `tnh_conductor_spike.py` | CLI module implementing the spike |
| `transcript.md` | Full stdout/stderr session log |
| `diff.patch` | Git changes (if any) |
| `run.json` | Run metadata |
| `events.ndjson` | Event stream (newline-delimited JSON) |
| `SPIKE_REPORT.md` | Findings, gotchas, recommendations |

**Decision Point:** If spike fails, evaluate alternative approaches (SDK, API-only, different agent surface) before proceeding.

---

### Phase 1: Headless Controller (Walking Skeleton)

**Goal:** CLI command that wraps a `claude-code` session with full kernel capabilities

**Deliverables:**

- `tnh-conductor` CLI entry point
- stdout/stderr capture for transcripts (PTY fallback for interactivity)
- Git diff capture for workspace changes
- Work-branch creation and management
- Provenance indexing

**Walking Skeleton:**

```bash
tnh-conductor --task "Summarize current progress"
# Creates work branch: task/summarize-progress-001
# Sends to Claude Code via CLI
# Captures transcript + diff
# Records in provenance store
# Returns to original branch
```

**Success Metric:** Output recorded in provenance without manual copy-paste; work isolated on branch

### Phase 2: Planner Evaluation Loop

**Goal:** Implement the decision-making component

**Deliverables:**

- Planner that consumes transcript + diff + validation
- Status classification logic
- Next-step determination
- Review queue generation

### Phase 3: Workflow Engine

**Goal:** Declarative workflow execution

**Deliverables:**

- YAML workflow parser
- Step sequencing
- Validation integration
- Gate semantics

### Phase 4: Prompt Library

**Goal:** First-class prompt management

**Deliverables:**

- Prompt versioning and storage
- Template rendering
- Post-hoc contract verification

### Phase 5: Multi-Agent Support

**Goal:** Coordinate multiple agent types

**Deliverables:**

- Codex integration
- Gemini integration (optional)
- Agent capability routing

### Phase 6: VS Code Integration

**Goal:** Visual control surface

**Deliverables:**

- Provenance graph visualization
- Real-time workflow monitoring
- Review journal browser

### Future: Prompt Regression Testing

Since prompts are "code" in this architecture, prompt changes can shift system behavior in unexpected ways. A future capability (Phase 7+) is **prompt regression testing**:

**Concept:**

- Maintain a test bench of recorded transcripts, diffs, and expected classifications ("golden runs")
- When evaluation or policy prompts are updated, run them against golden runs
- Detect if prompt changes shift classifications unexpectedly (e.g., previously `success` now `partial`)
- Flag regressions for human review before deploying prompt updates

**Goal:** Treat prompt versioning with the same rigor as code versioning — changes are testable and regressions are detectable.

This is a planned capability, not Phase 1 scope.

---

## Consequences

### Positive

- **Clear separation of concerns** — Conductor coordinates; agents perform; humans decide
- **Robust to agent quirks** — Dual-channel output handles diverse agent behaviors
- **Scales with complexity** — Workflow model supports arbitrarily complex sequences
- **Provider-agnostic** — Same architecture works with Claude Code, Codex, Gemini
- **Auditable by design** — Full provenance trail for every action
- **Aligns with engineering practice** — Git branches, async review, standard tooling
- **Smaller tool surface** — CLI opcodes are simpler than server-based tool interfaces
- **Better provenance** — CLI invocations + artifacts are first-class, versioned, auditable
- **Less brittleness** — No server schemas to drift; tools are self-documenting via `--help`

### Tradeoffs

- **Less "magical" autonomy** — Explicit workflows over emergent behavior
- **Slower than unsupervised agents** — Human review adds latency
- **Requires disciplined workflow definitions** — No ad-hoc task discovery

**These tradeoffs are intentional.** The goal is reliable, auditable progress — not maximum speed.

### Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| **CLI wrapping fragility** | Protocol Layer only captures transcript + diffs; no structured parsing |
| **Planner evaluation quality** | Use higher-capability model; iterate on evaluation prompts |
| **Workflow rigidity** | Support workflow versioning and evolution; human can redirect |
| **Review backlog** | Risk flags prioritize urgent items; blocking gates for critical paths |

---

## Open Questions

### 1. Claude Code CLI Wrapping

**Question:** Can Claude Code be reliably wrapped for headless operation?

**Options:** `--print` mode (confirmed), SDK approach, PTY fallback

**Decision needed by:** Phase 1

### 2. Planner Model Selection

**Question:** Should the Planner use the same model as sub-agents or a different one?

**Options:** Same (consistency), cheaper (cost), more capable (quality)

**Decision needed by:** Phase 2

### 3. Progress Signal Thresholds

**Question:** What constitutes a "stalled" agent?

**Options:** Time-based, event-based, agent-reported

**Decision needed by:** Phase 2

---

## Terminology

| Term | Definition |
|------|------------|
| **Conductor** | Workflow coordinator and supervisor (tnh-conductor) |
| **Kernel** | Minimal code layer: enforcement, capture, opcode execution |
| **Prompt-Program** | Versioned prompts that define system behavior (the "English code") |
| **Sub-Agent** | External AI system performing bounded tasks (Claude Code, Codex) |
| **Planner** | Trusted evaluator model that interprets outcomes |
| **Kernel Opcode** | Orchestration primitive: RUN_AGENT, VALIDATE, EVALUATE, GATE, STOP |
| **CLI Opcode** | Agent-facing tool: `tnh test`, `tnh diff`, `tnh context`, etc. |
| **Transcript Channel** | Conversational output from sub-agent |
| **Workspace Channel** | Filesystem effects (diffs, new files) |
| **Daily Review** | Periodic human gating and approval |
| **Provenance Ledger** | tnh-gen's record of all actions and decisions |
| **Policy Prompt** | English definition of allowed/forbidden behaviors |
| **Evaluation Prompt** | English criteria for planner status classification |
| **Artifact Contract** | Required outputs per run: AGENTLOG + summary + diffs |

---

## ADR Roadmap

This strategy ADR establishes the foundation. Implementation details are captured in follow-on ADRs.

### Current / Active

| ADR | Title | Scope |
|-----|-------|-------|
| **ADR-OA02** | Phase 0 Protocol Spike | Headless capture contract and safety controls |
| **ADR-OA03** | Agent Runner Architecture | Kernel + adapter pattern, runner contracts |
| **ADR-OA03.1** | Claude Code Runner | `--print` mode, stdout/stderr-first capture |
| **ADR-OA03.2** | Codex Runner (API) | Responses API approach (historical) |
| **ADR-OA03.3** | Codex CLI Runner | CLI-based execution via `codex exec`; supersedes OA03.2 |
| **ADR-OA04** | Workflow Schema + Opcode Semantics | YAML format, opcode definitions, ROLLBACK semantics |
| **ADR-OA05** | Prompt Library Specification | Prompt artifact format, versioning, template rendering |
| **ADR-OA06** | Planner Evaluator Contract | Input/output schemas, contradiction checks, provenance window |
| **ADR-OA07** | Diff-Policy + Safety Rails | Allowed/forbidden paths, dependency changes, escalation rules |
| **ADR-OA08** | Prompt Regression Testing Harness | Golden runs, classification drift detection (future) |

### Historical / Superseded

| ADR | Title | Status |
|-----|-------|--------|
| **ADR-OA01** | TNH-Conductor Strategy (v1) | Superseded by this document |
| **ADR-OA03.2** | API-Based Codex Runner | Superseded by ADR-OA03.3 (CLI approach) |

Each ADR will be created as implementation progresses through the phases defined in this strategy.

---

## Related ADRs

### Related Existing ADRs

- [ADR-OA01](/architecture/agent-orchestration/adr/adr-oa01-agent-orchestration-strategy.md) — Original strategy (superseded by this document)
- `adr-pv01-provenance-tracing-strat.md` — Foundation provenance infrastructure
- `adr-tg01-cli-architecture.md` — CLI patterns for tnh-gen
- `adr-at04-ai-text-processing-platform-strat.md` — Related orchestration patterns

---

## References

- Armin Ronacher, "Agents are Hard" — https://lucumr.pocoo.org/2025/11/21/agents-are-hard/
- Mario Zechner, "What if you don't need MCP?" — https://mariozechner.at/posts/2025-11-02-what-if-you-dont-need-mcp/
- Claude Code CLI documentation — https://code.claude.com/docs/en/cli-reference
- OpenAI Codex CLI documentation — https://developers.openai.com/codex/cli

---

## Summary

tnh-conductor is a **prompt-program runtime**: a minimal enforcement kernel that executes workflows defined in English.

The system is written in English. Code exists for capture, enforcement, and execution — not for encoding behavior.

Key principles:

- **Kernel is minimal** (~500 lines): branch management, stdout/stderr capture, diff capture, policy enforcement, opcode execution
- **Behavior lives in prompts**: task instructions, policies, evaluation criteria, triage rules, journal formats
- **Workflows are bytecode**: YAML compiles to opcodes; intelligence lives in the prompts they reference
- **CLI opcodes over tool servers**: prefer small, composable repo-local commands as the agent tool surface
- **Artifact contract**: CLI invocations + durable artifacts are the stable handoff—not UI scraping
- **Enforcement is post-hoc**: verify diffs against policies after execution, not during
- **Humans remain authors**: daily review, blocking gates for high-risk changes, full provenance trail

tnh-conductor enables semi-autonomous progress without surrendering control. It coordinates, listens, evaluates, and records — while humans remain responsible authors of the system.

---

*This ADR establishes the strategic foundation for TNH-Scholar's agent coordination system: a prompt-program runtime enabling bounded, auditable, provenance-driven development workflows with CLI opcode tooling.*
