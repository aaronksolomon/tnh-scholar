---
title: "Adr"
description: "Table of contents for architecture/agent-orchestration/adr"
owner: ""
author: ""
status: processing
created: "2026-04-10"
auto_generated: true
---

# Adr

**Table of Contents**:

<!-- To manually edit this file, update the front matter and keep `auto_generated: true` to allow regeneration. -->

**[ADR-OA01: TNH-Conductor — Provenance-Driven AI Workflow Coordination](adr-oa01-agent-orchestration-strategy.md)** - Strategic architecture for coordinating external AI agents (Claude Code, Codex) through bounded, auditable, human-supervised workflows

**[ADR-OA01.1: TNH-Conductor — Provenance-Driven AI Workflow Coordination (v2)](adr-oa01.1-conductor-strategy-v2.md)** - Strategic architecture for coordinating external AI agents through bounded, auditable, human-supervised workflows with CLI opcode tooling

**[ADR-OA02: Phase 0 Protocol Layer Spike](adr-oa02-phase-0-protocol-spike.md)** - De-risking spike to prove headless agent capture and safety controls for tnh-conductor

**[ADR-OA03: Agent Runner Architecture](adr-oa03-agent-runner-architecture.md)** - Phase 1 architecture for agent execution — kernel + adapter pattern based on OA02 spike learnings

**[ADR-OA03.1: Claude Code Runner](adr-oa03.1-claude-code-runner.md)** - Claude Code execution path — headless print mode only, no interactive/PTY automation

**[ADR-OA03.2: Codex Runner](adr-oa03.2-codex-runner.md)** - Codex execution path — API-first, tool-driven runner for implementation tasks

**[ADR-OA03.3: Codex CLI Runner](adr-oa03.3-codex-cli-runner.md)** - Codex execution path via CLI — headless exec mode, superseding API-based approach

**[ADR-OA04: Workflow Execution Contracts](adr-oa04-workflow-schema-opcode-semantics.md)** - Defines the canonical workflow document format, opcode semantics, and execution-contract foundation for tnh-conductor runtime implementation.

**[ADR-OA04.1: MVP Runtime Build-Out Sequence](adr-oa04.1-implementation-notes-mvp-buildout.md)** - Implementation-guide addendum for OA04 defining the MVP runtime build order, role split, and handoff to OA07 bootstrap workspace work.

**[ADR-OA04.2: Runner Contract](adr-oa04.2-runner-contract.md)** - Defines the maintained RUN_AGENT request/result, artifact, and normalization contract for Claude CLI and Codex CLI adapters.

**[ADR-OA04.3: Provenance and Run-Artifact Contract](adr-oa04.3-provenance-run-artifact-contract.md)** - Defines the maintained run directory, artifact manifest, and event/provenance handoff contract for workflow execution.

**[ADR-OA04.4: Policy Enforcement Contract](adr-oa04.4-policy-enforcement-contract.md)** - Defines the shared permissibility model, native-control mapping boundary, and violation handling contract for workflow execution.

**[ADR-OA04.5: Harness Backend Contract](adr-oa04.5-harness-backend-contract.md)** - Defines the maintained backend contract for executing generated and predefined validation harnesses under RUN_VALIDATION.

**[ADR-OA05: Prompt Library Specification](adr-oa05-prompt-library-specification.md)** - Defines prompt artifact schema, versioning, rendering, and catalog validation contracts for tnh-conductor prompt-program behavior.

**[ADR-OA06: Planner Evaluator Contract](adr-oa06-planner-evaluator-contract.md)** - Defines planner evaluator I/O schemas, status derivation, contradiction rules, and deterministic decision vectors for EVALUATE steps.

**[ADR-OA07: Diff-Policy + Safety Rails](adr-oa07-diff-policy-safety-rails.md)** - Defines the bootstrap safety model for worktree isolation, branch-scoped rollback, and agent authority boundaries in maintained agent orchestration.

**[ADR-OA07.1: Worktree Lifecycle and Rollback](adr-oa07.1-worktree-lifecycle-and-rollback.md)** - Bootstrap implementation guide for managed worktree creation, run-directory separation, and branch-scoped rollback in maintained agent orchestration.

---

*This file auto-generated.*
