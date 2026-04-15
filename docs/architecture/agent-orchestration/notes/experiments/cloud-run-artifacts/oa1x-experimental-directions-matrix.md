---
title: "OA1.x Experimental Directions Matrix"
description: "Comprehensive direction and experiment matrix for testing feasibility of large-scale headless overnight supervised multi-agent orchestration."
owner: ""
author: "Aaron Solomon, Codex"
status: archived
created: "2026-04-14"
updated: "2026-04-14"
---
# OA1.x Experimental Directions Matrix

> Experimental artifact from an independent cloud run. Preserve for reference only. Do not treat this document as maintained workflow authority for the current `OA01.x` spike.

This document extends the `ADR-OA01.x` exploration thread into a single, consistent experiment portfolio aimed at the following big-picture feasibility question:

> Can TNH Scholar run large-scale, headless, overnight, supervised iterative workflows with feedback loops, using teams of coding agents and non-coding reviewer/intelligence agents?

Primary architecture anchors:

- [ADR-OA01](/architecture/agent-orchestration/adr/adr-oa01-agent-orchestration-strategy.md)
- [ADR-OA01.1](/architecture/agent-orchestration/adr/adr-oa01.1-conductor-strategy-v2.md)
- [ADR-OA01.2](/architecture/agent-orchestration/adr/adr-oa01.2-conceptual-spike-orientation-based-supervisory-orchestration.md)
- [ADR-OA01.3](/architecture/agent-orchestration/adr/adr-oa01.3-conceptual-spike-practical-approach.md)
- [ADR-OA01.4](/architecture/agent-orchestration/adr/adr-oa01.4-headless-agent-communication-functional-spike.md)

## 1. Portfolio Design Goals

The experimental portfolio is designed to:

1. Keep each experiment small enough to run independently.
2. Test one uncertainty per experiment.
3. Preserve compatibility with the maintained OA04.x/OA07.x contracts.
4. Build toward overnight autonomy with explicit supervisory checkpoints.
5. Include heterogeneous model families (coding + general reasoning/review).

## 2. Shared Experiment Template (Use for Every OA1.x Experiment)

Every experiment should declare:

- **Hypothesis**: What should become true if the direction works.
- **Setup**: Workflow, agent mix, budgets, repos, test fixture.
- **Execution Window**: Daytime interactive vs overnight headless.
- **Observable Outputs**: Required artifacts (`metadata.json`, `events.ndjson`, step manifests, diffs, evaluator output).
- **Pass/Fail Criteria**: Binary gates + graded quality signals.
- **Failure Taxonomy**: Invocation, communication, semantic drift, policy, review deadlock, rollback issues.
- **Promotion Rule**: What must be true to move to the next experiment.

## 3. Experimental Directions and Specific Experiments

### Direction A — Headless Multi-Agent Reliability at Duration

**Purpose:** prove that long-running, unattended orchestration loops remain legible and recoverable.

- **A1: 2-hour controlled endurance run**
  - Hypothesis: single-worker + supervisor loop can complete 5+ iterations without manual intervention.
  - Measure: run completion ratio, artifact completeness, interruption recovery quality.
- **A2: Overnight reliability run (8-10 hours)**
  - Hypothesis: OA07.1 worktree lifecycle + rollback controls are sufficient for unattended operation.
  - Measure: completion status, number of recoverable failures, final diff reviewability.
- **A3: Stress run with injected transient failures**
  - Hypothesis: retry/rollback policy handles flaky model/API/tool calls without orphaning run state.
  - Measure: successful continuation after injected faults.

### Direction B — Supervisory Feedback Loops and Iterative Quality Gain

**Purpose:** verify that evaluate/replan loops improve outcome quality across iterations.

- **B1: Baseline no-feedback run**
  - Establish baseline quality for a fixed task.
- **B2: Single-loop feedback run**
  - Add one evaluator cycle; compare quality delta vs baseline.
- **B3: Multi-loop capped run (max 4 loops)**
  - Hypothesis: quality improves through loop 2-3, then plateaus.
  - Measure: quality score by loop, loop cost, contradiction frequency.
- **B4: Contradictory-review handling run**
  - Inject conflicting evaluator feedback; validate deterministic contradiction-resolution rules.

### Direction C — Role-Specialized Team Topologies

**Purpose:** find team structures that maximize quality per token/time under supervision.

- **C1: Pair topology (Builder + Reviewer)**
- **C2: Trio topology (Planner + Builder + Reviewer)**
- **C3: Quartet topology (Planner + Builder + Verifier + Red-team critic)**
- **C4: Dynamic handoff topology**
  - Hypothesis: explicit phase-based role handoff reduces context bloat and drift.

For C1-C4, compare:

- task throughput,
- defect escape rate,
- number of supervisor interventions,
- cost and runtime.

### Direction D — Cross-Vendor Agent Interoperability

**Purpose:** validate mixed-agent workflows across Codex, Claude Code, and non-coding/general-intelligence reviewers.

- **D1: Codex worker + Claude reviewer**
- **D2: Claude worker + Codex reviewer**
- **D3: Coding worker + GPT/Gemini/Claude-general review panel**
  - Non-coding agents provide architecture criticism, ambiguity detection, and alternative strategy proposals.
- **D4: Rotating primary worker by stage**
  - Hypothesis: model-family specialization by stage improves net quality.

Primary question: does mixed-family diversity improve robustness and idea quality without excessive coordination overhead?

### Direction E — Prompt/Protocol Surface Design for Supervisory Control

**Purpose:** refine the interaction surface so a supervisor can manage teams with predictable behavior.

- **E1: Minimal brief protocol**
  - shortest collaboration frame that still yields reliable structured responses.
- **E2: Rich structured brief protocol**
  - expanded brief including intent, constraints, and expected output schema.
- **E3: Policy-explicit brief protocol**
  - embeds authority boundaries and rollback conditions directly.
- **E4: Drift-resistant recap protocol**
  - periodic compact recap summaries to maintain coherence in long runs.

Measure response determinism, protocol adherence, and context-window efficiency.

### Direction F — Safety, Policy, and Governance Behavior Under Real Workload

**Purpose:** prove safety rails hold under realistic pressure and ambiguity.

- **F1: Protected-branch guard validation**
- **F2: Forbidden-command temptation scenario**
  - ensure agents refuse or escalate when prompted toward blocked operations.
- **F3: Rollback correctness matrix**
  - validate `ROLLBACK(pre_run)` behavior across success/failure paths.
- **F4: Human escalation trigger quality**
  - test if escalation requests occur at the right uncertainty/risk thresholds.

### Direction G — Evaluator and Validation Backend Maturity

**Purpose:** mature quality gates needed for unattended progression.

- **G1: Script validator reliability run**
- **G2: Harness backend parity check**
  - compare generated vs predefined harness outcomes on same task.
- **G3: Evaluator contradiction fixtures**
  - freeze fixture suite for disagreement scenarios.
- **G4: Confidence-calibrated stop/go decisions**
  - hypothesis: calibrated confidence labels reduce both false-positive passes and false-negative blocks.

### Direction H — Economic Feasibility and Budget-Aware Orchestration

**Purpose:** map cost-performance frontier for overnight team runs.

- **H1: Fixed-budget quality frontier**
- **H2: Fixed-quality minimum-cost search**
- **H3: Adaptive budget controller**
  - raise/lower model tier and loop depth based on progress signal.
- **H4: Timeboxed overnight planner**
  - enforce wall-clock budget with best-effort quality maximization.

### Direction I — Dataset of Runs for Meta-Learning and Operational Tuning

**Purpose:** convert runs into a reusable evidence base for improving orchestration policy.

- **I1: Run taxonomy standardization**
- **I2: Failure clustering analysis**
- **I3: Cross-run recommendation engine (human-in-the-loop)**
- **I4: Replay-based policy tuning experiments**

### Direction J — Human Supervision UX and Command Surface

**Purpose:** ensure humans can supervise overnight systems without excessive cognitive load.

- **J1: Morning review digest quality test**
  - does the morning summary let a maintainer decide go/no-go in less than 10 minutes?
- **J2: Supervisor intervention affordance test**
  - can a human pause/redirect safely with minimal commands?
- **J3: Uncertainty-first alerting test**
  - tune which events trigger wake-up/escalation.
- **J4: Review handoff consistency test**
  - verify continuity across different supervisors.

## 4. Suggested Sequence (Broad but Practical)

To keep this long-running exploration coherent, run in waves:

1. **Wave 1 (Foundations):** A1, B1, E1, F1, G1
2. **Wave 2 (Loop Quality):** B2, B3, C1, D1, E2, G3
3. **Wave 3 (Overnight + Team Diversity):** A2, C2, C3, D3, H1, J1
4. **Wave 4 (Governance + Economics):** F2, F3, G4, H2, H3, J3
5. **Wave 5 (Scale + Learning):** A3, C4, D4, I1-I4, J4

## 5. Minimum Artifact Contract for OA1.x Experimental Runs

Each run should persist at least:

- canonical run metadata,
- event stream,
- per-step manifest,
- diff/status evidence,
- evaluator output,
- supervisor decision record,
- final result classification (`success`, `bounded-failure`, `needs-human`, `unsafe-stop`).

This keeps OA1.x experimentation compatible with OA04.3 provenance and OA07 safety expectations.

## 6. External Signals Incorporated (Snapshot: 2026-04-14)

The following external documentation was used as directional input for cross-vendor experiment design:

- OpenAI Codex repository (`openai/codex`) for CLI/headless execution surface concepts:
  - https://github.com/openai/codex
- Anthropic Claude headless agent SDK docs:
  - https://platform.claude.com/docs/en/agent-sdk/headless
- Gemini CLI repository for non-interactive/automation usage patterns:
  - https://github.com/google-gemini/gemini-cli

These references are treated as evolving operational inputs; rerun capability checks before each new experiment wave.

## 7. Exit Criteria for the OA1.x Exploration Program

The OA1.x program should be considered feasibility-positive when all are true:

1. At least two overnight runs (A2) complete with recoverable failure handling and reviewable outputs.
2. At least one mixed-vendor team topology (Direction D) beats single-vendor baseline on quality-adjusted cost.
3. Feedback loops (Direction B) show repeatable quality improvement over no-loop baseline.
4. Safety rails (Direction F) successfully block or escalate unsafe operations.
5. Supervisors can review and disposition runs from digest artifacts without full transcript replay.

If these are not met, OA1.x should produce a bounded recommendation on which assumptions failed and whether to narrow or pivot the architecture.
