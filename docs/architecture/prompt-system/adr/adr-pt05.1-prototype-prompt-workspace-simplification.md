---
title: "ADR-PT05.1: Prototype Prompt Workspace Simplification"
description: "Defines the active prototype prompt storage model around a tracked repo-local workspace and deprecates the external shared prompt-repo path for current TNH Scholar operations."
type: "transition-strategy"
owner: "aaronksolomon"
author: "GPT-5 Codex"
status: proposed
created: "2026-05-05"
parent_adr: "adr-pt05-prompt-platform-strategy.md"
related_adrs:
  - "adr-pt04-prompt-system-refactor.md"
  - "adr-cf02-prompt-catalog-discovery.md"
---

# ADR-PT05.1: Prototype Prompt Workspace Simplification

Defines the active prototype prompt storage model around a tracked repo-local workspace and deprecates the external shared prompt-repo path for current TNH Scholar operations.

- **Status**: Proposed
- **Type**: Transition Strategy
- **Date**: 2026-05-05
- **Owner**: Aaron Solomon
- **Author**: GPT-5 Codex

---

## Context

TNH Scholar prompt architecture currently reflects two different operating models.

The first is the older prompt-platform / configuration assumption:

- prompts live outside `tnh-scholar`
- developers clone a separate prompt repository into `prompts/`
- end users obtain prompts through setup flows
- git-backed prompt catalog behavior remains available as a platform capability

The second is the actual current prototype operating model:

- walkthroughs, golden tests, and prompt/schema evaluation are run against the tracked repo-local `tnh-prompts/` workspace
- prompt iteration for `tnh-gen` is being performed inside this repository
- bundled runtime prompts in `src/tnh_scholar/runtime_assets/prompts/` are treated as the promoted stable subset, not the main prototyping surface

Recent `tnh-gen` case-study work made this mismatch concrete:

1. The maintained walkthrough and golden-validation path depends on `--prompt-dir ./tnh-prompts`.
2. No active GitHub automation was found that syncs or checks in prompt changes from an external prompt repository.
3. The runtime prompt catalog still contains code and docs shaped around the older separate-repo model.

This creates unnecessary ambiguity about:

- which prompt directory is authoritative during prototype work
- whether prompt changes are expected to arrive from GitHub automation
- whether prompt sharing/distribution is a current platform concern or deferred research

For the current prototype phase, the repo needs a simpler, explicit prompt operating model that matches actual practice and supports high-quality demos, walkthroughs, and release validation.

---

## Decision

### 1. Adopt a Simplified Prototype Prompt Home Model

For the active TNH Scholar prototype phase, prompt storage and versioning are simplified to three roles:

1. **Tracked repo-local prompt workspace**: `tnh-prompts/`
   - primary surface for prompt iteration, walkthroughs, golden tests, and release validation
   - versioned in the main `tnh-scholar` repository
   - expected to carry prompts that are under active evaluation but not yet promoted to bundled runtime assets

2. **Bundled runtime prompts**: `src/tnh_scholar/runtime_assets/prompts/`
   - minimal shipped subset for installed-package behavior
   - destination for prompts that are considered stable enough to become system-dependent defaults or packaged fallbacks

3. **User prompt workspace**: user-configured prompt directories
   - still supported as a customization surface
   - not the normative prototype validation surface

### 2. Deprecate the External Shared Prompt-Repo Model for Current Operations

The older model in which prompt authoring and versioning are centered on a separately managed shared prompt repository is deprecated for current TNH Scholar prototype operations.

This includes deprecating the following as the **normative** operating path:

- external prompt-repo cloning as the expected development workflow
- prompt update/check-in assumptions tied to GitHub-side management
- release or walkthrough reliance on untracked local prompt checkouts

This ADR does **not** prohibit future reintroduction of a shared prompt-distribution model. It only removes that model from the active prototype baseline.

### 3. Keep Shared-Prompt / Git-Managed Catalog Capacity Isolated as Experimental

Existing code paths for git-backed prompt catalogs, prompt setup/download flows, and broader prompt-sharing concepts are retained only as experimental or legacy-isolated capability unless and until a later ADR reactivates them as first-class platform behavior.

Rules for this phase:

- these paths must not be presented as the default `tnh-gen` operating model
- release validation, walkthroughs, and maintained docs should not depend on them
- future expansion toward shared prompt libraries or web-distributed prompt catalogs is treated as research scope, not current product scope

### 4. Use Promotion Rather Than Mirroring as the Main Stability Path

Prompt lifecycle for the current prototype phase is:

1. iterate in `tnh-prompts/`
2. validate through walkthroughs, goldens, and system-dependent use
3. promote stable prompts into `runtime_assets/prompts/` when they become packaged or system-critical

This replaces the notion that the main stability path is a separate external prompt repository mirrored back into the application repo.

### 5. Defer the Default Discovery Repoint as a Follow-On Implementation Decision

This ADR does **not** immediately change runtime discovery defaults in code.

Follow-on implementation must decide whether to:

- repoint default workspace discovery from `prompts/` to `tnh-prompts/`, or
- keep current discovery but require explicit `--prompt-dir ./tnh-prompts` for prototype validation paths

That decision should be made deliberately after review of packaging, installed-wheel behavior, and remaining legacy prompt-catalog surfaces.

---

## Consequences

### Positive

1. The prompt operating model matches actual current `tnh-gen` practice.
2. Walkthroughs, goldens, and release demos can rely on a tracked prompt workspace inside the main repo.
3. Prompt versioning/storage becomes simpler and easier to explain during the current prototype phase.
4. Bundled runtime assets remain a clear promotion target rather than a parallel authoring surface.
5. Future prompt-sharing work remains possible without complicating present operations.

### Negative

1. Some existing docs and configuration ADRs now need explicit clarification or addendums.
2. The codebase still contains legacy or experimental prompt-management surfaces that may confuse contributors until follow-on cleanup is completed.
3. The default prompt discovery path remains ambiguous until a later implementation decision is made.

---

## Alternatives Considered

### A. Keep the external prompt repository as the normative model

**Rejected**: This no longer matches actual walkthrough, golden-test, and prototype validation practice.

### B. Immediately repoint all runtime defaults in the same slice

**Deferred**: This may be the right direction, but it should be decided with packaging and installed-behavior review rather than folded implicitly into a docs/demo slice.

### C. Remove git-backed prompt catalog and setup/download code immediately

**Rejected**: The capability may still be useful as experimental or future research infrastructure, and immediate removal is not necessary to clarify current operations.

---

## Open Questions

1. Should `PromptPathBuilder` and `GenAISettings` repoint their workspace default from `prompts/` to `tnh-prompts/` before the next release?
2. Should `tnh-setup` deprecate external prompt download behavior in favor of repo-local and bundled prompt flows?
3. What is the explicit boundary between experimental prompt-sharing infrastructure and maintained prompt-platform behavior?
4. Which prompts should be promoted from `tnh-prompts/` into `runtime_assets/prompts/` before the next release milestone?

---

## Addendum 2026-05-05: Default Workspace Repoint Implemented

**Context**: Follow-on `tnh-gen` review work completed the implementation decision that this ADR left open.

**Decision**:

- repo-local workspace discovery now defaults to `./tnh-prompts/` rather than `./prompts/`
- the repo `prompts/` mirror is no longer treated as the active workspace inside `tnh-scholar`
- `tnh-setup` no longer downloads prompts from the old external prompt repository as part of the normative setup flow

**Implications**:

- walkthroughs and golden tests can now rely on the default repo-local prompt home
- `--prompt-dir` remains available for intentional overrides and experiments
- user prompt directories and bundled runtime prompts remain part of the three-layer discovery model
