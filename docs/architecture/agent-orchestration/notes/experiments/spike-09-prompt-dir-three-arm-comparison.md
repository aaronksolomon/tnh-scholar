---
title: "SPIKE-09 Prompt Dir Three-Arm Comparison"
description: "Comparison of direct Codex, supervisory Codex, and kernel-mediated orchestration on the same bounded `tnh-gen --prompt-dir` implementation task."
owner: ""
author: "Codex"
status: current
created: "2026-04-16"
updated: "2026-04-16"
---

# SPIKE-09 Prompt Dir Three-Arm Comparison

## Experiment ID

`SPIKE-09`

## Question

On the same bounded implementation task, how do three arms compare in practical usefulness and behavior?

- direct single-agent Codex
- supervisory Codex with native subagents
- kernel-mediated orchestration through `tnh-conductor`

## Setup

Task brief:

- `/docs/architecture/agent-orchestration/supervisory-shell-trial/prompt-dir-task-brief.md`

Arms:

- direct Codex in isolated worktree: `tmp/prompt-dir-arms/worktrees/direct`
- supervisory Codex in isolated worktree: `tmp/prompt-dir-arms/worktrees/supervisory`
- kernel-mediated orchestration in managed worktree: `.tnh-conductor/worktrees/20260416T151658Z`

All Codex launches used the sanitized user-like environment established in `SPIKE-08`.

Primary artifacts:

- `tmp/prompt-dir-arms/direct.stdout.jsonl`
- `tmp/prompt-dir-arms/direct.stderr.log`
- `tmp/prompt-dir-arms/supervisory.stdout.jsonl`
- `tmp/prompt-dir-arms/supervisory.stderr.log`
- `.tnh-conductor/runs/20260416T151658Z/events.ndjson`
- `.tnh-conductor/runs/20260416T151658Z/metadata.json`
- `.tnh-conductor/runs/20260416T151658Z/artifacts/implement/policy_summary.json`

## Result

All three arms produced useful implementation work, which is the main positive finding of this experiment.

This was a small bounded task, so the direct arm naturally had the least coordination overhead and therefore looked cleaner. That should not be read as the main conclusion of the experiment.

The more important finding is that both alternative orchestration shapes showed credible viability:

- supervisory Codex demonstrated real native subagent invocation, recovery, and synthesis behavior
- kernel-mediated orchestration produced a real implementation path in its managed worktree rather than only scaffolding or trace output

The main weaknesses observed in the supervisory and kernel arms were operational:

- runtime overhead
- weak or delayed stopping behavior
- opaque execution-state visibility
- and some fragility in delegation and artifact integration

Those look more like improvable runtime issues than evidence that the orchestration approaches are fundamentally unworkable.

Observed at cutoff:

- direct arm: completed cleanly with final report and targeted tests passing
- supervisory arm: worktree reached a complete-looking implementation, but the parent supervisor process was still running when observation was cut off
- kernel arm: managed worktree contained a substantial implementation diff, but the conductor run had emitted only `step_started` provenance and had not written a final summary at cutoff

## Arm A: Direct Codex

Outcome:

- implemented the feature directly
- touched 8 files
- targeted validation passed

Changed files:

- `/docs/cli-reference/tnh-gen.md`
- `/src/tnh_scholar/cli_tools/tnh_gen/commands/config.py`
- `/src/tnh_scholar/cli_tools/tnh_gen/commands/list.py`
- `/src/tnh_scholar/cli_tools/tnh_gen/commands/run.py`
- `/src/tnh_scholar/cli_tools/tnh_gen/state.py`
- `/src/tnh_scholar/cli_tools/tnh_gen/tnh_gen.py`
- `/tests/cli_tools/test_tnh_gen.py`
- `/tests/cli_tools/test_tnh_gen_coverage.py`

Validation:

- `poetry run pytest tests/cli_tools/test_tnh_gen.py tests/cli_tools/test_tnh_gen_coverage.py`
- result: `65 passed, 2 warnings`

Practical read:

- on a simple bounded task, this arm had the least overhead and therefore the cleanest execution path
- it remains the right baseline for judging what the more complex orchestration arms add or cost

## Arm B: Supervisory Codex

Outcome:

- attempted explicit implementation and test/docs delegation to native subagents
- first two `spawn_agent` attempts failed because the parent thread rollout was unavailable for fork
- recovered by rephrasing the subagent launches without forked thread context
- implementation subagent succeeded
- test/docs subagent initially failed on patch application, but the worktree still ended up with the full expected file set

Changed files:

- `/docs/cli-reference/tnh-gen.md`
- `/src/tnh_scholar/cli_tools/tnh_gen/commands/config.py`
- `/src/tnh_scholar/cli_tools/tnh_gen/commands/list.py`
- `/src/tnh_scholar/cli_tools/tnh_gen/commands/run.py`
- `/src/tnh_scholar/cli_tools/tnh_gen/state.py`
- `/src/tnh_scholar/cli_tools/tnh_gen/tnh_gen.py`
- `/tests/cli_tools/test_tnh_gen.py`
- `/tests/cli_tools/test_tnh_gen_coverage.py`

Validation:

- direct inspection of the worktree passed
- `poetry run pytest tests/cli_tools/test_tnh_gen.py tests/cli_tools/test_tnh_gen_coverage.py`
- result: `63 passed, 2 warnings`

Important evidence:

- real delegation attempts are visible in `tmp/prompt-dir-arms/supervisory.stdout.jsonl`
- failure evidence is visible in `tmp/prompt-dir-arms/supervisory.stderr.log`

Practical read:

- this arm did prove native subagent invocation is viable in a headless run
- the supervisor respected the contract better than earlier experiments and did not immediately collapse into single-agent execution
- the main weaknesses were coordination fragility and stopping/visibility issues, not lack of useful output
- on a more decomposable task, this shape could plausibly outperform a single-agent pass if the current runtime issues are improved

## Arm C: Kernel-Mediated Orchestration

Outcome:

- managed worktree contained a substantial implementation diff before the run was cut off
- controller-level provenance remained sparse
- the run did not emit a final summary during observation

Changed files:

- `/docs/cli-reference/tnh-gen.md`
- `/src/tnh_scholar/cli_tools/tnh_gen/commands/config.py`
- `/src/tnh_scholar/cli_tools/tnh_gen/commands/list.py`
- `/src/tnh_scholar/cli_tools/tnh_gen/commands/run.py`
- `/src/tnh_scholar/cli_tools/tnh_gen/config_loader.py`
- `/src/tnh_scholar/cli_tools/tnh_gen/state.py`
- `/src/tnh_scholar/cli_tools/tnh_gen/tnh_gen.py`
- `/tests/cli_tools/test_tnh_gen.py`
- `/tests/cli_tools/test_tnh_gen_coverage.py`

Structural distinction:

- unlike the other two arms, this one introduced an explicit helper in `config_loader.py` for non-null override merging
- that is the main unique design direction across the three arms

Validation:

- local targeted pytest reproduction from the managed worktree did not complete cleanly because the fresh managed worktree virtualenv did not have `pytest` available yet
- result at manual check time: `pyenv: pytest: command not found`

Practical read:

- the kernel path did produce meaningful code, not just scaffolding
- this is positive evidence that the existing conductor codepath is viable enough to keep in the spike
- the main current limitations are weak observability, unclear completion state, and higher inspection cost
- those limitations may be tractable enough that the kernel path could become much more competitive on larger tasks

## Overlap And Uniqueness

Overlap:

- all three arms converged on the same user-facing feature shape
- all three touched the same core files for CLI callback, shared state, list/run/config plumbing, tests, and CLI docs
- all three routed the override through config loading rather than bypassing config resolution entirely

Uniqueness:

- direct arm: most complete and best validated
- supervisory arm: only arm with explicit native subagent evidence and coordination recovery behavior
- kernel arm: only arm to push the override-handling logic further down into `config_loader.py`

## Practical Conclusion

The main outcome is that supervisory Codex and `tnh-conductor` both look viable enough to keep pursuing in the `OA01.x` spike.

This experiment should be read as:

- direct execution is the least burdened path on a simple task
- supervisory execution is viable and now has explicit evidence of native subagent behavior
- kernel-mediated execution is viable and can produce real code in the managed worktree
- the main barriers are runtime overhead, stopping-condition behavior, and execution-state opacity

That is a positive result for the broader spike question, because those barriers appear operational and potentially improvable rather than architectural dead ends.

So the comparison does not show that single-agent execution is categorically better. It shows that the orchestration paths are promising, but they currently pay coordination and observability costs that are easy to see on a small task.

## Useful Artifacts

Most useful:

- `tmp/prompt-dir-arms/direct.stdout.jsonl`
- `tmp/prompt-dir-arms/supervisory.stdout.jsonl`
- `tmp/prompt-dir-arms/supervisory.stderr.log`
- `.tnh-conductor/runs/20260416T151658Z/metadata.json`
- `.tnh-conductor/runs/20260416T151658Z/events.ndjson`

Most useful worktrees:

- `tmp/prompt-dir-arms/worktrees/direct`
- `tmp/prompt-dir-arms/worktrees/supervisory`
- `.tnh-conductor/worktrees/20260416T151658Z`

## Next Action

Continue the spike with tasks that are large enough, or naturally decomposable enough, to give the supervisory and kernel arms a fairer opportunity to justify their overhead.

Focus the next round on improving and measuring:

- subagent spawn reliability
- return-path and merge reliability
- stopping-condition behavior
- validation handoff
- and run-state visibility in the kernel path

Keep the direct sanitized Codex arm as the baseline, but treat the supervisory and kernel arms as active candidates for larger-task advantage rather than as secondary curiosities.
