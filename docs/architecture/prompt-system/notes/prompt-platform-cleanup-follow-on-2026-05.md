---
title: "Prompt Platform Cleanup Follow-On"
description: "Follow-on cleanup identified during tnh-gen prompt-home testing after PT05.1 default-path alignment."
owner: ""
author: "GPT-5 Codex"
status: current
created: "2026-05-05"
updated: "2026-05-05"
---

# Prompt Platform Cleanup Follow-On

This note captures prompt-platform cleanup work discovered while validating the
`tnh-gen` testing slice that moved the repo-local prompt home to `./tnh-prompts/`.

The immediate `tnh-gen` testing goal was achieved:

- repo-local default prompt discovery now resolves to `./tnh-prompts/`
- the old setup-download path is no longer normative
- the active runtime no longer depends on `PromptSystemSettings.tnh_prompt_dir`

However, the review and rerun loop exposed remaining follow-on cleanup that should
be handled as a separate prompt-platform slice rather than mixed into the current
testing work.

## Main follow-on areas

1. **Docs triage and updates**
   - Update user/developer docs that still imply the default prompt home is `./prompts`
   - Add ADR addenda where older architecture docs still describe the external prompt-repo model as normative
   - Leave clearly archived historical docs alone unless they are presented as current

2. **Experimental-surface labeling**
   - Keep the concept of a prompt catalog as the active abstraction
   - Explicitly mark git-backed/shared prompt-catalog code and docs as experimental where still present
   - Avoid presenting prompt sharing or git-backed prompt distribution as the default `tnh-gen` operating path

3. **Config / override hygiene**
   - Confirm local override behavior remains intentional: explicit env/config/CLI overrides should still win
   - Reduce operator confusion from stale examples and old env-var assumptions
   - Prefer one clear runtime path for prompt-home resolution through `GenAISettings` + `TNHContext`

## Why this is deferred

This work is adjacent to the active `tnh-gen` test slice, but not required to finish
the current journal and JSON-golden validation loop. It is better handled as a focused
cleanup pass after the testing slice is stabilized and reviewed.

## Suggested return order

1. update current-facing docs
2. add ADR addenda / historical clarifications
3. label experimental code/doc surfaces
4. trim remaining prompt-sharing/generic legacy drift where safe
