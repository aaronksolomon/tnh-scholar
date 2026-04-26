---
title: "Agent Workflow"
description: "General human-and-agent workflow for TNH Scholar development."
owner: ""
author: "aaronksolomon, Claude Sonnet 4.5, Codex"
status: current
created: "2025-12-28"
updated: "2026-04-26"
---
# Agent Workflow

Repo-wide agent workflow is intentionally lightweight and judgment-driven.

## 1. Operating Model

- Agent roles are not fixed. Claude Code and Codex may each design, implement, review, or critique.
- The user decides when one agent is enough and when multiple independent reviews are warranted.
- Default to the lightest workflow that is honest about risk.
- Use broader review for architectural, release-adjacent, workflow, CI, orchestration, or otherwise high-consequence changes.

## 2. Validation Model

- Validation is local-first.
- Use focused checks for focused changes.
- Use broader local validation when the risk justifies it, typically `make ci-check`.
- Treat PR CI as advisory fast signal, not final authority.
- Use `full-ci` when extra GitHub-side confidence is warranted.
- Release validation is stricter than PR validation: run `make release-check` on the actual release candidate state.

## 3. Documentation and Judgment

- Keep workflow docs aligned with actual practice.
- Keep repo-root workflow docs broad and stable.
- Move more specific coordination patterns and experimental flows under agent-orchestration docs.
- Merge and release judgment remain human-owned.
- Agents inform engineering judgment; they do not replace it.
