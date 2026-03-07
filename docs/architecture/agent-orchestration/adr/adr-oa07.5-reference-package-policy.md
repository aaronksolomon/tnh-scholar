---
title: "ADR-OA07.5: Reference Package Policy"
description: "Defines how prototype and deprecated agent-orchestration packages are labeled, imported, documented, and eventually retired while the maintained MVP runtime is being built."
type: "design-detail"
owner: "aaronksolomon"
author: "Aaron Solomon, GPT-5 Codex"
status: accepted
created: "2026-03-06"
parent_adr: "adr-oa07-mvp-runtime-architecture-strategy.md"
related_adrs:
  - "adr-oa03.2-codex-runner.md"
  - "adr-oa03.3-codex-cli-runner.md"
  - "adr-oa04.2-mvp-hardening-compliance-plan.md"
  - "adr-oa07-mvp-runtime-architecture-strategy.md"
---

# ADR-OA07.5: Reference Package Policy

Defines how prototype and deprecated agent-orchestration packages are labeled, imported, documented, and eventually retired while the maintained MVP runtime is being built.

- **Status**: Accepted
- **Type**: Design Detail
- **Date**: 2026-03-06
- **Owner**: Aaron Solomon
- **Author**: Aaron Solomon, GPT-5 Codex
- **Parent ADR**: [ADR-OA07](/architecture/agent-orchestration/adr/adr-oa07-mvp-runtime-architecture-strategy.md)
- **Related ADRs**:
  - [ADR-OA03.2](/architecture/agent-orchestration/adr/adr-oa03.2-codex-runner.md)
  - [ADR-OA03.3](/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-runner.md)
  - [ADR-OA04.2](/architecture/agent-orchestration/adr/adr-oa04.2-mvp-hardening-compliance-plan.md)
  - [ADR-OA07](/architecture/agent-orchestration/adr/adr-oa07-mvp-runtime-architecture-strategy.md)

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

ADR-OA07 establishes that the maintained MVP runtime will be built beside prototype-era code rather than by mutating that prototype code in place. Two current package families already fall into reference territory:

- `spike/`
- `codex_harness/`

These packages still have value:

- `spike/` preserves the Phase 0 / runner exploration record
- `codex_harness/` preserves the superseded API-first Codex path and its artifact shapes

But without a clear policy they create confusion:

- maintainers may keep adding forward-path code to the wrong package
- imports may quietly couple maintained subsystems back to prototype code
- docs may refer to reference packages as if they were current architecture
- later cleanup becomes harder because nothing marks what is truly retained versus merely forgotten

This ADR defines the policy for reference packages during the OA07 migration.

Expected end-state:

- reference packages are retained while the OA07 ADR series is being implemented and the maintained runtime is still stabilizing
- once the maintained replacements are implemented and the historical comparison value is no longer operationally necessary, these reference packages should be deleted entirely rather than kept indefinitely
- when that happens, ADRs that referenced the retained packages should receive addendums or status updates as appropriate so the architectural record stays honest

### Reference Package Definition

For agent-orchestration MVP, a reference package is:

> code retained for historical, comparative, or migration-reference value, but not part of the maintained forward implementation path.

Reference packages are not:

- the place for new feature work
- the place for new architectural decisions
- hidden dependencies of maintained subsystems
- temporary migration-source packages such as `conductor_mvp/`, which should be deleted after maintained replacements exist rather than moved under `reference/`

### Implementation Guidance

Reference policy should be strict enough to prevent architectural drift, but light enough to avoid pointless churn while the maintained MVP is still being built.

Guidance for implementers:

- preserve useful historical artifacts
- stop forward-path growth in reference code
- make reference status explicit in code and docs
- allow narrow compatibility or inspection imports only where truly necessary during migration

Goal:

> retain history without letting history define the maintained architecture

---

## Decision

### 1. Reference packages live under `agent_orchestration/reference/`

Prototype and deprecated packages retained during migration should live under:

- `agent_orchestration/reference/spike/`
- `agent_orchestration/reference/codex_harness/`

This makes their status explicit in the code layout and prevents them from appearing as peer maintained subsystems.

### 2. Reference packages must be clearly labeled in code

Each reference package should expose an explicit module-level docstring stating:

- why the package is retained
- which ADR superseded or replaced it
- that it is not the maintained forward path

At minimum:

- `reference/spike/` should be labeled as historical prototype/reference code
- `reference/codex_harness/` should be labeled as deprecated/reference because OA03.2 was superseded by OA03.3

Example module docstring format:

```python
"""Reference package: spike/

Retained for: Phase 0 runner exploration record, CLI runner comparison
Superseded by: OA07.2 (runners/), OA07.3 (validation/)
Status: NOT the maintained forward path. No new implementation work here.
"""
```

### 3. No new forward-path implementation work lands in reference packages

Once a maintained replacement subsystem exists or is designated, new implementation work must land there rather than in reference code.

Examples:

- new runner work belongs in `runners/`, not `reference/spike/`
- new validation work belongs in `validation/`, not prototype providers
- new maintained artifact or workspace logic belongs in their maintained subsystem packages

Reference packages may still receive:

- labeling updates
- import-path migration support during transition
- narrow bug fixes only if required to preserve a still-used reference workflow during migration

Physical move rule:

- move packages under `reference/` only when a maintained replacement exists, or when imports/docs are updated in the same change so no ambiguous half-migrated state is left behind

### 4. Maintained subsystems must not depend on reference packages

Maintained packages such as:

- `kernel/`
- `runners/`
- `validation/`
- `workspace/`
- `run_artifacts/`
- `execution/`

must not import from `reference/`.

If a maintained subsystem still needs logic from a reference package, that is a migration signal:

- extract the needed logic into a maintained subsystem, or
- duplicate intentionally and then retire the reference dependency

Reference-to-maintained imports may exist temporarily for comparison or migration helpers, but maintained-to-reference imports are not allowed.

### 5. Documentation must distinguish current architecture from reference code

Docs should name reference packages as:

- historical
- prototype
- deprecated
- superseded

as appropriate.

Docs must not present reference packages as the current recommended architecture once a maintained subsystem ADR exists.

This applies especially to:

- subsystem overviews
- package docstrings
- CLI references
- migration notes

### 6. Reference packages may preserve artifact examples and comparison value

Reference packages may continue to serve as:

- examples of earlier artifact layouts
- examples of earlier control loops
- comparison points during migration

That is a legitimate reason to retain them temporarily.

However, preserved examples do not justify allowing them to remain implicit dependencies of maintained code.

### 7. Retirement happens by explicit condition, not by age alone

Reference packages should be removed or archived only when:

- a maintained replacement exists
- the maintained replacement is documented
- important comparison or artifact examples are no longer needed, or have been preserved elsewhere
- import dependencies from maintained code have been eliminated

This avoids both premature deletion and indefinite zombie retention.

The intended direction after OA07 implementation is complete is full removal, not permanent retention.

### 8. `codex_harness/` is reference/deprecated immediately

Because [ADR-OA03.2](/architecture/agent-orchestration/adr/adr-oa03.2-codex-runner.md) was superseded by [ADR-OA03.3](/architecture/agent-orchestration/adr/adr-oa03.3-codex-cli-runner.md), `codex_harness/` should be treated as reference/deprecated immediately during OA07 migration.

That means:

- no new forward work there
- explicit deprecated/reference labeling
- retention only for artifact and design-history value until later cleanup

### 9. `spike/` is reference, not deprecated

`spike/` remains reference code because it still captures useful discovery work and CLI runner history.

Unlike `codex_harness/`, it is not deprecated because its role is historical/prototype reference rather than a specifically superseded architecture branch.

The policy outcome is still the same for forward work:

- no new maintained implementation should land there

---

## Suggested Package Shape

```text
agent_orchestration/
  common/
  kernel/
  runners/
  validation/
  workspace/
  run_artifacts/
  execution/
  reference/
    spike/
    codex_harness/
```

Notes:

- this ADR governs status and migration discipline, not the internal design of maintained subsystems
- reference packages can remain flat or retain their prototype shape until retirement, as long as their status is explicit

---

## Consequences

### Positive

- Makes the maintained/reference boundary explicit in both code and docs.
- Prevents prototype packages from quietly remaining on the forward implementation path.
- Preserves historical and comparative value without allowing architectural drift.
- Makes eventual cleanup a deliberate step with clear retirement conditions.

### Negative

- Introduces import and package-path churn when `spike/` and `codex_harness/` move under `reference/`.
- Requires documentation cleanup so old architecture narratives stop pointing at prototype packages as current.

### Neutral

- Reference packages may still be useful for testing, comparison, and artifact inspection during migration.
- Retention during MVP build-out is acceptable as long as forward-path ownership remains clear.
