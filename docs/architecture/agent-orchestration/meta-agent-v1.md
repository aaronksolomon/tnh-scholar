---
title: "TNH Orchestrator Meta-Agent v1"
description: "Initial strategic overview exploring provenance-aware agent supervision for TNH-Scholar"
owner: "aaronksolomon"
author: "Gemini AI, Aaron Solomon"
status: draft
created: "2026-01-13"
---

# Strategic Overview: The TNH Orchestrator (Meta-Agent)

*Gemini AI commentary:*

>This is an ambitious and timely evolution for `tnh-scholar`. By moving from "AI-assisted UI" to "Agentic Orchestration," you are essentially building a **Compiler for Agent Workflows**.

>Leveraging your existing `tnh-gen` (provenance-heavy) and the insights from Armin Ronacher’s "Agents are Hard," (https://lucumr.pocoo.org/2025/11/21/agents-are-hard/) the following document outlines the feasibility, strategic direction, and a roadmap for building this Meta-Agent.


---


## 1. Executive Summary & Feasibility

The goal is to transition `tnh-scholar` from a toolset for manual AI interaction into an autonomous orchestrator that manages external agents (Claude Code, Cursor/Codex) as **deterministic tools**.

**Feasibility:** **High.** The existing `tnh-gen` module provides the most difficult prerequisite: **Provenance**. In agentic workflows, the "state" is often lost in long context windows. By having a provenance-first generative layer, `tnh-scholar` is uniquely positioned to act as a "Supervisor" that logs not just what happened, but *why* it happened across different agent sessions.

**The "Lucumr" Constraint:** We will avoid the "God-Model" trap. We will not ask an LLM to "do the work." We will ask an LLM to **emit a plan**, execute that plan via CLI tools (Claude/Codex), and validate the diffs.

---

## 2. Research & Strategic Directions

### A. Treating Agents as Tool-Calls

Per "Agents are Hard," agents fail when they lose the "vibe" or get stuck in loops. We will treat `claude-code` and `codex` as **Ephemeral Workers**.

* **Meta-Agent (TNH-Scholar):** Holds the long-term memory, the project roadmap, and the provenance graph.
* **Sub-Agents:** Spawned for specific PRs or refactor tasks. They are killed after the task, preventing context-drift.

### B. Provenance-Driven State Management

Traditional agents store state in a chat history. `tnh-scholar` will store state in a **Session Ledger**. If Claude Code makes a change that breaks a test, the Meta-Agent uses `tnh-gen` data to identify exactly which prompt caused the regression and rolls back the file system.

### C. The "Daily Review" Loop (Human-in-the-loop)

Instead of the agent committing to `main`, it generates a **TNH-Journal** (a structured summary of the day's work).

* **Morning:** You review the Journal in the VS Code Extension.
* **Action:** You "Approve," "Adjust," or "Re-roll" specific nodes in the provenance graph.

---

## 3. The Walking Skeleton: "Project Ghostwriter"

Before full automation, we must build a prototype that demonstrates the ability to "handoff" a task.

### Phase 1: The Headless Controller (ADR-005)

* **Goal:** A CLI command within `tnh-scholar` that can wrap a `claude-code` session.
* **Mechanism:** Use `stdio` or a terminal wrapper to send a prompt to Claude Code, capture the output, and index the resulting diff into the `tnh-gen` provenance store.

### Phase 2: The Orchestration Schema

* Define a JSON/YAML schema for "Agent Tasks."
* *Example:* `{ "task": "refactor-utils", "agent": "claude-3-7-sonnet", "constraints": ["no-external-deps"], "validation": "npm test" }`

---

## 4. Proposed Architecture (The 10,000ft View)

1. **Orchestrator (The Brain):** High-level reasoning. Breaks `AGENT_WORKFLOW.md` into discrete steps.
2. **Protocol Layer:** Translates Orchestrator intent into CLI commands for Claude Code or Codex.
3. **Validation Layer:** A "Quality Gate" that runs tests/linting. If validation fails, it feeds the error back to the Orchestrator, NOT the sub-agent (to prevent recursive hallucination).
4. **Provenance Sink:** Every interaction is logged via `tnh-gen` for the VS Code UI to visualize.

---

## 5. Implementation Roadmap

### Step 1: Strategic ADR (The "Why")

Draft `ADR-004: Agent Orchestration Strategy`. Focus on the separation of "Planner" and "Executor." Define why we are using a Meta-Agent rather than just a longer prompt.

### Step 2: Component ADR (The "How")

Draft `ADR-005: Headless Agent Integration`. Research how to programmatically interact with `claude-code` and `cursor` (or raw LSP for Codex).

### Step 3: The First Skeleton (The "Hello World")

* **Script:** `tnh-agent --task "Summarize current progress"`
* **Action:** TNH-Scholar reads the last 5 `tnh-gen` logs, sends them to Claude Code via CLI, and saves the summary to a `DAILY_LOG.md`.
* **Success Metric:** The output is recorded in the provenance store without manual copy-pasting.

---

## 6. Addressing "Agents are Hard" Risks

* **Non-Determinism:** We solve this by making the "Meta-Agent" emit a structured plan (DAG) before execution.
* **The "Vibe" Problem:** If a sub-agent starts hallucinating, the `tnh-scholar` monitor detects a lack of progress in the file system and terminates the process.
* **Visibility:** The VS Code extension acts as a "Mission Control," showing the real-time thought process of the Meta-Agent.

---

### Next Action for You:

Does this alignment (Meta-Agent as a **Provenance-Aware Supervisor**) match your vision? If so, I can begin drafting the **Strategic ADR** for the Orchestrator logic.