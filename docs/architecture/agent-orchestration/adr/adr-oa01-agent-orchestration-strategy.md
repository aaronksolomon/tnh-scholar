---
title: "ADR-OA01: TNH-Conductor — Provenance-Driven AI Workflow Coordination"
description: "Strategic architecture for coordinating external AI agents (Claude Code, Codex) through bounded, auditable, human-supervised workflows"
type: "strategy"
owner: "aaronksolomon"
author: "Aaron Solomon, GPT 5.2, Claude Opus 4.5"
status: proposed
created: "2026-01-14"
---

# ADR-OA01: TNH-Conductor — Provenance-Driven AI Workflow Coordination

Strategic architecture for coordinating external AI agents through bounded, auditable, human-supervised workflows.

- **Status**: Proposed
- **Type**: Strategy ADR
- **Date**: 2026-01-14
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, GPT 5.2, Claude Opus 4.5

---

## Context

TNH-Scholar is a long-lived system for AI-assisted study, translation, and analysis of the teachings of Thich Nhat Hanh and the Plum Village tradition. The project explicitly embraces **AI leverage not only for content work, but for building and evolving the system itself**.

This requires a way to coordinate AI coding agents (e.g., Claude Code, Codex) that:

- Enables semi-autonomous progress
- Preserves human authority and review
- Avoids brittle "autonomous agent" designs
- Produces auditable, intelligible work products
- Fits naturally into an engineering workflow (git, branches, reviews)

### The Problem: "Agents are Hard"

Early experimentation — and industry analysis (see Armin Ronacher's "Agents are Hard") — shows that treating LLMs as either:

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

The kernel becomes small (~500 lines) and stable. The prompt library becomes the "standard library" of system behavior — versioned, auditable, and evolvable.

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

---

## Kernel vs Prompt-Program Layer

The system splits cleanly into two layers with distinct responsibilities:

### Kernel Layer (Code — Minimal, Stable)

The kernel handles **hard requirements** that cannot be expressed in prompts:

| Responsibility | Description |
|----------------|-------------|
| **Work-branch management** | Create/switch branches; prevent commits to main |
| **PTY transcript capture** | Record full sub-agent sessions |
| **Workspace diff/status** | Capture git state before/after each step |
| **Policy enforcement** | Post-hoc diff checks against allowed/forbidden paths |
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
┌─────────────────────────────────────────────────────────┐
│  PROMPT-PROGRAM LAYER                                   │
│                                                         │
│  triage.route_task.v1 → selects workflow: implement_adr │
│  planner.evaluate_step.v1 → determines status           │
│  risk.assess_changes.v1 → flags breaking API change     │
│  journal.generate_daily.v1 → produces review summary    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  KERNEL LAYER                                           │
│                                                         │
│  Creates work branch: task/adr-at03-impl                │
│  Executes opcode: RUN_AGENT(claude-code, prompt_id)     │
│  Captures: transcript.md, git diff, test results        │
│  Enforces: diff only touches allowed paths              │
│  Records: all events to provenance ledger               │
└─────────────────────────────────────────────────────────┘
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
│  │     (PTY capture, git diff/status, progress events)       │  │
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

---

## Planner Evaluation Loop

After each sub-agent step, tnh-conductor invokes a **planner evaluation** using a trusted, higher-level model.

### Planner Consumes

- Step intent (what we asked for)
- Transcript channel (what the agent said/did)
- Workspace diff summary (filesystem changes)
- Validation results (tests, lints)

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

### Opcode Set

The kernel executes a small, fixed set of opcodes:

| Opcode | Description |
|--------|-------------|
| `RUN_AGENT` | Invoke sub-agent with prompt; capture transcript + workspace |
| `RUN_VALIDATION` | Execute tests/lint/typecheck; capture results |
| `EVALUATE` | Invoke planner to assess status and determine next step |
| `GATE` | Queue for review or block for approval |
| `STOP` | Halt workflow (success, failure, or needs_human) |

Workflow YAML compiles to this opcode sequence. The kernel executes opcodes; it does not interpret intent.

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

It enables auditability, review generation, and long-term system memory **without agent memory**.

**tnh-gen does not make decisions.** It is the ledger, not the judge.

---

## Protocol Layer Specification

The Protocol Layer is explicitly bounded to:

| Responsibility | Description |
|----------------|-------------|
| **Transcript capture** | PTY/TTY logging of sub-agent sessions |
| **Workspace capture** | `git diff` / `git status` before/after |
| **Progress events** | Heartbeats, completion signals |

The Protocol Layer is **NOT** responsible for:

- Enforcing prompt contracts (post-hoc verification instead)
- Ensuring determinism (we claim "bounded," not "reproducible")
- Parsing structured output from agents (transcripts are semantic, not structured)

**Rationale:** This avoids architectural collapse due to CLI idiosyncrasies across different agent tools.

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

---

## Implementation Roadmap

### Phase 0: Protocol Layer Spike (De-risking)

**Goal:** Prove headless agent invocation + transcript capture works reliably

**Rationale:** The Protocol Layer is the highest-risk component. If we cannot reliably capture PTY transcripts and git diffs from headless agent sessions, the entire architecture is blocked. This spike de-risks before committing to full implementation.

**Spike Scope:**

- Headless invocation of Claude Code CLI (`claude --print` or PTY wrapper)
- Transcript capture to file
- Git diff capture before/after
- Basic provenance record write

**Target Surfaces:**

| Agent | Invocation Method | Capture Method |
|-------|-------------------|----------------|
| Claude Code | `claude --print` mode | stdout capture |
| Claude Code | PTY wrapper | PTY session log |
| Codex | CLI invocation | stdout/PTY |

**Spike Deliverable:**

```bash
# Minimal script that proves the capture chain
./spike-capture.py --agent claude-code --task "List files in src/"
# Outputs:
#   transcript.md (full session)
#   diff.patch (git changes, if any)
#   provenance.json (minimal record)
```

**Success Criteria:**

- [ ] Headless invocation completes without manual interaction
- [ ] Full transcript captured (not truncated)
- [ ] Git diff accurately reflects workspace changes
- [ ] Provenance record written with correct metadata

**Decision Point:** If spike fails, evaluate alternative approaches (SDK, API-only, different agent surface) before proceeding.

---

### Phase 1: Headless Controller (Walking Skeleton)

**Goal:** CLI command that wraps a `claude-code` session with full kernel capabilities

**Deliverables:**

- `tnh-conductor` CLI entry point
- PTY wrapper for transcript capture (proven in Phase 0)
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

---

## Consequences

### Positive

- **Clear separation of concerns** — Conductor coordinates; agents perform; humans decide
- **Robust to agent quirks** — Dual-channel output handles diverse agent behaviors
- **Scales with complexity** — Workflow model supports arbitrarily complex sequences
- **Provider-agnostic** — Same architecture works with Claude Code, Codex, Gemini
- **Auditable by design** — Full provenance trail for every action
- **Aligns with engineering practice** — Git branches, async review, standard tooling

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

**Options:** PTY wrapper, `--print` mode, SDK approach

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
| **Opcode** | Primitive workflow step: RUN_AGENT, VALIDATE, EVALUATE, GATE, STOP |
| **Transcript Channel** | Conversational output from sub-agent |
| **Workspace Channel** | Filesystem effects (diffs, new files) |
| **Daily Review** | Periodic human gating and approval |
| **Provenance Ledger** | tnh-gen's record of all actions and decisions |
| **Policy Prompt** | English definition of allowed/forbidden behaviors |
| **Evaluation Prompt** | English criteria for planner status classification |

---

## Related ADRs

### Proposed Follow-On ADRs

| ADR | Title | Phase |
|-----|-------|-------|
| ADR-OA02 | Headless Agent Integration | 1 |
| ADR-OA03 | Workflow Definition Language | 3 |
| ADR-OA04 | Prompt Library Architecture | 4 |

### Related Existing ADRs

- `adr-pv01-provenance-tracing-strat.md` — Foundation provenance infrastructure
- `adr-tg01-cli-architecture.md` — CLI patterns for tnh-gen
- `adr-at04-ai-text-processing-platform-strat.md` — Related orchestration patterns

---

## References

- Armin Ronacher, "Agents are Hard" — https://lucumr.pocoo.org/2025/11/21/agents-are-hard/
- Claude Code CLI documentation
- OpenAI Codex CLI documentation

---

## Summary

tnh-conductor is a **prompt-program runtime**: a minimal enforcement kernel that executes workflows defined in English.

The system is written in English. Code exists for capture, enforcement, and execution — not for encoding behavior.

Key principles:

- **Kernel is minimal** (~500 lines): branch management, PTY capture, diff capture, policy enforcement, opcode execution
- **Behavior lives in prompts**: task instructions, policies, evaluation criteria, triage rules, journal formats
- **Workflows are bytecode**: YAML compiles to opcodes; intelligence lives in the prompts they reference
- **Enforcement is post-hoc**: verify diffs against policies after execution, not during
- **Humans remain authors**: daily review, blocking gates for high-risk changes, full provenance trail

tnh-conductor enables semi-autonomous progress without surrendering control. It coordinates, listens, evaluates, and records — while humans remain responsible authors of the system.

---

*This ADR establishes the strategic foundation for TNH-Scholar's agent coordination system: a prompt-program runtime enabling bounded, auditable, provenance-driven development workflows.*
