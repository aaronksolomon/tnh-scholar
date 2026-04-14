---
title: "Current Supervisory Task Brief"
description: "Current task brief for the shell-launched supervisory team experiment."
owner: ""
author: "Codex"
status: current
created: "2026-04-13"
updated: "2026-04-13"
---
# Current Supervisory Task Brief

Current task brief for the first shell-launched supervisory experiment.

## Context

Relevant files and folders are:

- `AGENTS.md`
- `docs/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md`
- `docs/development`
- `docs/development/system-design.md`
- `docs/development/design-principles.md`
- `docs/development/style-guide.md`
- `docs/project`
- `TODO.md`
- `README.md`
- `docs/architecture/agent-orchestration`
- `docs/architecture/agent-orchestration/adr/adr-oa01.2-conceptual-spike-orientation-based-supervisory-orchestration.md`
- `docs/architecture/agent-orchestration/adr/adr-oa01.3-conceptual-spike-practical-approach.md`
- `docs/architecture/agent-orchestration/adr/adr-oa01.4-headless-agent-communication-functional-spike.md`
- `docs/architecture/agent-orchestration/notes/experiments/codex-headless-communication-report.md`
- `docs/architecture/agent-orchestration/supervisory-shell-trial/supervisory-team-workflow-contract.md`

Recent updates are:

- `OA01.2` through `OA01.4` were drafted to reset the orchestration direction toward orientation-based supervisory collaboration
- Codex headless communication experiments confirmed native subagent behavior in headless mode
- the communication surface is viable but still only partially understood
- the project is trying to learn quickly without letting architecture or design work bloat

## Task

Evaluate and explore the design space and implications of the new `OA01.2` to `OA01.4` direction as a supervisor coordinating a small team of native subagents.

The goal is not to write new ADRs or code. The goal is to see whether supervisory delegation produces a stronger result than one straight-line direct-agent critique pass.

Concretely:

- break the work into meaningful exploratory subagent workstreams,
- use subagents to review the relevant files for issues, consistency, implications, opportunities, and possible improvements,
- develop useful improvements in clarity, consistency, and direction where warranted,
- surface extensions, new directions, or novel ideas if they appear genuinely valuable,
- prune weak or bloating directions rather than expanding them,
- and produce one concise supervisory synthesis of the most important findings, improvements, and recommended next experiment.

## Key Constraint

Do not do the substantive evaluation work yourself.

Use subagents for the actual critique and analysis. Your job is supervision, synthesis, and stopping at the right point.

Use no more than 5 subagent calls total.

## Suggested Workstreams

If useful, split work along lines such as:

- strategic coherence of the `OA01.2` to `OA01.4` sequence
- practical feasibility of the proposed experimentation path
- risks of overbuilding versus under-structuring
- candidate improvements or pruning opportunities across the ADR set
- file or file-set review for consistency and clarity

These are suggestions, not mandatory partitions.

## Time and Effort Budget

Keep the experiment small.

Prefer a short supervisory run with a few targeted subagent calls over a long sprawling session.

## Expected Output

Return:

- a concise summary judgment,
- the subagent workstreams used,
- the strongest findings,
- the most valuable improvements or pruning moves identified,
- and the single most sensible next experiment.
