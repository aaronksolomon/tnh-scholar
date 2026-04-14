---
title: "Codex Headless Communication Report"
description: "Consolidated report on direct headless Codex communication experiments, observed errors, and the currently viable invocation pathway."
owner: ""
author: "Codex"
status: current
created: "2026-04-12"
updated: "2026-04-14"
---

# Codex Headless Communication Report

## Summary

Headless Codex communication is viable, but the surface is still only partially understood.

What is now clear:

- `codex exec` is usable for machine-readable collaboration,
- user-shell context matters materially,
- repo-local config is active and useful,
- native subagent behavior is available in headless mode,
- and `plugins` plus `shell_snapshot` are major noise contributors in this environment.

What is not yet clear:

- the functional cost of disabling noisy surfaces,
- the value of persistence/state features that currently look like noise,
- whether a user-launched supervisory agent is materially better than wrapper-mediated collaboration,
- and how much of Codex's native collaboration/product surface should be reused rather than rebuilt around.

## Experiment Sequence

### E1. Baseline Headless Reachability

- default authenticated invocation with a trivial `ACK` prompt
- result: success
- learning: Codex is reachable headlessly with the default authenticated home

### E2. Isolated Home Trial

- repo-local `CODEX_HOME` with a trivial `ACK` prompt
- result: failure
- learning: isolated state without auth is not viable; noise dropped but auth failed

### E3. Stream Separation

- authenticated invocation with explicit `stdout` and `stderr` separation
- result: success
- learning: this is the key cleanup move; collaboration output is clean on `stdout`

### E4. Real Review Prompt

- authenticated invocation with a real ADR review prompt and explicit `stdout`/`stderr` separation
- result: success
- learning: the channel is not only alive; it can produce useful review findings

### E5. User-Shell Comparison

- the same `ACK` command run from the user's shell
- result: success with clean `stdout` and empty `stderr`
- learning: Codex behaves better in a real user-shell context than in the live agent execution context

### E6. Repo-Local Wrapper

- wrapper-script invocation of both `ACK` and a real review task
- result: success
- learning: a tiny wrapper is useful for normalization and capture, but does not itself reproduce user-shell cleanliness

### E7. Repo-Local Config

- repo-local `.codex/config.toml` with `collab` and `collab_exec` profiles
- result: success
- learning: repo-local Codex config is active and can shape local CLI behavior, but did not materially reduce the core noise by itself

### E8. Native Subagent Smoke Test

- headless prompt explicitly requesting one subagent
- result: success
- learning: native subagent behavior is available in headless `exec`; `spawn_agent` and `wait` events appear in JSONL output

### E9. Feature-Noise Reduction

- wrapper runs with `--disable plugins`
- wrapper runs with `--disable plugins --disable shell_snapshot`
- result: success
- learning: `plugins` and `shell_snapshot` account for most of the noise in this environment

### E10. Low-Noise Native Subagent Path

- wrapper + repo-local `collab` profile + `--disable plugins --disable shell_snapshot` + explicit subagent prompt
- result: success
- learning: the lower-noise path still preserves native subagent collaboration events and returns clean machine-readable output

### E11. User-Shell Supervisory Trial

- shell-launched Codex supervisor using the supervisory-shell-trial assets
- result: useful but not clean
- learning:
  - the supervisor did perform distinct delegated workstreams,
  - native subagent collaboration produced useful convergent findings,
  - but the first three spawns failed because the session could not fork parent rollout context cleanly,
  - so the supervisor had to recover by embedding explicit repo/task context in each subagent prompt

## Results

### 1. Default Authenticated Home Is Usable

Using the installed Codex CLI against the default authenticated home succeeded for both a trivial handshake and a real review task.

Evidence:

- handshake output: `tmp/codex-stdout.jsonl`
- review output: `tmp/codex-review-stdout.jsonl`

The review task produced concrete findings about `OA01.4`, so this was not only a connectivity test.

### 2. Isolated `CODEX_HOME` Reduced Some Noise but Broke Authentication

Running with an isolated repo-local `CODEX_HOME` removed the broken local state-db warnings, but the invocation then failed with authentication errors.

Observed sequence:

- initial websocket retries with temporary server-side `500` errors,
- fallback to HTTP,
- then repeated `401 Unauthorized` responses because the isolated state did not carry usable auth.

This means isolated state is not currently a drop-in cleanup solution.

### 3. `stdout` and `stderr` Separation Is the Key Cleanup Move

Separating output streams was the most useful cleanup improvement.

When run as:

```bash
codex exec --json --ephemeral ... > useful.jsonl 2> diagnostics.log
```

the result is:

- clean JSON event stream on `stdout`,
- noisy but ignorable startup/runtime diagnostics on `stderr`.

This is the strongest practical outcome from the experiments.

### 4. User-Shell Context Is Cleaner Than Tool-Launched Context

The same `ACK` command run from the user's own shell produced a cleaner result than my tool-launched runs:

- clean JSON on `stdout`,
- empty `stderr`.

Evidence:

- user-shell output: `tmp/codex-user-stdout.jsonl`
- user-shell stderr: `tmp/codex-user-stderr.log`

This strongly suggests Codex expects a more normal user-shell environment than the live coding-agent tool environment naturally provides.

### 5. A Tiny Wrapper Script Works, But It Does Not Eliminate Environment Effects

A repo-local wrapper script was added at `scripts/codex_ephemeral_exec.py`.

It successfully:

- ran `ACK`,
- ran a real review task,
- captured `stdout` and `stderr`,
- and extracted a final message summary.

Evidence:

- wrapper `ACK` summary/output: `tmp/codex-script-stdout.jsonl`
- wrapper review output: `tmp/codex-script-review-stdout.jsonl`

But the wrapper did not remove the noisy warnings when launched from this live agent environment. That confirms the wrapper is useful for normalization, not for magically reproducing a true user shell.

### 6. Repo-Local Config Is Real but Not Sufficient

A repo-local `.codex/config.toml` was added and used successfully with named profiles.

This proved two things:

- repo-scoped Codex config is a real working surface,
- but simply adding a repo-local profile does not by itself clean up the dominant warnings in this environment.

The current repo-local profiles are useful as a place to hold experiment defaults, not yet as a solution to the noise problem.

### 7. Native Subagent Support Is Confirmed in Headless Mode

The strongest new finding from this round is that built-in Codex collaboration is not merely documented; it is visibly active in headless JSONL output.

Observed in `stdout`:

- `collab_tool_call` with `tool: "spawn_agent"`
- `collab_tool_call` with `tool: "wait"`
- subordinate agent completion message
- final top-level response after the wait completes

This means future work should be careful not to rebuild a subagent system that Codex already exposes natively.

### 8. Disabling `plugins` and `shell_snapshot` Materially Reduces Noise

The wrapper-based comparison showed:

- baseline wrapper path: heavy plugin-manifest and shell-snapshot warnings
- `--disable plugins`: plugin noise removed, state-db and shell-snapshot warnings remain
- `--disable plugins --disable shell_snapshot`: only state-db and ephemeral-thread warnings remain

This is the cleanest machine-oriented path found so far from the live agent environment.

### 9. Lower Noise Is Not Yet the Same Thing as Better Operation

The experiments show how to quiet the channel, but they do not yet show the cost of doing so.

Open question:

- are `plugins`, `shell_snapshot`, or state-backed behavior functionally useful for real supervisory collaboration, even if they are noisy in simple tests?

That question remains unanswered and should be treated as a real design concern rather than an implementation detail.

### 10. The First Supervisory Trial Was Productive but Exposed a Launch-Mode Constraint

The shell-launched supervisory run was the first meaningful test of Codex as a supervisor rather than a single headless worker.

What happened:

- the supervisor read the workflow contract and task brief,
- attempted three distinct subagent workstreams,
- failed on the first three spawn attempts with a parent-rollout fork error,
- retried with explicit repo and task context embedded in each subagent prompt,
- and then successfully completed three distinct review workstreams plus a final synthesis.

The subagent workstreams were genuinely distinct:

- strategic coherence of `OA01.2` to `OA01.4`
- practical feasibility and experiment shaping
- clarity, consistency, and pruning

This was not the same task repeated three times. The overlap happened later in the findings, where the three workstreams converged on similar structural issues.

The run also showed some limited creativity:

- the supervisor recovered from the failed spawn mode without user intervention,
- reframed the subagent prompts to compensate for missing inherited context,
- and produced a stronger synthesis than a straight-line single-pass critique would likely have produced.

At the same time, this was not a clean proof of the intended workflow contract.

Why:

- the supervisor had to retry the spawn strategy,
- it did a bit more framing and synthesis work itself than a strict reading of the contract would prefer,
- and the run surfaced a real product/runtime constraint rather than a purely prompt-level behavior question.

## Practical Interpretation

These experiments separated three questions clearly:

- can headless collaboration happen,
- can native Codex collaboration happen,
- and can either happen through a clean enough channel to support more meaningful experiments?

Current answers:

- headless collaboration: yes
- native subagent collaboration: yes
- clean enough operator channel: yes, provisionally

But the path is still exploratory. We have found a viable low-noise route, not yet an endorsed operating mode.

The supervisory-shell trial strengthens that conclusion:

- native supervisory use is plausible,
- but the collaboration surface still has operational constraints that need to be understood before treating it as a clean substrate.

## Matrix

| Surface | Expected / question | Observed here | Confidence | Current implication |
|---|---|---|---|---|
| `codex exec` | Official headless surface | Works for `ACK`, review prompts, and subagent prompts | High | Main baseline path |
| Authenticated default home | Should carry usable auth/state | Required for successful runs | High | Keep using `~/.codex` for now |
| Isolated repo-local home | Might give cleaner local isolation | Failed with `401 Unauthorized` | High | Not viable without explicit auth handling |
| `--ephemeral` | Should keep runs lightweight | Works; leaves a harmless backfill warning | High | Keep in baseline |
| `stdout` / `stderr` split | Should isolate usable output | Clean collaboration output on `stdout` | High | Essential baseline practice |
| Repo-local `.codex/config.toml` | Should be a real config layer | Profiles are active and usable | High | Good place for repo-scoped defaults |
| `collab` profile | Should reduce approval friction | Works, but does not materially change noise | Medium | Useful as a baseline profile |
| `collab_exec` profile | `inherit = "all"` might help | No meaningful cleanliness gain seen | Medium | Not currently special |
| Repo root context | Should pick up repo guidance | Returned `AGENTS.md` in prior tests | Medium | Repo discovery likely works |
| Outside-repo context | Should not see repo guidance | Returned `NONE` in prior tests | Medium | Boundary behaves plausibly |
| Wrapper script | Should normalize invocation | Works and returns a final summary JSON | High | Good thin launcher surface |
| Wrapper `stdin=DEVNULL` | Might remove stdin-related chatter | `Reading additional input from stdin...` still appears | Medium | Not fixed yet |
| `plugins` enabled | Might add useful capability, may add noise | Heavy plugin-manifest noise | High | Need cost/benefit testing |
| `plugins` disabled | Might reduce noise | Removes most stderr spam | High | Strong cleanup lever |
| `shell_snapshot` enabled | Might aid environment capture, may add noise | Snapshot cleanup warning appears | High | Need cost/benefit testing |
| `shell_snapshot` disabled | Might reduce noise | Removes snapshot warning | High | Strong cleanup lever |
| `multi_agent` feature | Documented and feature-listed | Behaviorally confirmed via JSONL `spawn_agent` and `wait` | High | Native collaboration surface is real |
| Native subagent events | Might not appear in headless mode | Visible in `stdout` JSONL | High | Reuse before rebuilding |
| Low-noise subagent path | Might break collaboration behavior | Still supports `spawn_agent` + `wait` | High | Best current machine-oriented path |
| Shell-launched supervisory run | Might show whether native supervision is meaningfully useful | Produced useful delegated work and synthesis, but required retry after fork-context failure | Medium | Promising enough to continue, but not a clean success |
| Initial fork-based subagent spawn | Might inherit parent context cleanly | Failed with `parent thread rollout unavailable for fork` | Medium | Launch mode matters; explicit context fallback may be necessary |
| State DB persistence | Might be useful despite warnings | Repeated migration discrepancy warning | Low | Understand before disabling or discarding |

## Error Classes Observed

### A. Local State Database Migration Warnings

Observed on the authenticated default home:

- `failed to open state db at /Users/phapman/.codex/state_5.sqlite: migration 24 was previously applied but is missing in the resolved migrations`
- `state db discrepancy during find_thread_path_by_id_str_in_subdir: falling_back`

Interpretation:

- the local Codex state database appears to be from an older or different internal migration set
- Codex continues operating by falling back rather than failing hard
- this is noisy but not currently fatal for headless use

Implication:

- this likely indicates a local Codex installation or state mismatch that could be cleaned up later
- it is not a blocker for immediate experimentation

### B. Plugin Manifest Warnings

Observed repeatedly:

- `ignoring interface.defaultPrompt: prompt must be at most 128 characters`

Interpretation:

- curated or installed plugin metadata under `~/.codex/.tmp/plugins/` contains manifests with overlong default prompts
- Codex logs the issue repeatedly during startup or plugin scanning

Implication:

- this appears to be upstream or CLI-environment noise, not project-specific failure
- it is currently harmless but very noisy

### C. Shell Snapshot Cleanup Warnings

Observed:

- failed deletion of shell snapshot temp files with `No such file or directory`

Interpretation:

- cleanup logic is attempting to remove temp snapshot files that are already gone

Implication:

- harmless noise

### D. Ephemeral Thread Backfill Warning

Observed after successful runs:

- `ephemeral threads do not support includeTurns`

Interpretation:

- Codex tries to backfill richer turn history even though ephemeral mode does not persist the session in the same way

Implication:

- harmless for current purposes
- another reason to treat `stdout` as the primary usable channel

### E. Isolated-State Authentication Failure

Observed under repo-local `CODEX_HOME`:

- websocket `500 Internal Server Error` during retries
- fallback to HTTP
- repeated `401 Unauthorized: Missing bearer or basic authentication in header`

Interpretation:

- repo-local isolated state lacks the authentication material used by the default home
- server-side transient websocket errors may also be present, but the decisive blocker was missing auth

Implication:

- a truly isolated state path would require explicit auth setup
- this is possible future work, but not required for current spike progress

### F. Personality / Model Warning Under Some Paths

Observed in lower-noise subagent runs:

- `Model personality requested but model_messages is missing, falling back to base instructions`

Interpretation:

- some model/profile combinations do not fully support the configured personality surface
- Codex falls back rather than failing hard

Implication:

- this is not currently a blocker
- but it means model/profile interactions are another surface worth understanding before turning defaults into stable tooling

### G. Parent Thread Rollout Unavailable for Fork

Observed in the first supervisory-shell run:

- `collab spawn failed: Fatal error: parent thread rollout unavailable for fork`

Interpretation:

- the spawned subagent path appears to expect parent rollout context that was not available in this launch mode
- the exact internal cause is still inferred rather than fully known, but the behavior is clear from the error and retry pattern

Implication:

- shell-launched native supervision works, but not all subagent spawn modes are equally dependable
- explicit task context in subagent prompts may currently be the safer path than assuming inherited context

## Current Recommendation

For machine-oriented experimentation from this live environment, the best current path is:

1. keep the authenticated default `~/.codex` home,
2. use repo-local profile `collab`,
3. use `--ephemeral`,
4. separate `stdout` and `stderr`,
5. disable `plugins` and `shell_snapshot` when the goal is a cleaner event channel,
6. treat `stdout` as the collaboration channel,
7. treat `stderr` as diagnostics only.

For higher-value next experiments, prefer a user-shell-launched supervisory run before doing much more wrapper or noise optimization.

For supervisory trials specifically:

- assume inherited fork-context may fail,
- and be prepared to pass explicit repo and task context to subagents.

## Open Questions

- What practical capability is lost when `plugins` are disabled?
- What practical capability is lost when `shell_snapshot` is disabled?
- Is the state DB warning merely noisy, or does it indicate degraded useful behavior?
- Can a user-launched supervisory Codex session coordinate real work more effectively than a thin wrapper-led collaboration pattern?
- How much of Codex's native subagent/planning surface should be treated as product capability to reuse rather than substrate to rebuild?
- Is inherited subagent fork-context dependable enough for future supervisory experiments, or should explicit-context delegation be the baseline?
- Does human framing remain necessary for genuine novelty and exploration, even if native supervision is operationally viable?

## Conclusion

The experiments now support a slightly stronger but still cautious conclusion:

- headless Codex communication is viable,
- native headless subagent collaboration is also viable,
- a materially cleaner invocation path exists,
- a shell-launched supervisory run can generate useful delegated analysis,
- but the costs of suppressing noisy surfaces are still unknown,
- and inherited subagent context currently looks less dependable than explicit-context delegation.

So the work remains exploratory. The next important step is not more local noise chasing by default. It is a more meaningful supervisory experiment, ideally launched from the user's shell, so the project can judge whether the native collaboration surface is genuinely useful for the direction now emerging in `OA01.2` to `OA01.4`.
