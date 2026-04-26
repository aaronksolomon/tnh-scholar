---
title: "Example Agent Workflow"
description: "Example multi-agent workflow preserved as a reference for agent-orchestration design and future automation."
owner: ""
author: "aaronksolomon, Claude Sonnet 4.5"
status: current
created: "2025-12-28"
updated: "2026-04-26"
---
# Example Agent Workflow

Example dual-agent workflow preserved as a reference artifact for TNH Scholar agent-orchestration design.

This document is no longer the repo-wide required operating workflow. It remains useful as:

- an example collaboration pattern for larger or higher-risk tasks
- a reference for future automated coordination experiments
- a blueprint for orchestration contracts in the agent-orchestration architecture

For the current broad repo-wide workflow, see the repo-root `AGENT_WORKFLOW.md`.

## Context

This workflow came from a period when agent roles were more fixed:

- CC = design-focused reviewer
- CO = implementation-focused executor

That fixed-role model is no longer the general repo policy. Current practice is more flexible:

- either Claude Code or Codex may design, implement, or review
- the user decides when one agent is enough
- the user decides when multiple agents are warranted
- larger, more complex, or mission-critical work often benefits from multiple independent reviews

Even so, the structured loop below remains a useful example for orchestration work.

## Example Loop

**Agent Abbreviations:** CC = Claude Code, CO = Codex

**Workflow Type:** Iterative loop. **Exit conditions**: All CI green, docs updated, merged -> next task. **Continue**: Issues discovered -> restart from Step 1. **Blocked**: External dependency -> document in `TODO.md`.

**Single-agent mode:** If only one agent is available, that agent performs both roles. Human review becomes more important because independent cross-checking is reduced.

## 1. Task Discovery

**Who:** CO

**Action:** If the user request is explicit, treat it as the task. Otherwise review `TODO.md` to identify the next task.

**Output:** Task description and scope identified.

## 2. Initial Design

**Who:** CC

**Prerequisites:** Task scope is clear.

Decision tree:

- Simple design: draft one ADR using `/docs/docs-ops/adr-template.md`
- Complex design: draft a strategy ADR with a sub-ADR roadmap
- Bug fix or patch: decide whether architectural re-evaluation is needed; if yes, draft an ADR addendum or decimal sub-ADR; if no, skip to implementation

Requirements:

- follow `/docs/docs-ops/adr-template.md`
- follow object-service constraints when GenAI scope is involved
- observe `AGENTS.md`
- review related ADRs and project docs before design decisions

**Output:** ADR in `proposed` status, or task ready for implementation.

## 3. Design Review

**Who:** CC + CO independently, then user approval

Review lenses:

- design principles
- style guide
- relevant ADRs
- implementation feasibility
- codebase fit
- testing strategy

If blocking issues are found:

- document them in `TODO.md`
- restart from task discovery if necessary

If the user approves:

- update ADR status from `proposed` to `accepted`

**Output:** Accepted ADR or rejected/superseded design.

## 4. Implementation

**Who:** CO primary, CC oversight

Typical behavior:

- if ADR exists, mark it `wip` at implementation start
- implement in focused iterations
- add tests alongside the work
- run tests during implementation
- document out-of-scope or blocking findings in `TODO.md`
- log change rounds in `AGENTLOG.md`

**Output:** Feature or fix implemented with passing tests.

## 5. Review, Correct, Finalize

**Who:** CC reviews, CO corrects

Review bundle:

- review changes against ADR scope
- run Sourcery on modified Python files
- run `make ci-check`
- repair all issues until checks pass
- update docs as needed

**Output:** All CI checks green, documentation complete.

## 6. Commit and PR

**Who:** CC

Prerequisites:

- CI green
- docs complete
- user approves commit/PR preparation

Typical steps:

- create or use focused feature branch
- organize commits logically
- update `CHANGELOG.md` and `TODO.md`
- open PR for features and larger changes

**Output:** Changes merged to `main` or committed directly for small cases.

## 7. Post-Merge Cleanup

**Who:** CC

Typical cleanup:

- delete working branch when appropriate
- update ADR status to `implemented` when relevant
- archive `AGENTLOG.md` for substantive merged feature work
- sync `CHANGELOG.md` and `TODO.md`

**Output:** Documentation and tracking files aligned with merged code.

## Why Keep This Example

This example remains relevant to agent-orchestration architecture because it demonstrates:

- explicit role separation
- independent review passes
- user-owned approval points
- restart conditions on blocking issues
- a clean handoff from planning to implementation to validation

Those properties are still useful when designing future orchestration contracts, even though the repo-wide human/agent workflow is now broader and more flexible.
