---
title: "Codex Official Docs Reference Summary"
description: "Local reference summary of the most relevant current official Codex docs for headless communication, configuration, auth, and built-in collaboration surfaces."
owner: ""
author: "Codex"
status: current
created: "2026-04-12"
updated: "2026-04-12"
---

# Codex Official Docs Reference Summary

This note pulls together the official Codex docs most relevant to the current `OA01.4` headless communication work.

It is not a decision document. It is a local reference summary of live official surfaces as checked on 2026-04-12.

## 1. Non-Interactive Execution

Official docs say `codex exec` is the supported non-interactive surface for headless use.

The most relevant official points are:

- `codex exec` is the intended mode for non-interactive tasks.
- while `codex exec` runs, Codex streams progress to `stderr` and prints only the final agent message to `stdout`
- `--ephemeral` is the supported way to avoid persisting rollout files to disk

This is strongly aligned with what we observed locally. In practice, `stdout`/`stderr` separation is not a hack; it is consistent with the documented shape of the interface.

Sources:

- [Non-interactive mode](https://developers.openai.com/codex/noninteractive)
- [Non-interactive mode lines 578-583](https://developers.openai.com/codex/noninteractive)
- [CLI reference](https://developers.openai.com/codex/cli/reference)

## 2. Authentication

The official docs describe authentication as portable enough to support headless and remote use.

The most important official point for our experiments is that Codex documents copying `~/.codex/auth.json` to another machine or environment when interactive login is not available. The docs also caution that this file is sensitive and should be treated like a password.

This matters because it means isolated-but-authenticated experiments are at least directionally supported. We do not need to assume that ambient user-home auth is the only possible path forever.

Sources:

- [Authentication](https://developers.openai.com/codex/auth)
- [Auth cache copy guidance, lines 653-678](https://developers.openai.com/codex/auth)

## 3. Config Layering

The official docs say Codex has layered configuration, not just one ambient user state.

The main documented order is:

1. CLI flags and `--config`
2. profile values from `--profile`
3. project `.codex/config.toml` layers from project root down to cwd
4. user config at `~/.codex/config.toml`
5. system config
6. built-in defaults

This is directly relevant to our work because it means we should keep auth questions separate from config questions. A repo-local `.codex/config.toml` is a documented supported surface even if auth still comes from the user home.

Sources:

- [Config basics](https://developers.openai.com/codex/config-basic)
- [Config layering, lines 562-584](https://developers.openai.com/codex/config-basic)

## 4. Repo Context and Project Discovery

The official docs indicate that Codex behavior depends on project root and repo-scoped config discovery, not only on the literal shell directory that launched the process.

That matches our local result:

- inside the repo root and a nested subdirectory, Codex reported `AGENTS.md`
- outside the repo, it reported `NONE`

So repo-boundary experiments are worth continuing. The docs support the idea that project-root discovery and project-local config materially affect behavior.

Sources:

- [Config basics](https://developers.openai.com/codex/config-basic)
- [Project config ordering, lines 576-584](https://developers.openai.com/codex/config-basic)

## 5. Useful CLI Flags for Current Work

The official CLI reference confirms a few flags that matter immediately for our experiments:

- `--ephemeral`: run without persisting session rollout files to disk
- `--skip-git-repo-check`: allow running outside a Git repository
- `--json`: emit machine-readable JSON

These are important because they let us:

- keep runs lightweight,
- create outside-repo boundary tests,
- and machine-parse results cleanly.

Sources:

- [CLI reference](https://developers.openai.com/codex/cli/reference)
- [CLI reference on `--ephemeral`, lines 1609-1617](https://developers.openai.com/codex/cli/reference)
- [CLI reference on `--skip-git-repo-check`, lines 1557-1560](https://developers.openai.com/codex/cli/reference)
- [CLI reference on `--json`, lines 1411-1419](https://developers.openai.com/codex/cli/reference)

## 6. Built-In Collaboration Surface: Subagents

The official docs explicitly say Codex supports subagent workflows.

The key official points are:

- current Codex releases enable subagent workflows by default
- Codex only spawns subagents when explicitly asked
- subagent workflows consume more tokens than single-agent runs
- subagents can run specialized agents in parallel and combine their results

This is highly relevant to our direction. It means we should not assume we need to build our own multi-agent substrate before understanding the built-in one.

At the same time, the docs frame this as a tradeoff surface, not free leverage. Token cost and coordination overhead are part of the product design.

Sources:

- [Subagents](https://developers.openai.com/codex/subagents)
- [Subagents on availability, lines 564-570](https://developers.openai.com/codex/subagents)
- [Subagents on parallel specialized agents, lines 554-562](https://developers.openai.com/codex/subagents)

## 7. Immediate Implications for Our Work

The official docs support a few practical conclusions:

- keep using `codex exec` as the main headless surface
- keep `stdout`/`stderr` separation as the default usage pattern
- keep `--ephemeral` in the baseline path
- treat project-root context as a real part of behavior
- treat isolated auth as a valid future experiment
- and explore built-in subagent capabilities before designing a separate multi-agent system

## 8. What This Summary Does Not Settle

These docs do not by themselves answer:

- why the local state-db migration warning is happening
- why plugin-manifest warnings are so noisy in this environment
- exactly what user-shell conditions make runs cleaner here
- or whether built-in subagents are sufficient for our intended collaboration model

Those remain experiment and design questions.
