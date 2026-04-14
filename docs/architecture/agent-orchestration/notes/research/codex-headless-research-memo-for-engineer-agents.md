---
title: "Codex Headless Research Memo for Engineer Agents"
description: "Official-surface findings and recommended work for Codex headless and multi-agent collaboration research."
owner: ""
author: "ChatGPT"
status: draft
created: "2026-04-12"
updated: "2026-04-12"
---

# Codex Headless Research Memo for Engineer Agents

## 1. Research Findings

This memo summarizes the most relevant official Codex findings for current headless and agent-collaboration research.

### Headless / non-interactive execution is an official surface

Codex has an explicitly supported non-interactive mode via `codex exec`. This is the correct starting point for headless runs, scripting, CI, and chained CLI workflows. The docs also frame this as the right surface when sandbox and approval settings must be made explicit rather than inherited from an interactive session.

Reference links:

- Non-interactive mode: https://developers.openai.com/codex/noninteractive
- CLI command-line options: https://developers.openai.com/codex/cli/reference

### Authentication is portable enough to support isolation experiments

Codex documents standard login flows, including device auth for headless environments. The docs also describe copying `~/.codex/auth.json` from a machine that can log in interactively to one that cannot. This is important because it suggests that isolated but authenticated runs may be possible without inventing an unsupported auth path.

Reference links:

- Authentication: https://developers.openai.com/codex/auth

### Config is layered; ambient home state is not the only control surface

Codex documents layered configuration:

- system config,
- user config at `~/.codex/config.toml`,
- project config at `.codex/config.toml`,
- profiles,
- CLI flags,
- and direct `--config` overrides.

This means research should separate auth dependence from config dependence. Repo-local or project-local config is a supported surface even if some auth or session state still lives in the user home.

Reference links:

- Config basics: https://developers.openai.com/codex/config-basic
- Advanced config: https://developers.openai.com/codex/config-advanced
- Config reference: https://developers.openai.com/codex/config-reference

### Working directory and project-root discovery matter

Codex does not operate only as “whatever shell happened to launch it.” The docs describe project-root discovery, upward search behavior, config-layer loading, and `AGENTS.md` guidance resolution. This means shell-context experiments must also control for working directory, project root, and instruction-loading behavior.

Reference links:

- Advanced config: https://developers.openai.com/codex/config-advanced
- AGENTS.md: https://developers.openai.com/codex/agents

### Some local statefulness is intentional

Codex documents local transcripts, resumable sessions, and accumulated working context. Some local persistence is therefore a product feature, not just local machine noise. The research question should not be “remove all local state,” but rather “identify the minimum intentional local state required for reproducible headless collaboration.”

Reference links:

- CLI features: https://developers.openai.com/codex/cli/features
- Best practices: https://developers.openai.com/codex/learn/best-practices

### Safety controls are a separate layer from execution

Codex documents sandboxing and approval modes as first-class concepts. This supports keeping execution research separate from broader safety interpretation. Safety should be studied on top of a known execution path, not used as a substitute for understanding how Codex actually runs.

Reference links:

- Sandboxing: https://developers.openai.com/codex/concepts/sandboxing
- Agent approvals & security: https://developers.openai.com/codex/agent-approvals

### Multi-agent collaboration is directionally supported

Codex officially documents subagents. This matters because collaboration is not purely an external orchestration fantasy; it is at least partially part of the product surface. At the same time, the docs warn about coordination overhead and conflict risk, especially for parallel write-heavy work. Read-heavy or clearly partitioned collaboration appears safer as a starting point.

Reference links:

- Subagents: https://developers.openai.com/codex/subagents

### Guidance surfaces in English are already part of Codex

Codex documents `AGENTS.md`, layered guidance, and best-practice patterns for structured plans and longer-running work. That aligns well with supervisor-plus-orientation ideas. It suggests that the near-term architecture may not need a large custom planning substrate to begin testing guided collaboration.

Reference links:

- AGENTS.md: https://developers.openai.com/codex/agents
- Best practices: https://developers.openai.com/codex/learn/best-practices

### The CLI surface is active and may drift

Codex has a live changelog and active CLI evolution. That means runtime inspection, current-help checking, and capability verification before invocation are not optional niceties for automation work; they are prudent engineering.

Reference links:

- Changelog: https://developers.openai.com/codex/changelog

### Cautions

- Do not treat undocumented local behavior as a contract unless repeated tests show it is both necessary and stable enough to rely on temporarily.
- Do not collapse these questions together:
  - what Codex officially supports,
  - what the currently installed binary does locally,
  - and what behavior is actually needed for agent-collaboration experiments.
- Do not attribute every behavioral difference to shell context; project root, config layering, `AGENTS.md`, auth state, and persistence may be the real cause.
- Plugin-related local artifacts should be treated cautiously until they are clearly mapped to documented Codex surfaces such as hooks, plugins, skills, MCP, or subagents.

## 2. Recommended Work

The goal now is not to design a full orchestration platform. The goal is to reduce uncertainty around real Codex execution surfaces and then use that understanding to test collaboration patterns.

### A. Build a documented-vs-observed matrix

Create a compact comparison table with columns such as:

- topic,
- officially documented behavior,
- locally observed behavior,
- confidence level,
- impact on headless runs,
- and follow-up experiment needed.

Suggested rows:

- auth,
- config,
- working directory / project root,
- `AGENTS.md` loading,
- persistence,
- session resume,
- sandbox mode,
- approval mode,
- plugin / hook / extension artifacts,
- and subagent / nested-agent behavior.

This should become the main reference artifact for follow-on engineering work.

### B. Run controlled user-shell mimic experiments

Compare runs across a small number of controlled contexts:

- direct user shell,
- `zsh -lc`,
- repo-local wrapper script,
- alternate working directory,
- alternate `HOME` or Codex-home arrangement if supported,
- and explicit config overrides.

For each run, capture:

- exact invocation,
- working directory,
- effective config source,
- auth source,
- whether `AGENTS.md` was present and loaded,
- output cleanliness,
- failures,
- and observable behavior differences.

The purpose is to identify what actually makes a run behave “as if user,” not just what looks similar at first glance.

### C. Test authenticated isolation directly

Because Codex documents portable auth cache behavior, run direct experiments on:

- temporary or repo-local home/state setup,
- copied auth cache,
- isolated config,
- and isolated transcripts/session state.

Primary question:

Can we achieve isolated but authenticated headless runs that are stable enough for collaboration experiments?

This is probably the highest-leverage next experiment.

### D. Distinguish guidance-layer collaboration from process-layer collaboration

There are at least three different collaboration modes worth keeping separate:

1. Codex guided by repository documents such as `AGENTS.md` and plans.
2. Codex invoking Codex or otherwise delegating through shell calls or subagent-style behavior.
3. A separate supervisory layer selecting work orientations and delegating to Codex or Claude.

Do not mix these too early. Test them separately.

### E. Start with narrow collaboration, not broad autonomy

For multi-agent collaboration experiments, begin with patterns that minimize conflict:

- read-heavy critique,
- design review,
- evaluation,
- targeted implementation in partitioned areas,
- or one agent producing a plan and another reviewing or refining it.

Avoid starting with parallel write-heavy collaboration across overlapping files until the execution and state model are better understood.

### F. Use plans where they help, but do not stop there

Plans are likely useful immediately, especially for:

- execution decomposition,
- shared context,
- step tracking,
- and handoff clarity.

But plans alone are probably not the whole story if the goal is real multi-agent collaboration. They should be treated as a helpful guidance surface, not the final collaboration architecture.

A reasonable near-term stance is:

- use plans now,
- test Codex-to-Codex or Codex-to-Claude collaboration in constrained settings,
- and delay broader orchestration design until execution and isolation assumptions are clearer.

### G. Add runtime capability checking to any automation path

Any scripted Codex invocation should verify current capability before assuming flags or behavior. At minimum, automation code should be prepared to:

- inspect current help output,
- confirm the intended subcommand exists,
- confirm relevant flags still exist,
- and fail loudly with a useful diagnostic when the surface has drifted.

This should be treated as baseline hygiene, not as a later hardening step.

### H. Practical recommendation for current direction

The current best path appears to be:

1. keep research ahead of architecture,
2. use `codex exec` as the primary headless surface,
3. explore isolated-but-authenticated execution,
4. use plans and `AGENTS.md` as immediate guidance tools,
5. test narrow multi-agent collaboration patterns,
6. and only then decide how much extra orchestration machinery is actually justified.

The current evidence does not suggest abandoning multi-agent collaboration. It suggests narrowing the question and grounding it in the official Codex surface before building more system code.
