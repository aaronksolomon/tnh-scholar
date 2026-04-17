---
title: "Agent Orchestration Collaboration Paradigms"
description: "Blue-sky research note framing the orchestration problem space for multi-agent coding and design collaboration across time, scope, and model families."
owner: ""
author: "Codex"
status: current
created: "2026-04-16"
updated: "2026-04-16"
---

# Agent Orchestration Collaboration Paradigms

## Purpose

Start a blue-sky research framing for the agent-orchestration problem space now emerging in TNH Scholar.

The core question is not just how to run one more agent, or how to harden one specific orchestration engine. The broader question is:

How should a collaborating team of agents be coordinated on significant coding and design work that stretches over time, requires iteration and supervision, and may benefit from multiple distinct model families?

This note is intended as a research starter rather than a decision document.

## Working Question

What are the main paradigms, coordination variables, and operating modes available for long-running multi-agent software work, and which combinations look most promising for TNH Scholar?

## Problem Framing

The space being explored here is broader than any one metaphor.

It may resemble:

- an orchestra with a conductor and bounded performers,
- a supervisory engineering team with delegated specialists,
- a distributed colony with local initiative and simple rules,
- or hybrid systems that mix deterministic control with model-driven judgment.

The research problem is therefore to map the space rather than collapse too early into one control metaphor.

## Candidate Coordination Variables

Variables that appear to matter:

- where planning authority lives,
- where semantic judgment lives,
- how delegation is invoked,
- whether delegation is native to the supervising model or mediated through explicit tools,
- how worker outputs are normalized,
- how long-running state is monitored,
- how retries or refinement loops are bounded,
- how different model families are selected for different roles,
- how artifacts and run state are exposed for supervision,
- how failure, interruption, and retry are handled,
- and how much of the system is deterministic program flow versus model-mediated coordination.

## Candidate Paradigm Families

### 1. Deterministic Kernel Orchestration

Workflow documents and kernel logic determine execution, routing, and artifact handling.

### 2. Native Supervisory Delegation

A strong supervisor agent delegates to native subagents and synthesizes results.

### 3. Tool-Mediated Supervisory Delegation

A supervisor delegates through explicit worker tools or runner adapters rather than native subagent magic.

### 4. Hybrid Supervision With Deterministic Execution Rails

A supervisor owns decomposition and judgment while a deterministic runtime owns execution boundaries, artifacts, and routing constraints.

### 5. Emerging or Mixed Forms

The space likely includes additional hybrids and layered combinations not yet named cleanly.

Examples may include:

- a model supervisor that delegates through explicit worker-runner tools,
- a deterministic kernel that executes only bounded steps while an external evaluator or planner decides routing,
- a mixed engineering team pattern where coding, testing, review, and design critique are treated as distinct worker roles,
- and longer-running systems that move between tightly controlled and loosely supervisory phases over the life of a task.

## Layer-Mixing Possibilities

One useful way to frame the space is by separating layers that are often bundled together:

- planning and decomposition,
- worker invocation,
- execution control,
- evaluation and routing,
- state reporting and operator visibility,
- and artifact normalization.

Different systems can then mix these layers in different ways.

For example:

- `tnh-conductor` currently puts most execution control in the kernel,
- shell-supervisory Codex puts planning and delegation judgment inside the model,
- a tool-mediated supervisory system would keep planning in the model but move worker invocation into explicit runner tools,
- and future hybrids may place evaluation in one model family, implementation in another, and deterministic guardrails around both.

This suggests the real design space is not a single orchestration architecture but a matrix of interchangeable coordination parts.

## Working Hypothesis

The most promising near-term direction may not be either extreme.

It may be a hybrid pattern in which:

- a strong supervisor model owns task decomposition, prioritization, and synthesis,
- explicit tool calls own worker invocation and result capture,
- deterministic runtime surfaces own state reporting, artifacting, and bounded execution constraints,
- and specialized models are selected for roles such as implementation, testing, code review, design critique, or exploratory analysis.

This is attractive because it may retain semantic flexibility without depending entirely on fragile native subagent behavior.

## Research Questions

Open questions to develop:

- Which paradigms scale best in elapsed runtime?
- Which paradigms scale best in conceptual scope?
- Which paradigms best support cross-model collaboration?
- Which paradigms are most observable and debuggable?
- Which paradigms fail gracefully?
- Which paradigms produce the best balance of flexibility and reproducibility?

More specific questions now emerging:

- What are the cleanest boundaries between supervisor intelligence and worker execution infrastructure?
- When should subagents be invoked natively by a model, and when should they be invoked through explicit tools?
- What kinds of task decomposition actually benefit from team coordination rather than adding overhead?
- Which roles are best handled by the same model family, and which benefit from deliberate model diversity?
- How much deterministic structure is required before a long-running collaborative system becomes inspectable and trustworthy?

## Comparative Experiment Categories

Useful experiment categories include:

- direct single-agent baseline versus coordinated multi-agent runs on the same task,
- native subagent supervision versus tool-mediated delegation,
- deterministic kernel execution versus model-driven supervisory routing,
- same-model team runs versus cross-model team runs,
- short bounded tasks versus longer iterative tasks,
- and one-shot review versus review-plus-refinement loops.

For each experiment, the important outputs are not just task completion but also:

- runtime overhead,
- delegation success rate,
- quality of synthesis,
- observability during execution,
- stopping behavior,
- and how easily a human can understand and trust what happened.

## Suggested Next Research Work

This document is intentionally incomplete. A stronger blue-sky pass should likely:

- name additional paradigm families and edge cases,
- sharpen the variable taxonomy,
- propose a clearer comparison matrix,
- separate conceptual scaling from runtime scaling,
- and identify which modes appear promising specifically for TNH Scholar rather than in the abstract.

It may also be useful to distinguish between:

- paradigms for implementation work,
- paradigms for review and critique,
- paradigms for long-running iterative programs of work,
- and paradigms for exploratory research or architectural investigation.

## Immediate Use

This note should help:

- frame follow-on research,
- guide comparative experiments,
- and give a future blue-sky researcher a structured starting point rather than a blank page.

## Notes

An initial attempt was made to use `tnh-gen` itself as a delegated research-expansion pass for this note. The current `tnh-gen` surface in this branch does not yet expose a clean custom prompt-directory path, and a temporary repo-local prompt experiment ultimately returned an empty result after working around registry and budget constraints.

That is not a blocker for this research note, but it is a useful reminder that orchestration and delegation surfaces are still uneven across the current tool stack.
