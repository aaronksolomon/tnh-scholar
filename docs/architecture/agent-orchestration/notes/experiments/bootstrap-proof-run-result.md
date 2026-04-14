---
title: "Bootstrap Proof Run Result"
description: "Concise record of the first maintained bootstrap proof execution, observed issues, and design implications."
owner: ""
author: "Codex"
status: current
created: "2026-04-10"
updated: "2026-04-10"
---
# Bootstrap Proof Run Result

## Summary

The first maintained bootstrap-proof executions were operationally useful even though they did not complete the intended repo task. The maintained conductor created a real managed worktree, launched the maintained runtime, persisted run metadata and step artifacts, and exposed important operator UX and runner-contract weaknesses.

This was not a wasted test. It was the first concrete proof that the current bootstrap path can run far enough to reveal real system design issues instead of only substrate gaps.

## What Happened

The bootstrap-proof workflow at `docs/architecture/agent-orchestration/bootstrap-proof/generic-bootstrap-proof.workflow.yaml` was executed through `tnh-conductor` against `main`.

Observed behavior:

- The conductor created a managed branch and worktree successfully.
- The run produced canonical run metadata, event logs, and step artifacts under `.tnh-conductor/runs/`.
- The `implement` step failed immediately with Codex CLI exit code `2`.
- The workflow routed `error -> STOP`, so the top-level run still reported `completed`.

The first failed run exposed one operator mistake: the workflow assets were not yet committed to `main`, so the managed worktree could not see the task brief. After those assets were committed, a second run failed in the same high-level way for a different reason.

## Confirmed Issues

### Run Status UX

The run summary currently allows `completed:STOP` even when the real task step failed. This is mechanically correct according to workflow routing, but it is misleading for operators and weak for bootstrap testing.

### No Heartbeat or Live Progress UX

`tnh-conductor` currently gives no in-progress terminal feedback while a run is active. For overnight or unattended runs this may be acceptable, but for active testing and diagnosis the operator needs at least step-level heartbeat output.

### Runner Contract Drift

The maintained Codex adapter assumes a fixed CLI flag contract. The current adapter invocation includes `--ask-for-approval`, but the installed Codex CLI help output does not expose that flag. That likely explains the immediate exit code `2` failure.

This is the most important design finding from the test. The external headless agent CLI should not be treated as a stable static API.

### Weak Failure Diagnostics

The current runner artifact set preserves metadata but not enough startup failure detail. A usage or argument error from the runner should leave a directly reviewable stderr artifact so the operator can diagnose failures without inspecting implementation code.

## Design Implications

The maintained runtime still appears viable for bootstrap, but the design center likely needs correction.

The durable value in the current system is:

- managed worktree isolation
- canonical run artifacts and provenance
- workflow control skeleton
- validation integration
- minimal last-resort rollback

The weaker assumption is the idea that Codex CLI and Claude CLI can be integrated as fixed-flag subprocess adapters. The more realistic direction is a thin adaptive conductor that probes installed runner capabilities and shapes invocation accordingly.

## Directions To Explore

- Add clear operator heartbeat output from the maintained kernel or app layer.
- Rework top-level run status so failed task execution does not read as successful completion.
- Persist runner stderr and startup diagnostics as first-class artifacts.
- Add runner capability probing before invocation.
- Treat adaptive runner invocation as a likely long-term requirement, not as an incidental patch.

## Current Conclusion

Bootstrap testing succeeded in the most important sense: it exposed the real next problem.

The next architecture question is not whether the conductor can create a managed worktree and launch a run. It can. The next question is how thin, adaptive, and operator-legible the maintained runner boundary should be when the external agent CLIs are powerful but evolving systems.
