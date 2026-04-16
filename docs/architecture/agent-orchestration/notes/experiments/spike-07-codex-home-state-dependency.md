---
title: "SPIKE-07 Codex Home State Dependency"
description: "Differential experiment on which HOME-scoped Codex state is required for a successful headless invocation and which state only affects startup noise."
owner: ""
author: "Codex"
status: current
created: "2026-04-15"
updated: "2026-04-15"
---

# SPIKE-07 Codex Home State Dependency

## Experiment ID

`SPIKE-07`

## Question

What `HOME`-scoped Codex state is actually required for a successful scripted headless invocation, and which state only changes startup noise?

## Setup

Constant conditions:

- executable: `/opt/homebrew/bin/codex`
- working directory: repo root
- command shape: `codex exec --json --ephemeral -p collab "<ACK prompt>"`
- same prompt, same cwd, same binary, same non-interactive launch path

Two differential matrices were run under `tmp/spike-07-home-state/`.

Matrix 1 varied broad `HOME/.codex` content:

- real home
- empty home
- auth only
- auth plus copied plugins
- auth plus copied state bundle

Matrix 2 narrowed the minimum successful home:

- config only
- auth plus config
- auth plus config plus installation id
- auth plus config plus copied plugins

Primary artifacts:

- `tmp/spike-07-home-state/20260415T203903/`
- `tmp/spike-07-home-state/20260415T203943/`

## Result

For the current scripted invocation shape, the minimum successful Codex home is:

- `auth.json`
- `config.toml`

Everything else tested was optional for basic success.

Main findings:

- `empty` home failed immediately with `config profile 'collab' not found`
- `auth only` failed the same way
- `auth + plugins` also failed the same way
- `config only` reached the API but failed with repeated `401 Unauthorized`
- `auth + config` succeeded and returned the expected ACK
- adding `installation_id` did not materially change the outcome
- adding copied plugin cache increased stderr noise materially

The practical conclusion is:

- `config.toml` is required for the `-p collab` invocation shape
- `auth.json` is required for authenticated API access
- copied sqlite state, logs, and installation metadata are not required for simple success
- copied plugin cache is not required and makes stderr worse

## Observed Noise Sources

The remaining startup noise in the minimum successful home did not come from missing copied state. Codex generated new home-local state on its own during startup.

Even with only `auth.json + config.toml`, Codex created:

- `.codex/.tmp/plugins/`
- `.codex/.tmp/plugins.sha`
- `.codex/.tmp/app-server-remote-plugin-sync-v1`
- `.codex/plugins/cache/openai-curated`
- `.codex/cache/codex_apps_tools/...`
- `.codex/installation_id`
- `.codex/models_cache.json`
- `.codex/shell_snapshots/`
- `.codex/tmp/arg0/...`
- `.codex/skills/.system/...`

That minimum-success run still emitted:

- repeated plugin manifest warnings for `build-ios-apps`
- one shell snapshot deletion warning
- one plugin-manager warning about remote plugins missing from the local marketplace

This means the current stderr noise is largely Codex startup behavior, not a sign that the scripted shell is missing broad prior state.

## Useful Artifacts

Broad matrix summary:

- `tmp/spike-07-home-state/20260415T203903/baseline_real_home.meta.txt`
- `tmp/spike-07-home-state/20260415T203903/empty.meta.txt`
- `tmp/spike-07-home-state/20260415T203903/auth.meta.txt`
- `tmp/spike-07-home-state/20260415T203903/auth_plugins.meta.txt`
- `tmp/spike-07-home-state/20260415T203903/auth_state.meta.txt`

Minimum-state matrix summary:

- `tmp/spike-07-home-state/20260415T203943/config_only.meta.txt`
- `tmp/spike-07-home-state/20260415T203943/auth_config.meta.txt`
- `tmp/spike-07-home-state/20260415T203943/auth_config_install.meta.txt`
- `tmp/spike-07-home-state/20260415T203943/auth_config_plugins.meta.txt`

Most useful stderr examples:

- `tmp/spike-07-home-state/20260415T203903/empty.stderr.log`
- `tmp/spike-07-home-state/20260415T203943/config_only.stderr.log`
- `tmp/spike-07-home-state/20260415T203943/auth_config.stderr.log`

## Next Action

For controlled scripted Codex runs, treat the minimum operator-managed home state as:

- `auth.json`
- `config.toml`

Do not copy plugin cache or sqlite state by default.

If lower stderr noise matters, the next experiment should target Codex startup/plugin behavior directly:

- compare minimal authenticated home with plugin sync enabled versus disabled if a supported flag or config exists
- compare noninteractive `exec` under minimal home with and without plugin-related home directories pre-created
- isolate whether the shell snapshot warning is avoidable or merely harmless
