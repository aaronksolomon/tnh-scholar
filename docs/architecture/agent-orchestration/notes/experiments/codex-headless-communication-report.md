---
title: "Codex Headless Communication Report"
description: "Consolidated report on direct headless Codex communication experiments, observed errors, and the currently viable invocation pathway."
owner: ""
author: "Codex"
status: current
created: "2026-04-12"
updated: "2026-04-12"
---

# Codex Headless Communication Report

## Summary

A viable headless Codex communication path was found.

The working path is:

- use the existing authenticated default Codex home under `~/.codex`,
- run with `--ephemeral`,
- and separate `stdout` from `stderr`.

Under that pattern, Codex can return clean machine-readable JSON on `stdout` while most startup and environment noise is confined to `stderr`.

This is enough to support further `OA01.4` experimentation.

The most important conceptual finding is simple:

- headless collaboration is not useless,
- the communication path is viable,
- and the main issue is channel cleanliness rather than inability to collaborate.

## What Was Tested

The experiments focused on four questions:

1. Can Codex be reached reliably in headless mode at all?
2. Can startup noise be reduced or isolated?
3. Can a real review task produce usable output through a repeatable interface?
4. Does Codex behave differently when run from a more user-shell-like path?

The main trials were:

- default authenticated invocation with a trivial `ACK` prompt,
- isolated `CODEX_HOME` invocation with a trivial `ACK` prompt,
- authenticated invocation with explicit `stdout` and `stderr` separation,
- authenticated invocation with a real ADR review task and explicit `stdout` and `stderr` separation,
- a direct user-shell run of the same `ACK` command,
- and a repo-local wrapper-script invocation of both `ACK` and a real review task.

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

## Practical Interpretation

These experiments separated two questions clearly:

- can headless collaboration happen,
- and can it happen through a clean enough channel?

The first answer is now yes.

The second answer is also provisionally yes, but with an important qualifier:

- the cleanest current path is user-shell-like execution,
- while live agent execution can still work if `stdout` and `stderr` are separated.

## Documented-vs-Observed Matrix

| Surface | Documented / expected | Observed here | Confidence | Notes |
|---|---|---|---|---|
| Headless execution | `codex exec` is the official non-interactive surface | Confirmed usable for `ACK` and real review prompts | High | This is the main viable path |
| Authenticated default home | Expected to carry normal user auth and state | Required for successful headless runs in these experiments | High | Default `~/.codex` works |
| Isolated repo-local Codex home | Plausibly useful for cleaner isolation | Reduced some state noise but failed with `401 Unauthorized` | High | Isolation without auth is not viable |
| `--ephemeral` mode | Expected to reduce persistence | Works and still returns usable output | High | Adds harmless backfill warning |
| `stdout` / `stderr` separation | Not a Codex feature, but standard CLI pattern | Strongly improves usability by isolating collaboration output | High | Best cleanup move so far |
| Repo root working directory | Expected to pick up repo context | Returned `AGENTS.md` when asked for instruction filename | Medium | Inference depends on Codex's self-report |
| Nested subdirectory inside repo | Expected to still resolve repo context | Also returned `AGENTS.md` | Medium | Suggests upward repo discovery works |
| Outside-repo context | Expected not to see repo-local guidance | Returned `NONE` and inspected `/tmp` instead | Medium | Good boundary-condition result |
| User shell vs live agent execution | Expected to differ in ambient state and permissions | User shell was much cleaner; live agent path remained noisy but usable | High | Context matters materially |
| Repo-local wrapper script | Expected to normalize invocation only | Worked for `ACK` and real review, but did not remove environment noise | High | Useful helper, not a full solution |
| Planning / multi-agent surfaces | Not yet directly tested behaviorally | `features list` exposes `multi_agent` as stable `true`; `collaboration_modes` shows removed `true` | Low | Visible surface exists, behavior still untested |

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

## Current Recommendation

For ongoing `OA01.4` experiments, the best current path is:

1. keep the authenticated default `~/.codex` home,
2. always use `--ephemeral`,
3. always separate `stdout` and `stderr`,
4. treat `stdout` as the collaboration channel,
5. treat `stderr` as diagnostics only.

In other words, prefer operational isolation over full state isolation.

When possible, prefer a user-shell-like launch context over an artificial tool or sandbox context.

## Do We Need Configuration Work?

Possibly, but not as an immediate prerequisite.

What may eventually be worth cleaning up:

- stale or mismatched local Codex state database
- noisy plugin metadata under `~/.codex/.tmp/plugins/`
- a more explicit authenticated isolated-state setup, if the project later wants reproducible repo-local Codex environments

What is not required right now:

- fixing all Codex local warnings before continuing experiments

The communication path is already usable enough without that cleanup.

## What This Means for Further Experiments

The immediate next step is not broader architecture. It is careful research and experimentation around the conditions that make Codex behave "as if run by the user."

That likely includes:

- authentication and credential location,
- persistence and state handling under `~/.codex`,
- plugin loading behavior,
- home-directory and shell expectations,
- and what permissions are required for a repo-local helper to preserve user-shell behavior.

The most likely-success avenues now appear to be:

1. continue user-shell-mimic experiments rather than isolated-home experiments,
2. build out the matrix with a few more rows before adding more code,
3. test one narrow planning or multi-agent surface that already appears in the feature set,
4. and defer any dangerous-mode or stronger-permission experiments until the normal path is better understood.

## Conclusion

The experiments support a clear outcome:

- headless Codex communication is viable,
- the main challenge is noisy local CLI/runtime behavior,
- and that noise can be managed well enough for continued experimentation by using ephemeral runs and separating `stdout` from `stderr`.

That is sufficient to continue the communication-focused `OA01.4` spike.
