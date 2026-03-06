---
title: "ADR-OA03.3: Codex CLI Phase-0 Protocol Spike"
description: "Spike to evaluate Codex CLI as the primary Codex execution surface, superseding the API-based Codex runner approach"
status: "proposed"
supersedes:
  - ADR-OA03.2
date: "2026-01-29"
---

# ADR-OA03.3 — Codex CLI Phase-0 Protocol Spike

## Context

Prior exploration of a Codex runner (ADR-OA03.2) attempted to invoke GPT-Codex models directly via the OpenAI Responses API with a custom orchestration harness. The spike demonstrated that:

- Codex models treat tool calls as terminal outputs.
- No reliable post-tool textual or structured summary is emitted.
- The VS Code Codex experience relies on a proprietary orchestration layer and app server not exposed via the public API.

This led to tabling further Codex automation due to high implementation cost and poor ROI.

New information confirms that **Codex is available as an official CLI**, documented at:

https://developers.openai.com/codex/cli

The Codex CLI provides:
- A local, client-side agent loop
- Built-in sandboxing and approval policies
- Persistent run history
- File system and command execution
- A user experience comparable to the VS Code Codex extension

This reopens Codex automation as a viable path using a *client-driven* rather than *API-driven* model.

---

## Decision

Conduct a **Phase‑0 protocol spike** to evaluate the Codex CLI as the primary Codex execution surface.

This spike explicitly **supersedes the API-based Codex runner strategy** (ADR-OA03.2) and explores whether Codex CLI can serve as a first-class agent engine within the OA01 orchestration strategy.

---

## Scope of the Spike

### In Scope

1. Install and run Codex CLI in a TNH‑Scholar workspace
2. Execute representative code-editing tasks non-interactively
3. Observe and document:
   - File modifications
   - Console output
   - Run history artifacts
4. Evaluate sandbox and permission configuration
5. Identify durable artifacts suitable for meta-agent ingestion

### Out of Scope

- Reimplementing Codex orchestration logic
- Direct use of the OpenAI Responses API
- VS Code extension instrumentation or UI scraping
- Cost optimization or billing guarantees (observational only)

---

## Evaluation Questions

The spike should answer the following:

1. Can Codex CLI reliably perform multi-step code edits in a repo?
2. Where and how are run transcripts and summaries stored?
3. Can Codex be run deterministically with project-local configuration?
4. What artifacts can be harvested post-run without UI integration?
5. Is the CLI behavior functionally equivalent to Codex in VS Code?

---

## Success Criteria

The spike is considered successful if:

- Codex CLI can be invoked as a subprocess with predictable behavior
- Workspace diffs can be captured via git after execution
- A minimal, repeatable artifact set can be defined (diff + transcript)
- The CLI eliminates the need for a custom tool-loop orchestrator

---

## Architectural Implications

If successful, Codex CLI becomes:

- The **Codex execution engine**
- A peer to Claude Code in the agent runner architecture
- A client-driven agent whose outputs are harvested, not synthesized

This aligns with ADR-OA01’s principle that **orchestration owns provenance and lifecycle, not the agent loop itself**.

---

## Next Steps (Post-Spike)

If the spike succeeds:

1. Mark ADR-OA03.2 as superseded
2. Introduce a new Codex CLI runner ADR (Phase‑1)
3. Define a standard agent-run artifact contract
4. Integrate Codex CLI into the meta-agent orchestration layer

---

## Status

**Proposed — Phase‑0 Spike**
