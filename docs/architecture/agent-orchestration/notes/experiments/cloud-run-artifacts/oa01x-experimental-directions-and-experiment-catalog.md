---
title: "OA01.x Experimental Directions and Experiment Catalog"
description: "Structured, evolving catalog of broad experimental directions and concrete experiments for long-running supervised multi-agent overnight runs."
owner: ""
author: "Aaron Solomon, Codex"
status: archived
created: "2026-04-14"
updated: "2026-04-14"
related_adrs:
  - "/docs/architecture/agent-orchestration/adr/adr-oa01.2-conceptual-spike-orientation-based-supervisory-orchestration.md"
  - "/docs/architecture/agent-orchestration/adr/adr-oa01.3-conceptual-spike-practical-approach.md"
  - "/docs/architecture/agent-orchestration/adr/adr-oa01.4-headless-agent-communication-functional-spike.md"
---

# OA01.x Experimental Directions and Experiment Catalog

> Experimental artifact from an independent cloud run. Preserve for reference only. Do not treat this document as maintained workflow authority for the current `OA01.x` spike.

## Purpose

This document extends the `OA01.x` exploratory line into a **broad, consistent, and execution-ready experimental portfolio** focused on the big-picture objective:

- large-scale headless overnight runs,
- complex iterative task loops,
- supervised feedback cycles,
- team-of-agents collaboration,
- and cross-model diversity (Codex, Claude Code, Gemini-class systems, and non-coding general reviewers).

It is intended as a long-running catalog. Directions are deliberately diverse so the program does not overfit to one runner, one model family, or one orchestration assumption.

## How to Use This Catalog

Each direction includes:

1. hypothesis,
2. risk being tested,
3. specific experiments,
4. readiness gate to move forward.

Use the IDs (`DIR-x.EX-y`) in run notes and experiment reports.

## Shared Experiment Card Schema

Every experiment should be logged with the same structure:

- **Experiment ID**
- **Question**
- **Inputs** (task class, model mix, runtime constraints)
- **Procedure** (bounded steps)
- **Primary Metrics** (quality, reliability, cost, latency, supervision load)
- **Pass / Pivot / Fail Criteria**
- **Artifacts** (prompt packages, transcript bundles, diffs, review notes)
- **Next Action**

---

## Direction 1: Headless Reliability and Runtime Drift Tolerance

### Hypothesis
A supervisor can keep overnight work productive despite CLI/API drift by using lightweight capability probes and fallback routing.

### Experiments

- **DIR-1.EX-1 Capability Handshake Matrix**
  - Validate startup probes for Codex CLI, Claude Code CLI, and Gemini-compatible execution surfaces.
  - Track probe confidence and false-positive/false-negative rates.
- **DIR-1.EX-2 Invocation Drift Canary**
  - Run nightly canary tasks that test known invocation contracts and flag drift before full overnight workflows.
- **DIR-1.EX-3 Graceful Degradation Routing**
  - When one runner surface fails, route to alternate worker model with preserved task brief and evidence context.

### Readiness Gate
At least 10 consecutive nightly canary cycles with no undetected invocation failures.

---

## Direction 2: Orientation Quality and Supervisor Choice Discipline

### Hypothesis
Orientation-first supervision (implementation, repair, design review, evaluation, synthesis) improves task continuation quality versus undifferentiated prompting.

### Experiments

- **DIR-2.EX-1 Orientation A/B Baseline**
  - Compare identical repo tasks under (a) no explicit orientation and (b) explicit orientation packets.
- **DIR-2.EX-2 Orientation Misclassification Recovery**
  - Intentionally start tasks with a wrong orientation; measure supervisor ability to reclassify quickly.
- **DIR-2.EX-3 Orientation Granularity Sweep**
  - Compare 4-orientation vs 7-orientation taxonomies for quality and operator burden.

### Readiness Gate
Orientation-based runs outperform baseline on completion quality and rework burden in at least two task classes.

---

## Direction 3: Multi-Agent Team Topologies

### Hypothesis
Small role-specialized teams (builder, tester, reviewer, synthesizer) outperform single-agent loops for complex overnight tasks.

### Experiments

- **DIR-3.EX-1 Team Size Sweep**
  - Compare 1-agent, 2-agent, and 4-agent structures on equivalent tasks.
- **DIR-3.EX-2 Fixed vs Dynamic Role Assignment**
  - Evaluate whether static role assignment or per-iteration role reassignment yields better throughput and fewer contradictions.
- **DIR-3.EX-3 Hierarchical vs Peer Teaming**
  - Compare strict supervisor hierarchy against peer-review swarm plus supervisor arbitration.

### Readiness Gate
A repeatable topology shows measurable gains in completion quality without disproportionate cost growth.

---

## Direction 4: Cross-Model Diversity and Cognitive Complementarity

### Hypothesis
Combining coding-focused models with general reasoning reviewers improves architecture and risk detection quality.

### Experiments

- **DIR-4.EX-1 Coding + General Reviewer Pairing**
  - Pair a coding agent with a non-coding general reviewer for design critique and edge-case surfacing.
- **DIR-4.EX-2 Triad Composition Study**
  - Builder (coding model) + critic (general model) + verifier (coding model) triad on structural changes.
- **DIR-4.EX-3 Dissent Injection Protocol**
  - Require one reviewer to generate strongest objections before merge recommendation.

### Readiness Gate
Cross-model ensembles detect materially more high-severity issues than coding-only teams on shared benchmark tasks.

---

## Direction 5: Feedback Loops and Iterative Repair Convergence

### Hypothesis
Explicit loop contracts (attempt cap, evidence minimum, escalation rules) reduce infinite retries and improve convergence.

### Experiments

- **DIR-5.EX-1 Loop Contract Variants**
  - Compare strict (max 3 loops) vs adaptive loop budgets.
- **DIR-5.EX-2 Evidence-First Retry Rule**
  - Require fresh evidence before each retry; compare against unrestricted retries.
- **DIR-5.EX-3 Forced Human Escalation Thresholds**
  - Evaluate intervention thresholds based on contradiction count and validation stagnation.

### Readiness Gate
Loop stall rate decreases while successful repair completion remains stable or improves.

---

## Direction 6: Validation Harness Depth and Structural Test Coverage

### Hypothesis
Layered validation (unit/integration/behavioral/trajectory checks) increases trust in unattended overnight outputs.

### Experiments

- **DIR-6.EX-1 Validation Pyramid Trial**
  - Expand from smoke-only checks to layered test tiers per task risk class.
- **DIR-6.EX-2 Structural Trajectory Assertions**
  - Add trajectory-level assertions (step order, policy checks, contradiction events).
- **DIR-6.EX-3 Differential Validator Routing**
  - Choose validator depth by risk profile and diff scope.

### Readiness Gate
False-accept rate drops without unacceptable runtime expansion.

---

## Direction 7: Provenance, Observability, and Replayability

### Hypothesis
Fine-grained traces and normalized run artifacts make overnight failures diagnosable and reproducible enough for continuous improvement.

### Experiments

- **DIR-7.EX-1 Unified Run Artifact Bundle**
  - Ensure every run emits normalized prompts, outputs, diffs, checks, decision vectors, and escalation notes.
- **DIR-7.EX-2 Trace-Driven Root Cause Benchmark**
  - Measure median time-to-root-cause with and without structured traces.
- **DIR-7.EX-3 Partial Replay Protocol**
  - Re-run failed segments from checkpointed context to test replay utility.

### Readiness Gate
Median root-cause time and replay success rate both improve over baseline.

---

## Direction 8: Supervision UX and Human-in-the-Loop Load Shaping

### Hypothesis
Supervisor-facing summaries with priority scoring can keep humans in control while minimizing overnight interruption burden.

### Experiments

- **DIR-8.EX-1 Morning Review Compression**
  - Generate compact "overnight digest" packets and compare review time against raw transcript review.
- **DIR-8.EX-2 Escalation Priority Scoring**
  - Rank escalations by impact and uncertainty; test whether humans resolve highest-value items first.
- **DIR-8.EX-3 Approval Granularity Trial**
  - Compare per-step approvals vs per-batch approvals vs risk-triggered approvals.

### Readiness Gate
Human review time per completed overnight run falls while post-review defect leakage does not rise.

---

## Direction 9: Safety Rails, Policy Enforcement, and Blast-Radius Control

### Hypothesis
Path-level and action-level policy enforcement can make long unattended runs operationally safe enough for regular use.

### Experiments

- **DIR-9.EX-1 Policy Violation Adversarial Suite**
  - Seed forbidden actions and verify deterministic block behavior.
- **DIR-9.EX-2 Worktree Isolation Stress Test**
  - Launch concurrent overnight tasks and confirm no cross-task workspace contamination.
- **DIR-9.EX-3 Rollback Drill Protocol**
  - Simulate bad-run rollback recovery across multiple branches.

### Readiness Gate
Policy evasion rate stays near zero under adversarial tests, with successful rollback drills.

---

## Direction 10: Cost, Throughput, and Overnight Capacity Planning

### Hypothesis
Token/time budgets and adaptive routing can scale overnight runs while maintaining acceptable quality-per-dollar.

### Experiments

- **DIR-10.EX-1 Budgeted Planner Policies**
  - Compare fixed-budget vs adaptive-budget run policies.
- **DIR-10.EX-2 Throughput Saturation Curve**
  - Measure quality, latency, and failure as parallel overnight workload increases.
- **DIR-10.EX-3 Cheap-First / Strong-Later Routing**
  - Evaluate staged model escalation pipelines.

### Readiness Gate
An operating envelope is established for safe parallel load with defined quality and budget bounds.

---

## Direction 11: Benchmarking and Comparative Evaluation Framework

### Hypothesis
A stable benchmark suite prevents narrative bias and enables reliable architectural decisions.

### Experiments

- **DIR-11.EX-1 Task Corpus Definition**
  - Build a balanced benchmark across implementation, repair, design review, and evaluation tasks.
- **DIR-11.EX-2 Blind Review Panel**
  - Evaluate output artifacts with blinded raters (human and AI) to reduce model-brand bias.
- **DIR-11.EX-3 Longitudinal Score Tracking**
  - Track metrics across weeks to detect regressions and model drift.

### Readiness Gate
Benchmark results become the default decision input for strategy pivots.

---

## Direction 12: Adaptive Planning and Subagent Strategy

### Hypothesis
Selective subagent invocation and planner-level decomposition improve complex-task completion when bounded by explicit contracts.

### Experiments

- **DIR-12.EX-1 Subagent Use Policy Trial**
  - Compare "no subagents", "always subagents", and "policy-gated subagents".
- **DIR-12.EX-2 Decomposition Depth Sweep**
  - Test shallow vs deep decomposition plans for iterative complex tasks.
- **DIR-12.EX-3 Contradiction Arbitration Loop**
  - Add an arbiter pass when subagents disagree materially.
- **DIR-12.EX-4 Remote Planner Independence Trial**
  - Run the same OA01.x planning prompt across repeated cloud or remote executions and compare overlap, novelty, and retained provenance.
  - Require explicit evidence of subagent use before treating delegated planning as an observed capability rather than a plausible explanation.

### Readiness Gate
Subagent usage policy is defined by evidence, not preference, and tied to measurable task classes.

---

## Proposed Execution Waves

- **Wave A (Foundational)**: Directions 1, 2, 7, 9
- **Wave B (Teaming + Looping)**: Directions 3, 4, 5, 12
- **Wave C (Scale + Governance)**: Directions 6, 8, 10, 11

Each wave should end with a synthesis memo that captures:

- what should become maintained,
- what should remain experimental,
- what should be retired.

## External Resource Scan (Used to Shape This Catalog)

This catalog directionally aligns with the current (as of 2026-04-14) ecosystem signals:

- OpenAI Codex non-interactive execution and subagent workflows:
  - https://developers.openai.com/codex/noninteractive
  - https://developers.openai.com/codex/subagents
  - https://developers.openai.com/codex/cli/reference
- Anthropic Claude Code docs (CLI/headless usage patterns):
  - https://docs.anthropic.com/en/docs/claude-code/overview
- Google Gemini CLI/API orchestration references:
  - https://ai.google.dev/gemini-api/docs
- Structural testing research for LLM agents (trace-first methods):
  - https://arxiv.org/abs/2601.18827

These references are not treated as architectural truth. They are used as external directional inputs while `OA01.x` keeps primary authority in in-repo ADRs and experiment evidence.

## Near-Term Backlog (First 14 Experiments)

1. DIR-1.EX-1
2. DIR-1.EX-2
3. DIR-2.EX-1
4. DIR-2.EX-2
5. DIR-3.EX-1
6. DIR-4.EX-1
7. DIR-5.EX-1
8. DIR-6.EX-1
9. DIR-7.EX-1
10. DIR-8.EX-1
11. DIR-9.EX-1
12. DIR-10.EX-1
13. DIR-11.EX-1
14. DIR-12.EX-1

This set intentionally spans foundational robustness, orientation quality, teaming, safety, scale, and evaluation discipline.
