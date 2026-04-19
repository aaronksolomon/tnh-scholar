---
title: "tnh-gen Implementation Plan — April 2026"
description: "Brief phased implementation plan for the tnh-gen robustness and contract work identified in the April 2026 review."
owner: "aaronksolomon"
author: "Aaron Solomon, OpenAI Codex"
status: proposed
created: "2026-04-16"
auto_generated: false
---

# tnh-gen Implementation Plan — April 2026

Brief execution plan for the `tnh-gen` robustness work identified in the April 16, 2026 review and refined by the related ADR updates.

This plan is intentionally short. It is for sequencing and execution control, not for restating the ADRs.

---

## Goals

1. Make completion success/failure semantics reliable for human and agent callers.
2. Preserve input document frontmatter through the `run` pipeline.
3. Reduce CLI friction for delegated/scripted use.
4. Separate catalog-health noise from invocation failures.

---

## Scope

In scope:

- Typed completion outcome envelope and adapter diagnostics
- `tnh-gen run` success/failure/output behavior
- `--prompt-dir` and forwarded run aliases
- Budget-block UX improvements
- Frontmatter-aware read/write pipeline
- Catalog health aggregation and suppression behavior

Out of scope for this slice:

- Broad prompt-system redesign beyond catalog health surfacing
- Anthropic/provider-parity work outside the OpenAI path
- Registry-data maintenance except where needed for local verification

---

## Phase Sequence

### Phase 1: Typed Completion Outcome

Objective: establish the canonical domain contract before changing CLI behavior.

Primary files:

- `src/tnh_scholar/gen_ai_service/models/transport.py`
- `src/tnh_scholar/gen_ai_service/models/domain.py`
- `src/tnh_scholar/gen_ai_service/mappers/completion_mapper.py`
- `src/tnh_scholar/gen_ai_service/providers/openai_adapter.py`
- `src/tnh_scholar/gen_ai_service/safety/safety_gate.py`

Deliverables:

- `failure_reason` and `adapter_diagnostics` on `ProviderResponse`
- `CompletionEnvelope(outcome, result, failure, provenance, warnings, policy_applied)`
- OpenAI adapter hardening for empty-content-with-tokens and unsupported response shapes
- Mapper logic that preserves failure as typed domain state instead of warning-only degradation

Verification:

- Unit tests for transport-to-domain mapping
- Adapter tests for empty-content and malformed-shape cases
- No CLI behavior changes yet beyond preserving typed outcome

### Phase 2: Run Command Contract

Objective: make `tnh-gen run` honor the typed outcome envelope.

Primary files:

- `src/tnh_scholar/cli_tools/tnh_gen/commands/run.py`
- `src/tnh_scholar/cli_tools/tnh_gen/types.py`
- `src/tnh_scholar/cli_tools/tnh_gen/errors.py`
- `src/tnh_scholar/cli_tools/tnh_gen/output/provenance.py`

Deliverables:

- Success path only for `outcome == succeeded`
- Explicit API payloads for `succeeded`, `incomplete`, and `failed`
- No output-file writes on failed completion outcomes
- Agent-safe stdout/stderr behavior in `--api` mode

Verification:

- CLI tests for exit codes and payloads
- Regression check: failed provider completion must exit non-zero
- Regression check: no provenance-only success file on failure

### Phase 3: CLI Ergonomics

Objective: remove known invocation cliffs for delegated callers.

Primary files:

- `src/tnh_scholar/cli_tools/tnh_gen/tnh_gen.py`
- `src/tnh_scholar/cli_tools/tnh_gen/commands/run.py`
- `src/tnh_scholar/cli_tools/tnh_gen/config_loader.py`

Deliverables:

- Global `--prompt-dir`
- Forwarded `run` aliases for `--config`, `--api`, and `--prompt-dir`
- Actionable budget-block diagnostics using `max_dollars`

Verification:

- CLI parsing tests for canonical and forwarded forms
- Budget-block API payload test
- Help-text/examples updated to canonical agent-safe form

### Phase 4: Frontmatter Preservation

Objective: preserve existing document metadata while keeping provenance authoritative.

Primary files:

- `src/tnh_scholar/cli_tools/tnh_gen/commands/run.py`
- `src/tnh_scholar/cli_tools/tnh_gen/output/provenance.py`
- `src/tnh_scholar/metadata/metadata.py` only if helper gaps appear

Deliverables:

- Input parsing through `Frontmatter.extract()`
- Body-only prompt injection
- Output merge using typed metadata plus provenance keys

Verification:

- Golden tests for input-with-frontmatter and input-without-frontmatter
- Regression check that original non-provenance keys survive round-trip

### Phase 5: Catalog Health

Objective: move prompt-catalog issues out of ambient invocation stderr.

Primary files:

- `src/tnh_scholar/gen_ai_service/pattern_catalog/adapters/prompts_adapter.py`
- `src/tnh_scholar/prompt_system/adapters/filesystem_catalog_adapter.py`
- `src/tnh_scholar/prompt_system/adapters/git_catalog_adapter.py`
- `src/tnh_scholar/prompt_system/service/loader.py`
- `src/tnh_scholar/cli_tools/tnh_gen/commands/config.py`

Deliverables:

- Aggregated `CatalogHealth`
- Severity split between fatal and non-fatal prompt issues
- `config show --catalog-health`
- `--quiet` and `--api` behavior aligned with ADR-TG02 addendum

Verification:

- Catalog-load tests with mixed valid/invalid prompts
- CLI tests confirming warning suppression and explicit health reporting

---

## Recommended Delivery Order

1. Phase 1
2. Phase 2
3. Phase 3 and Phase 4 in parallel
4. Phase 5
5. Docs and final command-reference cleanup

Rationale:

- The typed outcome envelope is the dependency for reliable CLI behavior.
- Frontmatter work is independent of the completion contract once the `run` command structure is stable.
- Catalog health is isolated and should not block the core success/failure repair.

---

## Validation Gates

Per implementation PR or slice:

- Run changed-file tests first
- Run `make docs-build` for any docs updates
- Run `make pr-check` before PR creation
- Run `make ci-check` before final merge

Recommended focused test areas:

- `tests/gen_ai_service/`
- `tests/cli_tools/tnh_gen/`
- Prompt catalog adapter tests

---

## Risks

- The typed `CompletionEnvelope` change is a breaking contract for internal callers and helper utilities.
- CLI output tests may need broad fixture refresh once `failed` and `incomplete` become explicit payload states.
- Catalog health work can sprawl into prompt-system cleanup if not kept bounded to reporting surfaces.

---

## Done Criteria

- A provider-completed empty result is represented as a typed failure end-to-end.
- `tnh-gen --api run ...` provides a stable machine-readable contract for success, incomplete, and failed outcomes.
- Failed completions do not write success-shaped output files.
- Input frontmatter is preserved across `run`.
- Prompt catalog issues are queryable explicitly and no longer flood normal stderr.

---

## References

- [ADR-TG01: CLI Architecture](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md)
- [ADR-TG02: Prompt System Integration](/architecture/tnh-gen/adr/adr-tg02-prompt-integration.md)
- [ADR-TG03: Typed Completion Outcome and Adapter Diagnostics](/architecture/tnh-gen/adr/adr-tg03-completion-contract.md)
- [tnh-gen Robustness Review — April 2026](/architecture/tnh-gen/notes/tnh-gen-robustness-review-2026-04.md)
