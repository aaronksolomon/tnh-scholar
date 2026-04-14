---
title: "Supervisory Team Workflow Contract"
description: "Minimal workflow contract for a shell-launched Codex supervisor coordinating a team of native subagents."
owner: ""
author: "Codex"
status: current
created: "2026-04-13"
updated: "2026-04-13"
---
# Supervisory Team Workflow Contract

Minimal contract for the first user-shell supervisory experiment.

## Purpose

Run one Codex session as a supervisor of a small native subagent team and learn how much useful coordination Codex can perform before any custom orchestration layer is added.

## Supervisor Role

The supervisor is responsible for:

- reading the task brief,
- deciding what workstreams exist,
- launching native subagents for substantive work,
- clearly orienting subagents toward distinct workstreams,
- comparing and synthesizing subagent results,
- deciding what follow-on delegation is needed,
- and returning a clear terminal result for the human operator.

## Core Constraint

The supervisor should not do substantive task work itself.

For this experiment, substantive work includes:

- writing or revising the main design content,
- performing detailed critique that could have been delegated,
- drafting implementation changes,
- and carrying out direct analysis that belongs to a subagent workstream.

The supervisor may still do lightweight coordination work itself, such as:

- reading the task brief,
- reading high-level repo instructions,
- selecting which subagents to launch,
- comparing subagent outputs,
- synthesizing a final recommendation,
- and deciding when to stop.

## Delegation Rule

All meaningful task elements should be delegated to subagents.

Examples:

- if the task is design critique, the supervisor should assign critique angles to subagents
- if the task is planning, the supervisor should assign candidate approaches or analysis passes to subagents
- if the task is implementation shaping, the supervisor should assign codebase reading and option generation to subagents
- if the task is review, the supervisor should assign file or file-set review purposes such as issues, consistency, summary, or comparative assessment

The supervisor may refine or sequence those delegations, but it should not collapse the experiment back into single-agent execution.

## Allowed Native Behaviors

The supervisor may:

- spawn one or more native subagents,
- wait for subagent results,
- send follow-up work to subagents if needed,
- ask subagents to review files or file sets for a distinct purpose,
- compare competing results,
- and stop early if the task is blocked or the results are converging poorly.

## Delegation Budget

Keep the experiment small.

Unless the task brief says otherwise, use no more than 5 subagent calls total.

The goal is to test supervisory leverage, not to maximize fan-out.

## Stop Conditions

The supervisor should stop when one of the following is true:

- the task brief has been addressed well enough for human review,
- subagent results are repetitive or low-value,
- the session is blocked on missing context or permissions,
- or the time and effort budget in the task brief has been reached.

## Required Final Output

The final response should be useful to a human reviewer.

It should include:

- a short statement of outcome,
- what subagent workstreams were used,
- the main result or recommendation,
- and any clear blockers or next steps.

## What This Experiment Is Testing

This contract is not trying to prove that Codex can solve the task well.

It is trying to prove whether a shell-launched supervisor using native subagents can:

- maintain a supervisory role,
- delegate real work instead of absorbing it,
- produce a useful synthesized result,
- and do so in a way that appears stronger than a comparable straight-line single-agent pass.
