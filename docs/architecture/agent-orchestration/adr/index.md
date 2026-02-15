---
title: "Adr"
description: "Table of contents for architecture/agent-orchestration/adr"
owner: ""
author: ""
status: processing
created: "2026-02-15"
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

**[ADR-OA04: Workflow Schema + Opcode Semantics](adr-oa04-workflow-schema-opcode-semantics.md)** - Defines the canonical workflow document format and execution semantics for tnh-conductor kernel opcodes.

**[ADR-OA04.1: Implementation Notes - MVP Build-Out Sequence](adr-oa04.1-implementation-notes-mvp-buildout.md)** - Implementation-guide addendum for OA04 defining MVP execution flow, role split, and incremental build sequence.

**[ADR-OA05: Prompt Library Specification](adr-oa05-prompt-library-specification.md)** - Defines prompt artifact schema, versioning, rendering, and catalog validation contracts for tnh-conductor prompt-program behavior.

**[ADR-OA06: Planner Evaluator Contract](adr-oa06-planner-evaluator-contract.md)** - Defines planner evaluator I/O schemas, status derivation, contradiction rules, and deterministic decision vectors for EVALUATE steps.

---

*This file auto-generated.*
