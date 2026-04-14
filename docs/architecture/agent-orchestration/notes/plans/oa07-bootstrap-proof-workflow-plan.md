---
title: "OA07 Bootstrap Proof Workflow Plan"
description: "Plan for the first generic maintained bootstrap-proof workflow, aligned with the existing agent development workflow but constrained by the current headless runtime."
owner: ""
author: "OpenAI GPT-5 Codex"
status: current
created: "2026-04-10"
updated: "2026-04-10"
---
# OA07 Bootstrap Proof Workflow Plan

Purpose: define the next planning slice after PR-8. The goal is not more runtime substrate. The goal is to prove that the maintained headless path can complete one useful repository task through a generic workflow shape that is recognizably aligned with the existing `AGENT_WORKFLOW.md`.

This note is intentionally about the workflow shape and operator plan, not about one task-specific implementation diff.

## Why This Note Exists

PR-8 established a maintained local/headless entry point:

- `tnh-conductor`
- a thin bootstrap app layer
- a maintained kernel
- a managed git worktree boundary
- canonical artifacts, manifests, metadata, and final state

That is necessary, but it is still only substrate.

The next strategic question is:

Can the maintained runtime complete one useful repo-native task through a generic orchestration workflow rather than only through test scaffolding?

## Design Anchor

This plan should mimic the existing repo workflow in `AGENT_WORKFLOW.md`, not invent a detached conductor-only pattern.

That matters because the desired direction is not “make a special workflow for one task.” It is “begin expressing the existing development process through the maintained orchestration path.”

The first proof should therefore preserve these high-level ideas from the existing workflow:

- a task is identified before execution,
- implementation is the primary machine-executed phase,
- deterministic validation happens after implementation,
- human review still happens outside the automated loop,
- failures should usually lead to correction, not rollback.

However, the first maintained proof cannot yet mirror the full `AGENT_WORKFLOW.md` loop mechanically, because the maintained runtime does not yet support the full semantic-control layer.

## Current Maintained Runtime Reality

The current maintained runtime can honestly support:

- loading one YAML workflow from disk via `src/tnh_scholar/agent_orchestration/kernel/adapters/workflow_loader.py`
- `RUN_AGENT`
- `RUN_VALIDATION`
- `ROLLBACK(pre_run)`
- `STOP`
- managed worktree execution
- canonical run artifacts and provenance capture

The current maintained runtime does **not** yet support a real generic correction loop in the same way that `AGENT_WORKFLOW.md` describes, because:

- the maintained headless entry fails closed on `EVALUATE` and `GATE`
- `RUN_AGENT.prompt` is still a static string in `src/tnh_scholar/agent_orchestration/kernel/models.py`
- there is no maintained task-parameter rendering layer yet
- there is no maintained prompt-library execution layer in the bootstrap entry
- `RUN_VALIDATION` currently supports builtins and generated harnesses, but not an arbitrary task-defined validation command set

That means the first bootstrap proof should mimic the **center** of the existing workflow, not the full loop.

## What The First Proof Should Actually Demonstrate

The first bootstrap proof should show that the maintained path can do all of the following in one run:

1. start from a committed base ref,
2. create a managed worktree,
3. execute one real coding task against this repository,
4. run deterministic validation,
5. persist canonical metadata, events, manifests, and terminal state,
6. leave behind a reviewable diff in the managed worktree,
7. allow the human to decide whether the result is worth promoting into the normal git review flow.

That is enough to count as bootstrap proof.

It is **not** necessary for the first proof to show:

- semantic evaluator routing,
- gate approvals,
- commit/push/PR automation,
- prompt-catalog compilation,
- multi-agent collaboration,
- iterative fix loops inside one run.

## Generic Workflow Requirement

The workflow itself should stay generic.

That means:

- do not create a one-off workflow whose only meaning is “implement `--prompt-dir`”
- do not encode a task slug, file list, or one-off validation command directly into the workflow shape
- keep the workflow close to the existing development loop: implement, validate, stop

The task-specific part should live outside the workflow body.

## Recommended Generic Proof Shape

The first maintained proof workflow should use a minimal generic shape like this:

```yaml
workflow_id: bootstrap_proof_generic
version: 1
description: Generic maintained bootstrap proof workflow for one narrow repo task.
entry_step: implement
steps:
  - id: implement
    opcode: RUN_AGENT
    agent: codex
    prompt: |
      Read the bootstrap proof task brief at the standard repository path.
      Implement only that task.
      Run local checks before finishing when practical.
      Do not commit, push, or open a PR.
    routes:
      completed: validate
      error: STOP
      killed_timeout: STOP
      killed_idle: STOP
      killed_policy: STOP

  - id: validate
    opcode: RUN_VALIDATION
    run:
      - tests
      - lint
    routes:
      completed: STOP
      error: STOP
      killed_timeout: STOP
      killed_idle: STOP
      killed_policy: STOP

  - id: STOP
    opcode: STOP
```

This is generic in structure:

- one implementation step,
- one deterministic validation step,
- one terminal stop.

The task-specific material moves into a separate task brief.

## Task Brief Convention

Because the maintained runtime does not yet render task parameters into prompts, a generic workflow needs one stable convention for task discovery.

The simplest viable convention is:

- the workflow prompt tells the agent to read one checked-in task brief at a standard path
- the operator updates that task brief before the run
- the workflow itself remains unchanged across different proof tasks

Recommended shape:

- one repo path reserved for the current bootstrap-proof task brief
- the brief contains:
  - task objective
  - scope boundaries
  - files likely in scope
  - acceptance criteria
  - preferred validation expectations
  - explicit “do not” rules

This keeps task specificity out of the workflow while avoiding premature prompt-program tooling.

## Validation Strategy

Validation is the hardest genericity constraint in the current maintained runtime.

Today the bootstrap profile maps builtin validator IDs in `src/tnh_scholar/agent_orchestration/app/profile.py`:

- `tests`
- `lint`
- `typecheck`

Those are runtime-profile choices, not workflow-specific commands.

This leads to one important planning rule:

The first proof task should be chosen so that broad maintained validation is acceptable.

That is why a narrow repo task like `tnh-gen --prompt-dir` is attractive:

- it is small enough to validate deterministically,
- it is useful product work,
- and it should be able to live under broad repo hygiene checks better than a large architectural task.

If the broad builtins prove too expensive or too noisy, the next change should still preserve a generic workflow by introducing a generic proof-validation profile, not by making the workflow task-specific.

## Recommended Operator Assets

Before the first proof run, the repo should contain:

1. one generic bootstrap-proof workflow YAML
2. one current bootstrap-proof task brief at a stable path
3. one short operator note with the run command and success criteria

This is enough to run the maintained headless path honestly.

It is not necessary to build a full prompt catalog or workflow registry first.

## Operator Command

The operator path should be explicit and stable.

Recommended command shape:

```bash
poetry run tnh-conductor run \
  --workflow <generic-proof-workflow-path> \
  --repo-root . \
  --base-ref main
```

Optional executable overrides can still be provided if needed, but they should not be the central story.

The operator note should document:

- the workflow path
- the task brief path
- the run command
- where to inspect canonical run artifacts
- where the managed worktree will appear
- what counts as proof success

## What Needs To Be Planned Versus Built

The bootstrap-proof slice needs planning in four areas.

### 1. Workflow Shape

This is mostly a design decision:

- keep the workflow generic
- keep it close to the current real development pattern
- avoid semantic-control features that are not yet maintained

### 2. Task Brief Convention

This is the missing bridge between “generic workflow” and “real task.”

Without a stable task-brief convention, the workflow will drift into being task-specific.

### 3. Validation Posture

This is the main practical constraint.

We need to decide whether the first proof can succeed under the current broad builtin validation profile, or whether a generic proof-validation profile is required first.

### 4. Proof Success Criteria

The run should only count as bootstrap proof if it produces:

- a useful repository diff,
- green deterministic validation,
- canonical artifacts,
- and a reviewable result that a human would plausibly carry forward.

## What Should Stay Out Of Scope

To stay aligned with the direction memo, this proof slice should not expand into:

- maintained `EVALUATE`
- maintained `GATE`
- multi-step correction routing
- commit/push/PR automation
- prompt-library infrastructure
- richer rollback design

Those may come later, but they are not needed to prove the maintained path is useful.

## Mapping To The Existing Agent Workflow

The first maintained proof should be understood as a compressed subset of the existing `AGENT_WORKFLOW.md`.

Approximate mapping:

- Task Discovery:
  handled by the human before the run, via the task brief
- Initial Design / Design Review:
  handled before the run, outside the maintained runtime
- Implementation:
  mapped to one `RUN_AGENT`
- Deterministic validation:
  mapped to one `RUN_VALIDATION`
- Human review and follow-up:
  handled after the run, outside the maintained runtime

So the first proof is not “the whole workflow is automated.”

It is:

The maintained orchestration path can now execute the implementation-and-validation core of the real workflow against a real repo task.

## Recommended Next Slice

The next implementation slice should be planned as:

- add the generic bootstrap-proof workflow file
- add the task-brief convention and first task brief
- add the operator run note
- run the proof against one narrow repo-native task
- inspect the run artifacts and resulting worktree

Only after that run should the project decide whether the next missing lever is:

- a generic correction loop,
- a better validation profile,
- or PR automation.

## Acceptance Criteria For This Planning Note

This planning note is successful if it establishes agreement on the following:

- the first proof workflow should be generic, not task-tailored
- the first proof should mimic the existing agent workflow only at the implementation-and-validation core
- the task-specific content should live in a task brief, not in the workflow body
- the maintained headless CLI is necessary but not sufficient by itself
- no large prompt/workflow tooling build-out is required before attempting the first proof run

## Practical Recommendation

Use `tnh-gen --prompt-dir` as the first task candidate, but do **not** bake that task into the workflow.

Instead:

- keep one generic bootstrap-proof workflow,
- write one task brief for the `--prompt-dir` task,
- run the maintained headless CLI against that pair,
- and judge the result by the artifacts, validation, and usefulness of the resulting diff.
