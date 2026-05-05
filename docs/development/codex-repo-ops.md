---
title: "Codex Repo Ops"
description: "Repo-local Codex configuration policy for TNH Scholar prototype operator workflows."
owner: ""
author: ""
status: current
created: "2026-05-02"
updated: "2026-05-02"
---
# Codex Repo Ops

This note documents the repo-local `.codex/config.toml` file as a repository
operations surface, not an application runtime surface.

## Purpose

The tracked `.codex/config.toml` exists to make repo-local Codex behavior more
predictable for TNH Scholar operator workflows during the current prototype
phase. In particular, it supports:

- lower-friction repo operations in the checked-out project
- streamlined test-environment runs for prompt and golden-workflow work
- the current VICOA-related operator path discussed in active prototype work

These settings do not affect `tnh-scholar` package behavior, `tnh-gen`
application semantics, or shipped runtime assets.

## Current Profiles

- `collab`
  Uses workspace-write sandboxing and `approval_policy = "never"` for
  repo-scoped collaborative work inside the checked-out repository.
- `collab_exec`
  Keeps the same sandbox/approval posture while inheriting the full shell
  environment for operator-driven execution paths that need the real repo-local
  environment.
- `repo`
  Mirrors the repo-operations posture explicitly so repo-level workflows have a
  named stable profile rather than depending on ad hoc local defaults.

## Environment Inheritance

`shell_environment_policy.inherit = "all"` is intentional in this repo-local
configuration.

The goal is not to change code execution semantics inside `tnh-scholar`. The
goal is to reduce operator friction for prototype repo workflows that depend on
the real checked-out environment, shell configuration, and repo-local tooling
surface.

This is especially relevant when the active workflow is about repository
operations, test-environment setup, or the current VICOA-related path rather
than product code changes.

## Scope Boundary

Keep this file focused on repo operations:

- acceptable: sandbox posture, approval posture, repo-local execution defaults
- acceptable: operator-quality-of-life settings for prototype workflows
- not acceptable: using `.codex/config.toml` to document or control
  `tnh-scholar` application behavior

If a change affects product/runtime behavior, document it in the maintained
architecture or CLI docs instead.

## Related Context

- Prior experiment note: [/docs/architecture/agent-orchestration/notes/experiments/codex-headless-communication-report.md](/architecture/agent-orchestration/notes/experiments/codex-headless-communication-report.md)
- Prompt mirror workspace: `tnh-prompts/README.md`
- Repo policy baseline: `AGENTS.md`
