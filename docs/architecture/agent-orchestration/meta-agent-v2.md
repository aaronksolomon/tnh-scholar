---
title: "TNH-Scholar Agent System — Draft v2"
description: "Refined design for provenance-driven, CLI-first agentic workflows"
owner: "aaronksolomon"
author: "Aaron Solomon"
status: draft
created: "2026-01-13"
---

# TNH-Scholar Agent System — Draft v2
## Provenance-Driven, CLI-First Agentic Workflows

---

## 1. Purpose and Scope

This document defines **Version 2** of the TNH-Scholar agent system.

The goal is **not** to build a general autonomous agent, but to construct a **deterministic, provenance-driven workflow engine** that can:

- Orchestrate bounded AI tools (Codex, Claude Code)
- Generate and validate concrete artifacts (diffs, reviews, implementations)
- Preserve full provenance for replay, audit, and human review
- Operate CLI-first, with VS Code as an optional observer/control surface

This system explicitly avoids:
- Open-ended agent autonomy
- Conversational state as “memory”
- Agents making project-level decisions

---

## 2. Core Design Principles

### 2.1 Agents Are Tools, Not Thinkers
Codex and Claude Code are treated as **artifact emitters**, not planners.

They:
- Receive constrained prompts
- Emit bounded outputs (diffs, reviews, summaries)
- Are ephemeral by design

They do *not*:
- Decide what to do next
- Maintain long-term context
- Own project state

---

### 2.2 All State Is Externalized
There is no “agent memory.”

All durable state lives in:
- The filesystem
- `tnh-gen` provenance records
- Explicit workflow state documents

This ensures:
- Replayability
- Debuggability
- Deterministic recovery from failure

---

### 2.3 CLI Is the Source of Truth
All workflows must be runnable headlessly via CLI.

VS Code:
- Observes
- Visualizes
- Gates approvals

It is **not required** for correctness.

---

## 3. High-Level System Overview

At a high level, the system consists of:

1. **Workflow Definitions**  
   Declarative descriptions of *what steps exist* and *in what order*

2. **Prompt Library**  
   Named, versioned prompts for Codex and Claude Code

3. **Sequencing Engine**  
   Iterates through prompt calls based on workflow state

4. **Execution Layer**  
   Runs CLI tools (Codex CLI, Claude Code CLI, validators)

5. **Validation Layer**  
   Runs tests, linters, and invariant checks

6. **Provenance Ledger (`tnh-gen`)**  
   Records *why*, *what*, *who*, and *what changed*

---

## 4. Prompt Library (First-Class Concept)

### 4.1 Prompt as a Named Artifact

Each prompt is:
- Named
- Versioned
- Tool-specific (Codex / Claude)
- Strictly bounded in scope

Example prompt identifiers:

- `codex.review_code.v1`
- `codex.implement_adr.v2`
- `claude.review_diff.v1`
- `claude.summarize_provenance.v1`

Prompts are stored as structured templates, not free text blobs.

---

### 4.2 Prompt Contracts

Each prompt defines:

- **Inputs**
  - Files
  - ADR IDs
  - Diff hunks
  - Constraints

- **Expected Outputs**
  - Patch / diff
  - Review report
  - Risk list
  - Summary

- **Forbidden Behaviors**
  - No task planning
  - No scope expansion
  - No file creation outside target set

This turns LLM calls into **typed operations**.

---

## 5. Workflow Sequencing Model

### 5.1 Workflow Definition File

Workflows are defined declaratively (YAML/JSON).

Example (conceptual):

```yaml
workflow: implement_adr
version: 2
steps:
  - prompt: codex.implement_adr.v2
    inputs: [adr_id, target_paths]
    output: diff

  - validate: run_tests
    on_fail: halt

  - prompt: claude.review_diff.v1
    inputs: [diff, adr_id]
    output: review_report

  - gate: human_approval