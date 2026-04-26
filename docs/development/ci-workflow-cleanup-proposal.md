---
title: "CI Workflow Cleanup Proposal"
description: "Proposed reorganization of TNH Scholar local and GitHub CI loops for rapid prototype development and release preparation."
owner: "Engineering"
author: "Codex"
status: "proposed"
created: "2026-04-26"
updated: "2026-04-26"
---
# CI Workflow Cleanup Proposal

Proposal for simplifying TNH Scholar’s local and GitHub CI loops so fast PR validation stays fast, full verification stays explicit, and release confidence remains human-owned.

## Purpose

This proposal restructures TNH Scholar CI around the way the repo is currently operated:

- human-in-the-loop, agent-assisted development
- fast iteration on bounded branches
- multiple feature/fix branches between minor releases, sometimes skipping patch-only releases entirely during rapid prototype phases
- advisory PR checks during rapid prototyping
- explicit human pre-release verification
- future movement toward longer-running agent workflows with human post-merge verification

The main goal is to make the system simpler and more honest:

- fast checks should be truly fast
- expensive checks should run only when they add real value
- naming should match behavior
- release verification should stay stricter than PR verification
- CI should be maximally informative to highly capable human/agent engineers, not a maze of opaque rules

## Current Problems

The current setup works, but it mixes several different intentions into one path.

### 1. Always-on PR CI still installs too much

The old single-file `.github/workflows/ci.yml` installed:

```bash
poetry install -E gui -E query -E ocr --no-interaction --no-ansi --no-root
```

That happens on every PR, even though the always-on job mainly runs:

- `ruff`
- `ruff format --check`
- `mypy`
- tree drift check
- markdown lint
- README/docs sync

Those checks do not need the full optional dependency graph.

### 2. The job name implies stronger guarantees than it provides

The GitHub job is called `lint-and-type-check`, but it also does install/setup, tree drift, docs checks, and sometimes tests. The name hides the real intent.

### 3. `full-ci` policy is only partially expressed in the workflow

The repo docs now correctly say:

- PR CI is lightweight by default
- `full-ci` opt-in is for higher-risk PRs
- `make release-check` is the mandatory full local pre-release gate

The original test gating already existed in the old `ci.yml`, but it was expressed as a conditional step inside a broader job. The real problem was that the workflow still looked and behaved like a heavy full-project install path even when only lightweight checks ran.

### 4. Docs validation and docs generation are still coupled in important places

This has already been partly improved in the `Makefile`, but the principle also needed to be applied in GitHub Actions. The old `docs.yml` ran `make docs-generate` during docs verification on PRs, which was a write action inside what should have been a read/validate path.

The correct rule should be:

- validation should be read-only by default
- generation should be explicit

### 5. Current CI does not clearly model the real development loop

The actual loop is:

1. local development
2. local focused validation
3. PR with advisory checks
4. optional deeper CI
5. merge
6. post-merge validation on `main`
7. explicit release candidate verification

The current workflow technically supports this, but it does not make the model obvious.

## Design Principles

This proposal follows the repo’s existing workflow stance in [/docs/development/git-workflow.md](/development/git-workflow.md) and [/docs/development/release-workflow.md](/development/release-workflow.md).

### Principle 1: Separate signal from cost

Cheap checks should run often.

Expensive checks should run:

- when explicitly requested
- on `main`
- before release

### Principle 2: Keep PR CI advisory, but not ambiguous

During rapid prototyping, PR CI is not the final authority. It should quickly answer:

- is the diff obviously broken?
- is formatting/lint/type health drifting?
- are docs obviously inconsistent?

It should not pretend to fully certify the branch when it is not doing so.

### Principle 3: Keep full verification close to merge and release

The full trust boundary should be:

- post-merge on `main`
- pre-release on the actual release candidate state

### Principle 4: Optimize for agent-centered development

The system should work well when:

- humans and agents iterate locally
- agents open PRs with bounded changes
- humans review and merge
- longer-running agents later handle more automation while humans retain release and post-merge oversight

### Principle 5: Prefer guidance over bureaucracy

The repo is currently operated by strong human and agent engineers who can reason about risk. CI should help them make good decisions by surfacing:

- what kind of change this is
- what level of validation has run
- what validation is still advisable
- how stale the deeper verification signal is

The system should avoid intricate policy branches that create hidden behavior or make agents optimize for CI quirks instead of engineering reality.

### Principle 6: Match rapid-prototype release cadence

TNH Scholar does not currently follow a rigid patch-every-time release pattern.

Actual cadence is closer to:

- multiple features and fixes accumulate between releases
- some cycles go straight to the next minor release
- sub-minor patch releases are used when helpful, not by obligation

That means CI should optimize for:

- steady development on `main`
- periodic deep confidence checks
- explicit release-candidate verification

not for a rigid enterprise-style gate on every small PR.

## Proposed Operating Model

### Local Loop

Local validation becomes the primary fast feedback path before PR creation.

Recommended commands:

```bash
make pr-check
make ci-check
```

Recommended usage:

- `make pr-check` for diff-sized readiness and changed-file guidance
- targeted pytest for the actual slice under edit
- `make ci-check` before opening a PR when the change affects maintained runtime behavior, packaging, orchestration, or dependencies

### PR Loop

PR CI should be intentionally split into two classes.

#### A. Fast PR Validation

Runs on every PR to `main`.

Purpose:

- fast, low-cost signal
- no heavy optional dependency graph
- no full test suite

Should include:

- checkout
- Python setup
- Poetry setup
- install minimal base + dev tooling only
- `ruff check`
- `ruff format --check`
- `mypy src/`
- markdown lint
- README/docs drift or sync check
- tree drift check

Should not include:

- `gui/query/ocr` extras by default
- full pytest
- docs regeneration
- package publishing logic

Recommended job name:

- `pr-validation`

#### B. Full PR Test Job

Runs only when:

- PR has `full-ci`
- or workflow is manually dispatched

Purpose:

- deeper pre-merge confidence for risky changes

Should include:

- full install needed for maintained test targets
- pytest
- possibly dependency-heavy checks that are too expensive for every PR

Recommended job name:

- `full-test`

This should remain opt-in and situational, not a universal expectation for every PR.

### Merge / Main Loop

Pushes to `main` should run the fuller confidence path automatically.

Purpose:

- confirm merged branch health
- catch issues in changes that intentionally skipped `full-ci`
- give humans a reliable post-merge baseline

Should include:

- same fast validation as PRs
- full pytest
- code scanning / CodeQL
- docs build validation

Recommended job names:

- `main-validation`
- `main-test`

This should be the canonical GitHub-side health signal for the repository.

### Periodic Full-CI Loop

Because local validation is the primary confidence path during normal development, it is useful to have a lightweight reminder when the GitHub-side deep check has not run recently.

Recommended behavior:

- run the full GitHub test path on `main` pushes, as already proposed
- also run a scheduled full-CI pass on a time basis, for example weekly
- if the scheduled run fails, treat that as a repo health warning, not necessarily an emergency

The point is not to over-govern development. The point is to prevent the team from going too long without a recent full integrated signal.

This should be framed as:

- a periodic health check
- a freshness indicator
- a warning mechanism

not as a new mandatory gate for every feature branch.

Implementation note:

- the exact freshness surface is TBD
- it could be a lightweight workflow summary, a generated artifact, an issue/comment, or a small status report
- the proposal requires the signal, not a specific UI mechanism

### Release Loop

Release trust should remain local-first and human-owned.

Required pre-release gate:

```bash
make release-check
```

This is the final authority before tagging or publishing.

The current `Makefile` direction is correct:

- read-only docs validation by default
- warn if Markdown changed
- avoid rewriting docs artifacts during release validation

For actual release prep, if docs changed and artifacts should be refreshed:

```bash
make docs-build
make release-check
```

## Proposed GitHub Workflow Layout

### Workflow 1: `ci-pr.yml`

Trigger:

- `pull_request` to `main`

Jobs:

1. `pr-validation`
2. `full-test` gated by `full-ci`

This replaces the current overloaded `lint-and-type-check` job.

Important clarification:

- the current workflow already gates the pytest step behind `main` or `full-ci`
- the change proposed here is to formalize that into separate jobs/workflows so GitHub status semantics, install cost, and UI clarity all match the actual policy

### Workflow 2: `ci-main.yml`

Trigger:

- `push` to `main`

Jobs:

1. `main-validation`
2. `main-test`

This is the real post-merge confidence workflow.

`main-test` should be the authoritative post-merge health signal. Unlike advisory PR validation, `main` is a real trust boundary and this job should fail loudly when integrated test coverage breaks.

### Workflow 3: `ci-scheduled.yml`

Trigger:

- `schedule` weekly
- optional `workflow_dispatch`

Jobs:

1. `scheduled-full-test`
2. optional lightweight freshness/reporting job

Purpose:

- provide periodic integrated confidence
- warn when the repo has gone too long without a recent full test signal
- give humans and agents a current baseline without forcing every PR through the same expensive path

### Workflow 4: `docs-pr.yml` and `docs-publish.yml`

Keep docs-specific workflows, but narrow the roles:

- read-only PR docs validation
- docs build and publication on `main`

It should stay path-filtered.

Concrete cleanup items:

- remove write-style docs generation from PR validation paths where possible
- narrow stale branch triggers such as `develop` and `docs-reorg` if they are no longer active operating branches

Recommended structure:

- PR docs workflow path should be read-only validation only
- `main` docs workflow path can do generation/build/publication

In practice, that means splitting the old docs responsibilities into:

- a read-only PR docs validation job
- a separate deploy-capable `main` publish job

### Workflow 5: `security.yml` or existing CodeQL workflow

Keep CodeQL and dependency/security scanning separate from normal fast validation.

Security workflows answer a different question from “is this PR ready to merge?”

If CodeQL/Sourcery remain externally configured rather than implemented as repo workflows, that is acceptable in the near term. They should be treated as adjacent signals, not as part of the minimum Phase 1 migration.

## Recommended Job Contents

### `pr-validation`

Install:

```bash
poetry install --no-interaction --no-ansi --no-root
```

If the repo later moves dev dependencies into an explicit opt-in group for CI speed reasons, that can be revisited during implementation. The proposal does not depend on `--with dev` specifically; it depends on avoiding unnecessary optional extras in the always-on PR path.

Run:

- `poetry run ruff check .`
- `poetry run ruff format --check .`
- `poetry run mypy src/`
- no directory-tree generation or drift checking in routine PR/main validation
- `npx markdownlint-cli2 '**/*.md'`
- `poetry run python scripts/sync_readme.py`

Rules:

- advisory failures can stay non-blocking during rapid prototype phase
- but the job should be clearly named as validation, not certification

### `full-test`

Install only what the tests actually require.

If full repo pytest still needs optional groups, install them here, not in `pr-validation`.

Run:

- `poetry run pytest --maxfail=1 --cov=tnh_scholar --cov-report=term-missing`

Gating:

- PR label `full-ci`
- manual dispatch if needed

### `main-test`

Same test command as `full-test`, but automatic on `main`.

This preserves current repo philosophy:

- PRs are lightweight by default
- `main` receives the full GitHub-side test run

This job should fail loudly and be treated as the authoritative post-merge health signal, not as an advisory-only status.

### `scheduled-full-test`

This should be the same or nearly the same as `main-test`, but time-triggered.

Purpose:

- catch latent integration drift even during periods of low merge activity
- keep a recent deep-validation signal available to humans and agents
- support minor releases that may bundle multiple features/fixes rather than shipping every patch increment

The output should be easy to interpret. Ideally:

- success updates a visible “last healthy full-CI run” timestamp
- failure creates a warning signal in GitHub Actions and, if useful later, a small issue/comment/report artifact

## Label and Trigger Policy

### `full-ci`

Use for:

- runtime code changes
- dependency updates
- CLI behavior changes
- packaging changes
- orchestration or runner changes
- anything with unclear risk
- any PR where humans or agents judge that a fresh full integrated signal would materially reduce risk

Do not require for:

- docs-only changes
- metadata-only cleanup
- bounded editorial work

### `docs-only`

Optional future label.

Could be used later to suppress irrelevant status noise, but this is not necessary now. The simplest near-term system does not need it.

### Manual dispatch

Keep `workflow_dispatch` available for the expensive test workflow.

This is useful for:

- agent-authored PRs
- reviewers who want full confidence before merge
- follow-up reruns without relabel churn
- situations where a fresh full integrated signal is desirable before merge

## Recommended Human and Agent Expectations

### Human developer

Before PR:

- run focused local checks
- run `make ci-check` for riskier changes

Before merge:

- decide whether `full-ci` is warranted
- review advisory GitHub checks
- consider whether a fresh full integrated CI run is desirable, not just the current PR checks

Before release:

- run `make release-check`
- run `make docs-build` first if docs artifacts truly need refresh

### Agent

Expected behavior now:

- run narrow local validation for the changed slice
- avoid relying on PR CI as the only proof of correctness
- prefer fast local feedback before opening PRs
- use `full-ci` recommendation in PR notes when the change is risky
- treat CI as decision support, not as a substitute for engineering judgment

Expected behavior later:

- agents may run longer local validation bundles automatically
- agents may request or trigger deeper CI
- humans still own final release and post-merge judgment

## Proposed Local Command Roles

### Keep

- `make pr-check`
- `make ci-check`
- `make release-check`
- `make docs-build`

### Clarify

#### `make pr-check`

Purpose:

- diff budgeting
- changed-file guidance
- local PR readiness

#### `make ci-check`

Purpose:

- broad local validation before PR for risky changes

This remains broader than GitHub’s always-on PR validation.

#### `make release-check`

Purpose:

- full release-candidate gate

It should remain stricter than PR CI.

## Migration Plan

### Phase 1: Clean Split

Before `0.4.0`:

1. rename current PR job conceptually to `pr-validation`
2. stop installing `gui/query/ocr` extras in always-on PR validation
3. move pytest into a separate gated `full-test` job
4. keep `main` full test coverage automatic
5. update workflow docs to match the actual structure
6. add a simple weekly scheduled full-test workflow or warning mechanism

This is the minimum high-value cleanup.

### Phase 2: Sharpen Status Semantics

After the split is stable:

1. decide which checks should be required for merge
2. make advisory vs required status explicit in branch protection
3. consider separate names for docs validation vs code validation

### Phase 3: Agent-Centered Expansion

Later, when longer-running agent workflows are more common:

1. add manual or agent-triggerable deep validation workflows
2. add artifact capture for agent-triggered checks
3. add post-merge verification/reporting workflows for autonomous runs

## Recommended End State

The simplest clear system for the next minor release is:

### Every PR

- fast `pr-validation`
- any adjacent security/review signals that are currently enabled or externally configured

### Risky PRs or manual request

- `full-test`

### Every push to `main`

- `main-validation`
- `main-test`

### Every week

- `scheduled-full-test`
- if it fails, treat that as a visible repo-health warning and investigate on a human timescale

### Adjacent signals

- CodeQL if enabled/configured
- Sourcery review if enabled/configured

### Every release

- human runs `make release-check`
- human runs `make docs-build` first if docs changed and artifacts should be regenerated

## Why This Is the Right Shape Now

This layout matches the repo’s actual operating reality:

- fast iteration matters more than heavy PR ceremony
- releases may bundle multiple features/fixes between minors
- humans still make the merge and release decisions
- agents benefit from fast advisory feedback, not fake certainty
- `main` and release candidates remain the real trust boundaries

It is also the cleanest stepping stone to future agent-heavy workflows:

- cheap checks stay cheap
- expensive checks become explicit
- release ownership stays human
- post-merge verification can later expand without redesigning the whole system

## Concrete Next Implementation

If this proposal is accepted, the next implementation PR should do only this:

1. split the old CI workflow into fast PR validation and gated full test logic
2. stop installing optional extras in the always-on PR path
3. rename jobs so the GitHub UI reflects their true purpose
4. add a simple scheduled full-test or freshness-warning workflow
5. update [/docs/development/git-workflow.md](/development/git-workflow.md) and [/docs/development/release-workflow.md](/development/release-workflow.md) to match the final workflow names
6. split docs validation/publication so PR docs verification is read-only and branch triggers match active repo usage

That is enough to materially improve PR speed and clarity before `0.4.0`.
