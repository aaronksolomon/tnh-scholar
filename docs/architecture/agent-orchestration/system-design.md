---
title: "TNH-Scholar Agent Orchestration System"
description: "Comprehensive design document synthesizing v1 and v2 meta-agent concepts with Claude Code review"
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Opus 4.5"
status: draft
created: "2026-01-13"
---

# TNH-Scholar Agent Orchestration System
## Comprehensive Design Document — v1.0

**Status:** Draft
**Sources:** `tnh-orchestrator-meta-agent.md` (v1), `tnh-orchestrator-meta-agent v2.md`
**Date:** 2026-01-13

---

## Executive Summary

TNH-Scholar is evolving from an AI-assisted translation/processing toolkit into a **provenance-driven workflow orchestration engine**. The system treats external AI agents (Claude Code, Codex, potentially Gemini) as **deterministic, ephemeral tool executors** rather than autonomous decision-makers.

### Core Innovation

The key insight is using `tnh-gen`'s provenance infrastructure as the **single source of truth** for agentic workflows. This solves the fundamental problems identified in Armin Ronacher's "Agents are Hard" analysis:

1. **Context drift** → Externalized state in provenance ledger
2. **Non-determinism** → Structured plans (DAGs) before execution
3. **The "vibe" problem** → Filesystem-based progress detection
4. **Visibility** → Full audit trail for human review

### Feasibility Assessment

**High feasibility.** The existing `tnh-gen` module provides the hardest prerequisite: provenance tracking. Most agent frameworks struggle to answer "why did the agent do X?" — TNH-Scholar already has this infrastructure.

---

## 1. Design Principles

### 1.1 Agents Are Tools, Not Thinkers

Codex and Claude Code are treated as **artifact emitters**:

| Agents DO | Agents DO NOT |
|-----------|---------------|
| Receive constrained prompts | Decide what to do next |
| Emit bounded outputs (diffs, reviews) | Maintain long-term context |
| Execute in ephemeral sessions | Own project state |
| Follow typed contracts | Expand scope beyond prompt |

**Rationale:** Per "Agents are Hard," agents fail when they lose the "vibe" or get stuck in loops. By treating them as ephemeral workers spawned for specific tasks and killed after completion, we prevent context-drift.

### 1.2 All State Is Externalized

There is no "agent memory." All durable state lives in:

- **Filesystem** — Code, configs, artifacts
- **`tnh-gen` provenance records** — The "why" behind every change
- **Workflow state documents** — Explicit progress markers

This ensures:
- **Replayability** — Any workflow step can be re-executed
- **Debuggability** — Full trace of what happened and why
- **Deterministic recovery** — Failed runs can resume from last checkpoint

### 1.3 CLI Is the Source of Truth

All workflows must be runnable headlessly via CLI.

**VS Code's role:**
- Observes workflow execution
- Visualizes provenance graphs
- Gates human approvals
- Provides "Mission Control" view

**VS Code is not required for correctness.** A workflow that only works in the IDE is a failed design.

### 1.4 The "Lucumr" Constraint

> We will not ask an LLM to "do the work." We will ask an LLM to **emit a plan**, execute that plan via CLI tools, and validate the outputs.

This separation of "Planner" and "Executor" is critical. The Meta-Agent:
1. Reasons about what needs to happen (high-level)
2. Emits a structured plan (DAG)
3. Delegates execution to bounded sub-agents
4. Validates results against expectations
5. Records everything in the provenance ledger

---

## 2. System Architecture

### 2.1 High-Level Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    TNH Orchestrator (Meta-Agent)                │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐   │
│  │   Workflow    │  │    Prompt     │  │    Sequencing     │   │
│  │  Definitions  │  │    Library    │  │      Engine       │   │
│  └───────────────┘  └───────────────┘  └───────────────────┘   │
│                              │                                  │
│  ┌───────────────────────────┴───────────────────────────────┐ │
│  │                    Protocol Layer                          │ │
│  │         (Translates intent → CLI commands)                 │ │
│  └───────────────────────────────────────────────────────────┘ │
└────────────────────────────────┬────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   Claude Code   │   │     Codex       │   │    Gemini (?)   │
│   (Sub-Agent)   │   │   (Sub-Agent)   │   │   (Sub-Agent)   │
└────────┬────────┘   └────────┬────────┘   └────────┬────────┘
         │                     │                     │
         └───────────────────────────────────────────┘
                               │
         ┌─────────────────────┴─────────────────────┐
         │                                           │
         ▼                                           ▼
┌─────────────────────────┐           ┌─────────────────────────┐
│    Validation Layer     │           │   Provenance Ledger     │
│  (tests, lints, checks) │           │      (tnh-gen)          │
└─────────────────────────┘           └─────────────────────────┘
```

### 2.2 Component Responsibilities

#### Orchestrator (The Brain)
- Holds long-term memory and project roadmap
- Breaks workflows into discrete steps
- Makes high-level decisions about approach
- Owns the provenance graph

#### Protocol Layer
- Translates orchestrator intent into CLI commands
- Handles agent-specific invocation patterns
- Manages stdio/terminal wrapping for agent sessions

#### Execution Layer (Sub-Agents)
- Claude Code, Codex, Gemini — ephemeral workers
- Receive constrained, single-purpose prompts
- Emit artifacts (diffs, reviews, summaries)
- Killed after task completion

#### Validation Layer (Quality Gate)
- Runs tests, linters, invariant checks
- If validation fails, feeds error back to **Orchestrator** (not sub-agent)
- Prevents recursive hallucination loops

#### Provenance Sink (tnh-gen)
- Records every interaction
- Tracks: *why*, *what*, *who*, *what changed*
- Enables rollback to any previous state
- Powers VS Code visualization

---

## 3. Prompt Library System

### 3.1 Prompts as Named Artifacts

Each prompt is a first-class, versioned artifact:

```
codex.implement_adr.v2
claude.review_diff.v1
claude.summarize_provenance.v1
```

**Properties:**
- Named with clear semantics
- Versioned for evolution tracking
- Tool-specific (Codex vs Claude vs Gemini)
- Stored as structured templates, not free text

### 3.2 Prompt Contracts

Each prompt defines a typed interface:

```yaml
prompt: codex.implement_adr
version: 2

inputs:
  - name: adr_id
    type: string
    description: "ADR identifier (e.g., ADR-AT03)"
  - name: target_paths
    type: list[path]
    description: "Files to modify"
  - name: constraints
    type: list[string]
    description: "Implementation constraints"

outputs:
  - name: diff
    type: unified_diff
    description: "Proposed code changes"

forbidden_behaviors:
  - "No task planning beyond the specified ADR"
  - "No scope expansion"
  - "No file creation outside target_paths"
  - "No external dependency additions without constraint"
```

**This turns LLM calls into typed operations.**

---

## 4. Workflow Sequencing Model

### 4.1 Workflow Definition Schema

Workflows are declarative (YAML/JSON):

```yaml
workflow: implement_adr
version: 2
description: "Implement an ADR with review and approval gates"

inputs:
  - adr_id
  - target_paths

steps:
  - id: implement
    prompt: codex.implement_adr.v2
    inputs: [adr_id, target_paths]
    output: diff

  - id: validate
    type: validation
    run: [tests, lint, typecheck]
    on_fail: halt

  - id: review
    prompt: claude.review_diff.v1
    inputs: [diff, adr_id]
    output: review_report

  - id: approval
    type: gate
    gate: human_approval
    present: [diff, review_report]
```

### 4.2 Agent Task Schema

Individual agent invocations follow a structured format:

```json
{
  "task_id": "refactor-utils-001",
  "task": "refactor-utils",
  "agent": "claude-code",
  "model": "claude-3-7-sonnet",
  "constraints": [
    "no-external-deps",
    "preserve-public-api"
  ],
  "inputs": {
    "target_files": ["src/utils/*.py"],
    "context_files": ["docs/adr/ADR-AT03.md"]
  },
  "validation": "pytest tests/unit/",
  "timeout": "10m",
  "provenance": {
    "parent_workflow": "implement_adr.v2",
    "step_id": "implement"
  }
}
```

---

## 5. Human-in-the-Loop: The Daily Review Pattern

### 5.1 The TNH-Journal

Instead of agents committing directly to `main`, the system generates a structured daily summary:

```markdown
# TNH-Journal: 2026-01-13

## Completed Tasks
- [x] Implemented ADR-AT03 refactor (3 files changed)
- [x] Fixed type errors in text_object.py

## Pending Review
- [ ] Diff: src/tnh_scholar/ai_text_processing/ (142 lines)
- [ ] Risk: Breaking change to public API

## Provenance Graph
→ Task: implement_adr.v2
  → Step: codex.implement_adr.v2 [SUCCESS]
  → Step: validate [SUCCESS]
  → Step: claude.review_diff.v1 [SUCCESS]
  → Step: human_approval [PENDING]
```

### 5.2 Review Workflow

**Morning Routine:**
1. Review Journal in VS Code Extension
2. Examine provenance graph for the day's work
3. For each pending item, choose:
   - **Approve** — Accept and proceed
   - **Adjust** — Modify specific nodes in the graph
   - **Re-roll** — Replay step with different parameters

**This ensures human oversight without blocking agent execution.**

---

## 6. Addressing "Agents are Hard" Risks

| Risk | Mitigation |
|------|------------|
| **Non-Determinism** | Meta-Agent emits structured plan (DAG) before execution |
| **Context Drift** | No agent memory; all state externalized to filesystem + provenance |
| **"Vibe" Problem** | Monitor filesystem for progress; terminate stalled agents |
| **Recursive Hallucination** | Validation errors go to Orchestrator, not sub-agent |
| **Visibility** | VS Code extension as "Mission Control" with real-time thought process |
| **State Loss** | Session Ledger in tnh-gen; rollback to any prompt that caused regression |

---

## 7. Implementation Roadmap

### Phase 0: Foundation (Current)
- `tnh-gen` provenance infrastructure exists
- Basic CLI tooling in place

### Phase 1: Headless Controller
**Goal:** CLI command within `tnh-scholar` that wraps a `claude-code` session

**Deliverables:**
- `tnh-agent` CLI entry point
- stdio/terminal wrapper for Claude Code
- Diff capture and indexing into provenance store

**Walking Skeleton:**
```bash
tnh-agent --task "Summarize current progress"
# Reads last 5 tnh-gen logs
# Sends to Claude Code via CLI
# Saves summary to DAILY_LOG.md
# Records in provenance store
```

**Success Metric:** Output recorded in provenance without manual copy-paste

### Phase 2: Orchestration Schema
**Goal:** Formal schema for agent tasks and workflows

**Deliverables:**
- JSON/YAML schema for Agent Tasks
- Workflow definition language
- Prompt contract specifications

### Phase 3: Prompt Library
**Goal:** First-class prompt management

**Deliverables:**
- Prompt storage and versioning
- Template rendering with typed inputs
- Prompt selection based on task type

### Phase 4: Multi-Agent Orchestration
**Goal:** Full DAG-based workflow execution

**Deliverables:**
- Workflow sequencing engine
- Multi-agent coordination
- Validation integration
- Human approval gates

### Phase 5: VS Code Integration
**Goal:** Visual control surface

**Deliverables:**
- Provenance graph visualization
- Real-time workflow monitoring
- Approval UI for gates

---

## 8. ADR Roadmap

### ADR-OA01: Agent Orchestration Strategy (Strategic)
- Why Meta-Agent architecture
- Separation of Planner and Executor
- Provenance-first design rationale

### ADR-OA02: Headless Agent Integration (Component)
- Claude Code CLI integration
- Codex CLI integration
- stdio wrapper design
- Output capture and provenance indexing

### ADR-OA03: Prompt Library Architecture (Component)
- Prompt versioning scheme
- Contract specification format
- Template rendering system

### ADR-OA04: Workflow Definition Language (Component)
- YAML/JSON schema
- Step types and sequencing
- Gate and validation patterns

---

## Appendix A: Reference Links

- Armin Ronacher, "Agents are Hard" — https://lucumr.pocoo.org/2025/11/21/agents-are-hard/
- Claude Code CLI documentation
- OpenAI Codex CLI documentation

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Meta-Agent** | The TNH-Scholar orchestrator that coordinates sub-agents |
| **Sub-Agent** | Claude Code, Codex, or Gemini running bounded tasks |
| **Provenance Ledger** | tnh-gen's record of all changes and their causes |
| **Prompt Contract** | Typed specification of inputs, outputs, and forbidden behaviors |
| **Session Ledger** | Per-workflow provenance tracking |
| **Quality Gate** | Validation checkpoint before proceeding |
| **DAG** | Directed Acyclic Graph representing workflow steps |

---

# Claude Code Review & Commentary

## Overall Assessment

This is an exceptionally well-conceived architecture. The v2 document significantly improves on v1 by:
1. Making the CLI-first principle explicit
2. Formalizing the Prompt Library concept
3. Adding typed contracts for prompts

The core insight — **using tnh-gen's provenance infrastructure as the control plane for agentic workflows** — is genuinely novel. Most agent frameworks treat provenance as an afterthought; this design makes it foundational.

## Strengths

### 1. Provenance-First Design
The existing `tnh-gen` infrastructure gives you something most agent builders lack: a robust answer to "why did the agent do X?" This is your competitive advantage.

### 2. "Lucumr" Constraint
Explicitly adopting the "emit a plan, don't do the work" pattern from "Agents are Hard" shows architectural maturity. Many agent systems fail precisely because they conflate planning and execution.

### 3. Typed Prompt Contracts
Treating prompts as named, versioned artifacts with typed I/O contracts is the right abstraction. This makes LLM calls:
- Testable
- Versionable
- Auditable
- Replaceable (swap Codex for Gemini with the same contract)

### 4. CLI-First Philosophy
Making VS Code "not required for correctness" is the right call. It ensures:
- CI/CD integration is possible
- Headless operation for batch processing
- No IDE lock-in

### 5. Validation Error Routing
Sending validation failures to the Orchestrator (not the sub-agent) is subtle but critical. This prevents the recursive hallucination loops that plague many agent systems.

## Concerns & Open Questions

### 1. Protocol Layer Complexity

**Issue:** The document describes a "Protocol Layer" that translates intent to CLI commands, but the actual mechanics of wrapping `claude-code` and `codex` CLIs are underspecified.

**Questions:**
- How do you capture structured output from Claude Code? (It's designed for interactive use)
- Does Codex CLI support the structured I/O you need, or will you need to parse free-text output?
- How do you handle Claude Code's tool calls (Read, Edit, Bash) in a headless context?

**Recommendation:** This needs detailed research. Consider prototyping the `stdio` wrapper for Claude Code first — it may reveal constraints that affect the overall design.

### 2. Prompt Contract Enforcement

**Issue:** The typed contracts are elegant in theory, but LLMs don't respect contracts. A prompt that says "no file creation outside target set" is a hope, not a guarantee.

**Questions:**
- How do you validate that an agent actually followed its contract?
- What happens when Claude Code creates a file you didn't authorize?
- Can you sandbox the agent's filesystem access?

**Recommendation:** Consider:
- Post-execution validation: diff the filesystem before/after, reject unauthorized changes
- Sandboxing: run agents in isolated environments where unauthorized actions fail
- Contract verification layer: separate step that checks outputs match contract

### 3. Error Recovery Granularity

**Issue:** "Rollback to any previous state" is easy to say but complex to implement for a codebase.

**Questions:**
- Does rollback mean git reset? What about uncommitted changes?
- How do you handle partial rollbacks (undo step 3 but keep steps 1-2)?
- What if the agent created files that shouldn't exist post-rollback?

**Recommendation:** Define the rollback model precisely:
- Are you rolling back the filesystem? Git history? Provenance records?
- Consider using git worktrees for sandboxed agent execution

### 4. Human Approval Latency

**Issue:** The "Daily Review" pattern implies agents work, then humans review next morning. But what if an agent gets stuck early?

**Questions:**
- How long should an agent spin before escalating?
- What's the notification mechanism for urgent issues?
- Can the human interrupt mid-workflow?

**Recommendation:** Add an urgency/escalation model:
- Stall detection: no filesystem progress for N minutes → alert
- Risk thresholds: certain operations require immediate human approval
- Interrupt protocol: human can pause/abort any running workflow

### 5. Multi-Model Coordination

**Issue:** You mention Claude Code, Codex, and "possibly Gemini later." But the document assumes these are interchangeable behind the Prompt Contract abstraction.

**Questions:**
- Are the CLIs actually similar enough for uniform wrapping?
- Do they have different capability profiles that matter for prompt routing?
- How do you decide which model gets which task?

**Recommendation:** Build the abstraction for multiple models from the start, but prototype with just Claude Code. Don't try to normalize Codex/Gemini until you've proven the single-model case works.

### 6. Provenance Storage Scale

**Issue:** Recording "every interaction" creates storage growth.

**Questions:**
- What's the retention policy?
- How do you query historical provenance efficiently?
- Is provenance per-session, per-workflow, or global?

**Recommendation:** Define provenance scopes and TTLs early. Consider:
- Hot tier: recent sessions (full detail)
- Warm tier: completed workflows (summary + key artifacts)
- Cold tier: archived (just enough to reconstruct if needed)

## Suggested Improvements

### 1. Add a "Capability Matrix" for Agents

Document what each agent type can/cannot do:

| Capability | Claude Code | Codex | Gemini |
|------------|-------------|-------|--------|
| File read | Yes | Yes | ? |
| File write | Yes | Yes | ? |
| Bash execution | Yes | ? | ? |
| Structured output | Limited | ? | ? |
| Web search | Yes | No | Yes |

This helps with prompt routing decisions.

### 2. Define "Stall" Precisely

The document says the monitor "detects a lack of progress in the file system." What counts as progress?

Suggestion:
- Filesystem change (file modified/created)
- Provenance record written
- Validation pass/fail emitted
- Explicit "heartbeat" from agent

### 3. Add Workflow Composition

Can workflows call other workflows? The current model seems flat.

Suggestion: Allow `include` or `call` step types:

```yaml
steps:
  - call: validate_and_lint.v1
    inputs: [target_paths]
```

### 4. Consider Abort Semantics

What happens when a workflow is aborted mid-execution?

- Which artifacts are kept?
- Is provenance marked as incomplete?
- Can the workflow be resumed?

### 5. Add Cost/Token Tracking

Agent calls cost money. Consider tracking:
- Tokens used per prompt
- Cost per workflow
- Budget limits per session

---

## Issues List

### Critical (Blocks Phase 1)

1. **P0: Claude Code CLI wrapping is unproven**
   - Need to prototype stdio capture for interactive sessions
   - May require using Claude Code in `--print` mode or SDK approach
   - Blocks: Headless Controller implementation

2. **P0: Filesystem sandbox strategy undefined**
   - How do you prevent unauthorized file operations?
   - Blocks: Prompt contract enforcement

### High (Blocks Phase 2)

3. **P1: Prompt contract validation not specified**
   - Need mechanism to verify agent outputs match contract
   - Could be post-execution diff analysis or structured output parsing

4. **P1: Error recovery/rollback model incomplete**
   - Define precisely what "rollback" means for filesystem + git + provenance

5. **P1: Human interrupt protocol missing**
   - How does a human abort a running workflow?
   - What's the cleanup procedure?

### Medium (Blocks Phase 3+)

6. **P2: Multi-agent capability normalization**
   - Different agents have different capabilities
   - Need abstraction that doesn't hide important differences

7. **P2: Provenance storage scaling**
   - Define retention policies and query patterns

8. **P2: Workflow composition/nesting**
   - Can workflows call other workflows?

### Low (Nice to Have)

9. **P3: Cost/token tracking**
   - Budget awareness for workflows

10. **P3: Notification/alerting system**
    - How are humans notified of stalls or urgent decisions?

---

## Recommended Next Steps

1. **Prototype Claude Code CLI wrapper** — This is the highest-risk unknown. Build a minimal proof-of-concept that:
   - Sends a prompt to Claude Code
   - Captures the resulting filesystem changes
   - Records them in tnh-gen

2. **Draft ADR-OA01 (Strategy)** — Formalize the "why" before the "how"

3. **Define the minimal Prompt Contract schema** — Start with just Codex for implementation tasks and Claude for review tasks

4. **Build the walking skeleton** — The `tnh-agent --task "Summarize current progress"` example is perfect

---

*Document generated by Claude Code (Opus 4.5) as part of TNH-Scholar development planning.*
