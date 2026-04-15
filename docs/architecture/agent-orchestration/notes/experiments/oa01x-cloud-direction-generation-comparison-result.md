---
title: "OA01.x Cloud Direction Generation Comparison Result"
description: "Independent result note for the three cloud-run OA01.x direction-generation attempts, focused on overlap, novelty, subagent evidence, and practical value."
owner: ""
author: "Codex"
status: current
created: "2026-04-14"
updated: "2026-04-14"
related_docs:
  - "/docs/architecture/agent-orchestration/notes/experiments/cloud-run-artifacts/oa01x-experimental-directions-atlas.md"
  - "/docs/architecture/agent-orchestration/notes/experiments/cloud-run-artifacts/oa1x-experimental-directions-matrix.md"
  - "/docs/architecture/agent-orchestration/notes/experiments/cloud-run-artifacts/oa01x-experimental-directions-and-experiment-catalog.md"
---

# OA01.x Cloud Direction Generation Comparison Result

## Experiment ID

`DIR-12.EX-4`

## Question

If the same broad OA01.x prompt is run in the cloud multiple times, potentially with native subagents, does it produce materially new strategic ground for TNH Scholar or mostly alternate packaging of the same portfolio?

## Inputs

- one prompt requesting a broad and well-documented experimental portfolio for overnight headless supervised multi-agent work,
- three saved result artifacts:
  - [OA01.x Experimental Directions Atlas](/architecture/agent-orchestration/notes/experiments/cloud-run-artifacts/oa01x-experimental-directions-atlas.md)
  - [OA1.x Experimental Directions Matrix](/architecture/agent-orchestration/notes/experiments/cloud-run-artifacts/oa1x-experimental-directions-matrix.md)
  - [OA01.x Experimental Directions and Experiment Catalog](/architecture/agent-orchestration/notes/experiments/cloud-run-artifacts/oa01x-experimental-directions-and-experiment-catalog.md)
- existing OA01.x anchors:
  - [ADR-OA01.2](/architecture/agent-orchestration/adr/adr-oa01.2-conceptual-spike-orientation-based-supervisory-orchestration.md)
  - [ADR-OA01.3](/architecture/agent-orchestration/adr/adr-oa01.3-conceptual-spike-practical-approach.md)
  - [ADR-OA01.4](/architecture/agent-orchestration/adr/adr-oa01.4-headless-agent-communication-functional-spike.md)

## Procedure

1. Read the three cloud-run artifacts as separate attempts rather than as one coordinated package.
2. Compare direction coverage, experiment shape, and alignment with current OA01.x bottlenecks.
3. Check for explicit retained evidence of native subagent use.
4. Judge practical value for TNH Scholar against current known constraints from the maintained OA01.x line.

## Run Counts and Timestamp

- run count reviewed: `3`
- review date: `2026-04-14`
- exact cloud execution timestamps were not preserved in the saved docs

## Outcomes Against Core Metrics

### Practical usefulness

- **useful:** yes
- **novel enough to keep:** yes, but as raw exploratory material rather than as maintained direction authority

The three attempts did expand the space in a few worthwhile ways:

- they widened the direction set beyond the current narrow communication focus,
- they surfaced missing program-level concerns such as benchmark corpus design, cost envelopes, morning-digest UX, routing, and comparative provider studies,
- and they repeatedly reinforced that subagent policy should be evidence-led rather than assumption-led.

### Overlap and uniqueness

The artifacts overlap heavily in intent and mid-level concepts, but they are not duplicates.

Observed shape:

- the **atlas** is the broadest and most operations-oriented of the three,
- the **matrix** is the cleanest executive summary and best at wave sequencing,
- the **catalog** is the strongest fit for a maintained experiment register because it has stable IDs and readiness gates.

Approximate token-set overlap across the full texts was moderate rather than extreme, at roughly `0.29` to `0.31` pairwise Jaccard similarity. In practice, the conceptual overlap is higher than that number suggests because the documents often rename the same core lanes:

- reliability / drift tolerance,
- team topology,
- cross-provider diversity,
- feedback loops,
- supervision UX,
- safety,
- provenance,
- economics,
- benchmarking,
- and subagent strategy.

### Novel directions

The most useful additions relative to the current OA01.2 to OA01.4 focus were:

- benchmark-corpus thinking,
- explicit budget and throughput experiments,
- morning-digest and escalation UX,
- and routing / portfolio optimization.

These are valuable because they highlight what will matter later if the project gets past the present communication and supervision proof stage.

The weakest additions were the broad long-horizon directions that outrun current evidence, especially:

- large-scale nightly concurrency sweeps,
- generalized distributed-run substrate assumptions,
- and polished multi-provider fabrics before the local comparison cases are established.

### Subagent evidence

There is **no retained artifact evidence** in these three documents that native subagents were actually used during the cloud runs.

What is present:

- external references to documented subagent capability,
- repeated recommendation to test subagent policy,
- and one document section explicitly about adaptive planning and subagent strategy.

What is absent:

- event logs,
- spawn/wait traces,
- explicit run notes saying subagents were invoked,
- or attempt-specific provenance showing delegated branches of work.

So the correct reading is:

- subagent use was requested,
- subagent-aware thinking appears in the outputs,
- but actual subagent execution is unconfirmed from the saved evidence.

### Cloud usefulness

The cloud approach looks useful as a **cheap independent ideation and reframing pass**, not yet as strong evidence of orchestration feasibility.

What it did well:

- produced broad option space quickly,
- gave three differently organized passes on the same problem,
- and generated some directions that the current OA01.x thread had not yet made first-class.

What it did not prove:

- reliable supervision loops,
- meaningful multi-agent execution quality,
- native subagent behavior,
- or overnight headless operational value inside TNH Scholar's real repo workflow.

The cloud run acted more like an external strategy workshop than a meaningful systems proof.

## Failure Taxonomy

- **provenance gap:** attempt-level runtime evidence was not preserved
- **comparison gap:** no shared scorecard or benchmark task was attached to the three attempts
- **authority drift risk:** broad strategy generation moved ahead of current OA01.x bottlenecks
- **repackaging overlap:** the three attempts often renamed similar themes instead of opening sharply distinct paths

## Findings

### 1. The work was not wasted

These were useful exploratory outputs. They produced several directions worth keeping in the OA01.x conversation, especially benchmarking, economics, digest UX, and routing.

### 2. The three attempts are better treated as one exploratory cluster than three separate breakthroughs

Their main value is convergence mapping:

- what ideas keep recurring,
- what surfaces only once,
- and which framing is most maintainable.

### 3. The catalog is the best candidate for maintained use

Of the three, the catalog is the best structural base because it gives stable IDs and readiness gates. The matrix is the best summary view. The atlas is the best source of broad optionality.

### 4. The cloud approach is useful only in a bounded role

For TNH Scholar, cloud runs appear useful for:

- independent brainstorming,
- alternate framing,
- and broad literature or capability synthesis.

They are weak for:

- proving actual orchestration behavior,
- proving subagent execution,
- and deciding whether overnight collaboration is operationally viable.

### 5. Agent orchestration still looks directionally worthwhile for TNH Scholar, but only if kept narrow

The strongest near-term case is not "large-scale overnight teams."
The strongest near-term case is:

- bounded supervisory comparisons,
- explicit orientation-based task framing,
- evidence-first retry loops,
- and small team topology tests on real repository tasks.

That remains aligned with `OA01.2` to `OA01.4`.

## Recommendation

`iterate`

Keep the cloud-generated materials as exploratory input, but do not treat them as proof that the cloud path or large-scale orchestration is working.

They should remain clearly marked experimental artifacts rather than maintained workflow documents.

## Valuable Ideas To Lift Into The Maintained Spike

- keep subagent policy evidence-led rather than preference-led,
- keep supervision UX focused on short human-review artifacts,
- keep artifact expectations explicit but minimal,
- and keep the decisive comparison centered on direct-agent versus tightly bounded supervised use.

## Follow-Up Experiment IDs

- `SPIKE-02`
- `SPIKE-03`
- `SPIKE-04`
- `SPIKE-05`

## Current Recommendation

Pursue the current OA01.x spike only through the next narrow tranche:

- direct-agent vs supervised-agent comparison on the same repo task,
- supervised run with explicit artifact scorecard,
- explicit native subagent evidence capture,
- and minimal operator-facing review artifacts.

Do not spend heavily yet on broad distributed overnight architecture. The current evidence supports continued experimentation, not platform commitment.
