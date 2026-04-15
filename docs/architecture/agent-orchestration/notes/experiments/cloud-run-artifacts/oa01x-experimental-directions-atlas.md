---
title: "OA01.x Experimental Directions Atlas"
description: "Broad and structured experimental direction set for validating multi-agent, headless overnight execution with supervised feedback loops across Codex, Claude Code, and additional model reviewers."
owner: "aaronksolomon"
author: "Codex"
status: archived
created: "2026-04-14"
updated: "2026-04-14"
---

# OA01.x Experimental Directions Atlas

> Experimental artifact from an independent cloud run. Preserve for reference only. Do not treat this document as maintained workflow authority for the current `OA01.x` spike.

## Purpose

Define a **broad, testable, and implementation-oriented** experimental direction set for OA01.x, with a concrete experiment catalog focused on this target:

- large-scale **headless overnight runs**,
- complex **iterative task loops**,
- explicit **supervision and feedback**,
- **team-of-agents collaboration**,
- and **multi-provider participation** (Codex, Claude Code, and non-coding/general AI reviewers).

This atlas is intentionally design-forward and experiment-heavy, so it can drive long-running execution without prematurely freezing one architecture.

## Scope and boundaries

- This document defines **experimental directions**, **specific experiments**, and **acceptance signals**.
- It does **not** lock final production architecture; ADR decisions should be promoted only after repeated evidence.
- Experiments are meant to run incrementally and can be split into PR-sized slices.

## External surface scan used for this atlas (2026-04-14)

The following publicly documented capabilities informed prioritization:

- Codex supports subagents, non-interactive execution (`codex exec`), JSONL event streaming, output schemas, and CI-oriented auth/automation patterns: <https://developers.openai.com/codex/subagents>, <https://developers.openai.com/codex/noninteractive>, <https://developers.openai.com/codex/agent-approvals-security>.
- Claude Code docs describe multi-agent workflows, scheduling/automation patterns, and CI action integrations (`anthropics/claude-code-action@v1`): <https://code.claude.com/docs/en/overview>, <https://code.claude.com/docs/en/github-actions>.
- Gemini docs provide large-scale asynchronous batch execution and parallel/compositional function-calling patterns: <https://ai.google.dev/gemini-api/docs/batch-api>, <https://ai.google.dev/gemini-api/docs/function-calling>.
- MCP specification confirms standardized host/client/server tool and resource integration patterns plus safety expectations: <https://modelcontextprotocol.io/specification/2025-06-18>.
- GitHub Actions matrix/concurrency mechanics provide practical substrate for overnight distributed runs: <https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations>.

## Direction portfolio (broad set)

### Direction D1 — Supervisor Loop Kernel Reliability

**Hypothesis:** Overnight viability depends first on deterministic supervisor loop behavior and failure visibility.

**Experiments:**

1. **D1.E1 Run-state determinism stress test**
   - Replay same workflow inputs 25x; compare end states, events, and manifests for drift.
2. **D1.E2 Crash-restart recovery drill**
   - Force process kill at multiple lifecycle points; validate resume semantics and idempotency.
3. **D1.E3 Timeout/heartbeat watchdog trials**
   - Inject hung-step scenarios; ensure supervisor terminates, records cause, and continues queue.

**Success signal:** ≥95% deterministic terminal classifications; zero silent hangs.

---

### Direction D2 — Headless Execution at Scale (Nightly)

**Hypothesis:** Large unattended runs fail mostly from orchestration hygiene rather than model quality.

**Experiments:**

1. **D2.E1 Overnight burn-in (8h)**
   - Queue mixed tasks continuously for 8 hours with bounded resource quotas.
2. **D2.E2 Multi-runner parallelism sweep**
   - Sweep concurrency levels (1/2/4/8/16 workers) and map failure-rate inflection points.
3. **D2.E3 Queue backpressure validation**
   - Overfeed workload intentionally; verify graceful shed/defer behavior.

**Success signal:** stable completion rate, no resource runaway, no orphaned worktrees.

---

### Direction D3 — Cross-Agent Team Topologies

**Hypothesis:** Task quality improves when role-specialized teams are explicit (Implementer, Tester, Critic, Integrator).

**Experiments:**

1. **D3.E1 Topology A/B/C comparison**
   - Compare single-agent vs 2-agent pair vs 4-role team on same benchmark tasks.
2. **D3.E2 Lead-agent delegation protocol**
   - Evaluate quality/cycle-time when one lead coordinates subagents.
3. **D3.E3 Team memory contract**
   - Add shared artifact ledger; measure context-loss reduction across handoffs.

**Success signal:** higher merge-ready output per wall-clock hour without elevated policy violations.

---

### Direction D4 — Multi-Provider Agent Fabric

**Hypothesis:** Best outcomes come from provider diversity, not single-model monoculture.

**Experiments:**

1. **D4.E1 Codex implementer + Claude reviewer pipeline**
   - Primary code changes from Codex; structured critique from Claude.
2. **D4.E2 Claude implementer + Codex verifier pipeline**
   - Reverse pairing to identify directional asymmetry.
3. **D4.E3 General-model “out-of-box critic” stage**
   - Add GPT/Gemini/Claude general review pass focused on risk-blind spots and alternative designs.

**Success signal:** measurable defect-prevention lift and architecture-option diversity.

---

### Direction D5 — Feedback Loops and Evaluator Quality

**Hypothesis:** Iterative loops only work if evaluators are strict, legible, and difficult to game.

**Experiments:**

1. **D5.E1 Mechanical vs semantic evaluator stack**
   - Compare simple pass/fail checks to rubric-based semantic scoring.
2. **D5.E2 Anti-gaming adversarial suite**
   - Introduce intentionally superficial fixes to test evaluator robustness.
3. **D5.E3 Loop budget tuning**
   - Sweep max-iteration budgets and stopping criteria to optimize ROI.

**Success signal:** fewer false passes and better correlation with human review outcomes.

---

### Direction D6 — Prompt/Brief Contract Robustness

**Hypothesis:** Most multi-agent instability is prompt-contract drift, not runtime defects.

**Experiments:**

1. **D6.E1 Structured collaborator-brief schema trial**
   - Enforce shared brief fields (intent, boundaries, evidence expected, stop conditions).
2. **D6.E2 Ambiguity injection benchmark**
   - Add controlled ambiguity and test whether clarification loops resolve it safely.
3. **D6.E3 Instruction inheritance policy**
   - Validate propagation precedence across system/team/step-level instructions.

**Success signal:** reduced divergence across agents given equivalent objectives.

---

### Direction D7 — Artifact Contract and Provenance Depth

**Hypothesis:** Overnight supervision depends on first-class artifacts more than on chat transcripts.

**Experiments:**

1. **D7.E1 Canonical artifact minimum set validation**
   - Enforce transcript/final_response/policy_summary/manifest/event stream completeness.
2. **D7.E2 Evidence traceability audit**
   - Randomly sample runs; verify each decision can be traced to reproducible evidence.
3. **D7.E3 Compression/retention policy sweep**
   - Tune long-run storage to preserve forensic usefulness at manageable cost.

**Success signal:** post-run audits can reconstruct agent behavior without ambiguity.

---

### Direction D8 — Safety Rails for Long-Running Autonomy

**Hypothesis:** Productive autonomy requires fail-closed controls and granular escalation pathways.

**Experiments:**

1. **D8.E1 Approval-mode matrix**
   - Evaluate read-only/workspace-write/full-access profiles against productivity and risk.
2. **D8.E2 Destructive-command trap suite**
   - Simulate unsafe operations; verify hard blocks + legible violation records.
3. **D8.E3 Sandbox-escape resilience checks**
   - Validate boundary behavior for shell/network/file-scope policy combinations.

**Success signal:** zero high-severity safety breaches in unattended windows.

---

### Direction D9 — Human-in-the-Loop Supervision UX

**Hypothesis:** Effective supervision needs concise, interruption-minimizing review surfaces.

**Experiments:**

1. **D9.E1 Morning digest quality test**
   - Produce nightly summary bundles for human triage in <15 minutes.
2. **D9.E2 Escalation-threshold experiments**
   - Tune conditions that wake/notify humans during overnight runs.
3. **D9.E3 Decision checkpoint templates**
   - Standardize “approve/revise/reject/defer” packets to speed supervisor actions.

**Success signal:** low cognitive load and higher supervisor agreement consistency.

---

### Direction D10 — Worktree and Diff Lifecycle Economics

**Hypothesis:** Worktree isolation and diff hygiene determine whether large run volumes stay operational.

**Experiments:**

1. **D10.E1 Worktree churn endurance test**
   - High-volume create/run/discard cycles to uncover filesystem/git bottlenecks.
2. **D10.E2 Branch naming + garbage-collection policy test**
   - Validate recoverability and cleanup under heavy overnight load.
3. **D10.E3 Diff-size governance experiment**
   - Enforce size caps and auto-splitting to maintain reviewability.

**Success signal:** clean rollback/recovery with no stale workspace accumulation.

---

### Direction D11 — Task Routing and Portfolio Optimization

**Hypothesis:** Headless throughput increases when tasks are auto-routed by complexity/risk profile.

**Experiments:**

1. **D11.E1 Task classifier prototype**
   - Route tasks into lanes: trivial/mechanical/semantic/high-risk.
2. **D11.E2 Provider-role routing policy**
   - Map task lanes to best agent/provider role combinations.
3. **D11.E3 Cost-aware routing loop**
   - Include budget pressure in planner decisions while maintaining quality SLOs.

**Success signal:** improved quality-adjusted throughput per dollar/hour.

---

### Direction D12 — Evaluation Harness and Benchmark Corpus

**Hypothesis:** Long-term progress stalls without a stable benchmark corpus and scorecard.

**Experiments:**

1. **D12.E1 OA01.x benchmark pack v0**
   - Curate 30–50 representative repository tasks with gold review expectations.
2. **D12.E2 Replayable seed-run framework**
   - Re-run benchmark suites across architecture/prompt/policy changes.
3. **D12.E3 Regression gate for orchestration changes**
   - Block merges that degrade key run-quality metrics beyond thresholds.

**Success signal:** trendable, reproducible evidence of platform improvement.

## Prioritized execution waves

### Wave 1 (Immediate)

- D1, D2, D6, D8
- Goal: make overnight runs safe, restartable, and interpretable.

### Wave 2 (Near-term)

- D3, D4, D5, D7
- Goal: maximize multi-agent effectiveness and feedback-loop quality.

### Wave 3 (Scale-up)

- D9, D10, D11, D12
- Goal: operationalize at high run volume with measurable governance.

## Core metrics for all experiments

- **Run completion:** completed / started.
- **Intervention rate:** human interrupts per 100 runs.
- **Policy breach rate:** violations by severity tier.
- **Loop efficiency:** iterations to accepted output.
- **Review acceptance:** share of outputs accepted with minimal edits.
- **Cost efficiency:** accepted-output per unit compute budget.
- **Time-to-digest:** median morning supervisor triage time.

## Minimum reporting template per experiment

For consistency, each executed experiment should produce a note with:

1. hypothesis,
2. setup and inputs,
3. run counts and timestamps,
4. outcomes against core metrics,
5. failure taxonomy,
6. recommendation: iterate / promote / discard,
7. follow-up experiment IDs.

## Current recommendation

Proceed with **Wave 1 as the next long-running execution track**, while reserving a fixed percentage of capacity for D4 cross-provider experiments so multi-agent diversity is validated early and not postponed.
