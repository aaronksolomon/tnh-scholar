---
title: "Claude TODO Refresh"
description: "Focused TODO cleanup prompt for release-prep status and priority updates."
owner: ""
author: "OpenAI GPT-5 Codex"
status: current
created: "2026-04-24"
updated: "2026-04-25"
model_family: "claude"
---
# TODO refresh

Objective: tighten `TODO.md` so it reflects current release-prep reality without redesigning the document.

Context:
- the top of `TODO.md` has stale status and priority language
- `tnh-conductor status --watch` and `tnh-gen --prompt-dir` are already landed
- some sections still carry outdated registry, coverage, or prompt-migration wording

Requirements:
- refresh status summary and immediate next steps
- remove or rewrite clearly stale bullets
- keep active work visible
- add the near-term `tnh-conductor` docs / release-prep need if it is missing

Scope:
- in: `TODO.md`
- out: `CHANGELOG.md`, speculative roadmap additions, broad structural rewrite

Deliverable:
- short summary of the most important cleanups
- sections that still need human strategic review
