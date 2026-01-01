# Agent Session Log

This file captures AI agent interactions, decisions, discoveries, and work performed on the TNH Scholar project. It provides historical context for continuity across sessions and helps human collaborators understand the evolution of the codebase.

*See AGENTLOG_TEMPLATE.md for template.*

---

## Session History (Most Recent First)

<!-- Add new sessions here following the template format -->

## 2025-12-30 19:17 PST Provenance YAML Roundtrip Test

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: provenance-yaml-roundtrip-test
**Human Collaborator**: phapman

### Context

Added a provenance YAML frontmatter parsing test to complete the TODO item for roundtrip validation.

### Key Decisions

- **Roundtrip via safe_load**: Parse the YAML header with `yaml.safe_load` and validate fields plus body content.

### Work Completed

- [x] Added YAML roundtrip test for provenance output (files: `tests/cli_tools/test_tnh_gen_coverage.py`)
- [x] Marked provenance YAML roundtrip validation as complete (files: `TODO.md`)

### Discoveries & Insights

- **Warning source**: Running pytest surfaces an `audioop` deprecation warning from `pydub` (unrelated to provenance).

### Files Modified/Created

- `tests/cli_tools/test_tnh_gen_coverage.py`: Added provenance YAML roundtrip test.
- `TODO.md`: Marked YAML roundtrip validation as complete.

### Next Steps

- [ ] None noted.

### Open Questions

- None noted.

### References

- /architecture/tnh-gen/adr/adr-tg01-cli-architecture.md

## 2025-12-30 15:27 PST tnh-gen Provenance YAML Frontmatter

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: provenance-yaml-frontmatter
**Human Collaborator**: phapman

### Context

Swapped tnh-gen output provenance from HTML comments to YAML frontmatter per ADR-TG01 addendum and aligned tests/docs.

### Key Decisions

- **YAML frontmatter header**: Emit provenance as standard YAML frontmatter with a `schema_version` field for forward compatibility.
- **Unknown prompt version**: Default `prompt_version` to "unknown" when metadata is unavailable.

### Work Completed

- [x] Updated provenance header generation to YAML frontmatter (files: `src/tnh_scholar/cli_tools/tnh_gen/output/provenance.py`)
- [x] Updated run test assertions for YAML provenance (files: `tests/cli_tools/test_tnh_gen.py`)
- [x] Updated CLI docs to reflect YAML provenance format (files: `docs/cli-reference/tnh-gen.md`)

### Discoveries & Insights

- **Doc alignment**: CLI reference still described HTML comments and needed to be updated once the code switched formats.

### Files Modified/Created

- `src/tnh_scholar/cli_tools/tnh_gen/output/provenance.py`: Emit YAML frontmatter for provenance.
- `tests/cli_tools/test_tnh_gen.py`: Assert YAML provenance markers in output files.
- `docs/cli-reference/tnh-gen.md`: Document YAML provenance format.

### Next Steps

- [ ] Validate YAML parsing roundtrip for generated files.

### Open Questions

- None noted.

### References

- /architecture/tnh-gen/adr/adr-tg01-cli-architecture.md

## 2025-12-28 22:15 PST Documentation Standards & ADR Status Lifecycle

**Agent**: Claude Sonnet 4.5 (Claude Code)
**Chat Reference**: docs-adr-status-standardization
**Human Collaborator**: phapman

### Context

Cleaned up ADR status lifecycle definitions and updated implemented ADRs that were still marked as "proposed" or "accepted". Discovered 25 historical ADRs with `status: current` from pre-markdown-standards migration.

### Key Decisions

- **ADR status lifecycle**: Formalized `proposed` → `accepted` → `implemented` → `superseded`/`archived` with optional `wip` and terminal `rejected`
- **Status separation**: ADRs use `accepted`/`implemented`, guides/docs use `current`, never mix
- **`rejected` not `discarded`**: Standardized on `rejected` for clarity (more standard terminology)
- **Historical ADRs**: Added TODO for 25 ADRs marked `current` (low priority audit needed)

### Work Completed

- [x] Updated markdown-standards.md with ADR vs guide/doc status values and lifecycle flows (files: `docs/docs-ops/markdown-standards.md`)
- [x] Updated adr-template.md with complete ADR status definitions and editing policy (files: `docs/docs-ops/adr-template.md`)
- [x] Updated 3 implemented ADRs from `proposed`/`accepted` → `implemented` (files: `docs/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md`, `docs/architecture/tnh-gen/adr/adr-tg01.1-human-friendly-defaults.md`, `docs/architecture/docs-system/adr/adr-dd03-pattern-to-prompt.md`)
- [x] Added TODO item for Historical ADR Status Audit (25 ADRs with `current` status) (files: `TODO.md`)
- [x] Verified AT03.2 and AT03.3 already correctly marked as `implemented`

### Discoveries & Insights

- **Historical context matters**: 25 ADRs marked `current` were from before markdown-standards formalization (when migrating to YAML frontmatter, default was `current` for all kept files)
- **Status semantics**: `current` = content validity (guides), `implemented` = decision execution (ADRs)
- **Agent-friendly naming**: `rejected` clearer than `discarded` for standard ADR workflows

### Files Modified/Created

- `docs/docs-ops/markdown-standards.md`: Added universal vs ADR-specific status values, lifecycle flows, and key distinctions
- `docs/docs-ops/adr-template.md`: Updated ADR status values and editing rules
- `docs/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md`: Status `proposed` → `implemented`
- `docs/architecture/tnh-gen/adr/adr-tg01.1-human-friendly-defaults.md`: Status `accepted` → `implemented`
- `docs/architecture/docs-system/adr/adr-dd03-pattern-to-prompt.md`: Status `proposed` → `implemented`
- `TODO.md`: Added "Historical ADR Status Audit" task (low priority, 25 ADRs)

### Next Steps

- [ ] Low priority: Audit 25 historical ADRs with `status: current` to determine actual status (`implemented`, `superseded`, or `rejected`)

### Open Questions

- None noted.

### References

- [Markdown Standards](/docs-ops/markdown-standards.md)
- [ADR Template](/docs-ops/adr-template.md)
- TODO.md (Historical ADR Status Audit section)

---

## 2025-12-28 21:52 PST tnh-gen Coverage to 100%

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: tnh-gen-coverage-100
**Human Collaborator**: phapman

### Context

Expanded test coverage for the `tnh-gen` CLI to reach 100% module coverage and validated with targeted and full test runs.

### Key Decisions

- **Coverage via targeted tests**: Added focused unit/CLI tests to exercise edge branches rather than introducing broad integration scaffolding.
- **Exclude TYPE_CHECKING**: Marked the `TYPE_CHECKING` import guard as non-coverable to keep coverage signal meaningful.

### Work Completed

- [x] Added comprehensive coverage tests for config/list/run/output/policy/error/factory paths (files: `tests/cli_tools/test_tnh_gen_coverage.py`)
- [x] Excluded `TYPE_CHECKING` block from coverage (files: `src/tnh_scholar/cli_tools/tnh_gen/state.py`)
- [x] Ran targeted coverage and full test suite to confirm 100% coverage (files: `tests/cli_tools/test_tnh_gen.py`, `tests/cli_tools/test_tnh_gen_coverage.py`)

### Discoveries & Insights

- **Warnings surfaced**: Full suite emits `audioop` deprecation and a legacy metadata merge deprecation warning.

### Files Modified/Created

- `tests/cli_tools/test_tnh_gen_coverage.py`: Created coverage-focused tests for tnh-gen CLI.
- `src/tnh_scholar/cli_tools/tnh_gen/state.py`: Marked `TYPE_CHECKING` guard as `no cover`.

### Next Steps

- [ ] Decide whether to address the `audioop` and legacy metadata deprecation warnings.

### Open Questions

- None noted.

### References

- `AGENTLOG_TEMPLATE.md`

---

## 2025-12-27 21:30 PST ADR-TG01.1 Review Fixes

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: adr-tg01.1-sourcery-fixes
**Human Collaborator**: phapman

### Context

Addressed Sourcery review feedback for ADR-TG01.1 CLI output changes, focusing on reducing duplicated flags/helpers and tightening format guidance/testing.

### Key Decisions

- **Global-only `--api`**: Removed subcommand-level `--api` flags to avoid precedence confusion and rely on `ctx.api`.
- **Consolidated render helpers**: Simplified config/list rendering with shared helpers and normalized payload mapping.
- **Explicit format messaging**: Clarified help text and error messages for `--api`/`--format` constraints.

### Work Completed

- [x] Removed subcommand `--api` flags and updated usage/examples to prefer global `--api` (files: `src/tnh_scholar/cli_tools/tnh_gen/commands/run.py`, `src/tnh_scholar/cli_tools/tnh_gen/commands/list.py`, `src/tnh_scholar/cli_tools/tnh_gen/commands/config.py`, `src/tnh_scholar/cli_tools/tnh_gen/commands/version.py`, `src/tnh_scholar/cli_tools/tnh_gen/tnh_gen.py`)
- [x] Simplified config/list helpers, centralized render flow, and reduced per-key duplication (files: `src/tnh_scholar/cli_tools/tnh_gen/commands/config.py`, `src/tnh_scholar/cli_tools/tnh_gen/commands/list.py`)
- [x] Updated format validation errors/help strings for clarity (files: `src/tnh_scholar/cli_tools/tnh_gen/output/policy.py`, `src/tnh_scholar/cli_tools/tnh_gen/commands/list.py`, `src/tnh_scholar/cli_tools/tnh_gen/commands/config.py`, `src/tnh_scholar/cli_tools/tnh_gen/commands/version.py`, `src/tnh_scholar/cli_tools/tnh_gen/tnh_gen.py`)
- [x] Fixed TypedDict optionality for `ConfigValuePayload` and mapping typing in config rendering (files: `src/tnh_scholar/cli_tools/tnh_gen/types.py`, `src/tnh_scholar/cli_tools/tnh_gen/commands/config.py`)
- [x] Added tests for list/table invalid format, config human/invalid formats, and version API/human output (files: `tests/cli_tools/test_tnh_gen.py`)
- [x] Fixed Ruff capitalization in style guide (files: `docs/development/style-guide.md`)

### Discoveries & Insights

- **TypedDict variance**: TypedDict payloads need `Mapping`-compatible typing to satisfy helper signatures.
- **Global flag UX**: Tests needed updates to pass `--api` before subcommands after removing local flags.

### Files Modified/Created

- `src/tnh_scholar/cli_tools/tnh_gen/types.py`: Made `trace_id` required and config fields `NotRequired` in `ConfigValuePayload`.
- `src/tnh_scholar/cli_tools/tnh_gen/commands/config.py`: Reworked render helpers, key handling, and mapping types.
- `src/tnh_scholar/cli_tools/tnh_gen/commands/list.py`: Simplified list rendering flow and normalized entry mapping.
- `src/tnh_scholar/cli_tools/tnh_gen/commands/run.py`: Removed subcommand `--api` usage and relied on global context.
- `src/tnh_scholar/cli_tools/tnh_gen/commands/version.py`: Removed subcommand `--api` flag and clarified format help.
- `src/tnh_scholar/cli_tools/tnh_gen/output/policy.py`: Clarified format validation error messages.
- `src/tnh_scholar/cli_tools/tnh_gen/tnh_gen.py`: Updated global help text and examples.
- `tests/cli_tools/test_tnh_gen.py`: Added/updated tests for API vs human output and invalid formats.
- `docs/development/style-guide.md`: Capitalized Ruff in complexity guidance.

### Next Steps

- [ ] Run CLI test suite to validate updated `--api` usage and format checks.

### Open Questions

- None noted.

### References

- `docs/architecture/tnh-gen/adr/adr-tg01.1-human-friendly-defaults.md`

---

## 2025-12-27 19:30 PST tnh-gen run Prompt Refactor

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: tnh-gen-run-refactor
**Human Collaborator**: phapman

### Context

Refactored `tnh-gen run` to reduce cyclomatic complexity and keep API-related logic behind helpers for consistency.

### Key Decisions

- **Extract output pipeline**: Moved warnings, file output, and stdout formatting into helper functions to keep `run_prompt` high-level.
- **Centralize validation**: Pulled API settings and unsupported option checks into focused helpers.

### Work Completed

- [x] Extracted warning/output handling into `_emit_run_output` and related helpers (files: `src/tnh_scholar/cli_tools/tnh_gen/commands/run.py`)
- [x] Added `_apply_api_settings` to centralize API formatting validation (files: `src/tnh_scholar/cli_tools/tnh_gen/commands/run.py`)
- [x] Added `_validate_run_options` for unsupported option checks (files: `src/tnh_scholar/cli_tools/tnh_gen/commands/run.py`)

### Discoveries & Insights

- **run_prompt abstraction drift**: Inline API output handling and validation had started to erode the command’s abstraction boundary.

### Files Modified/Created

- `src/tnh_scholar/cli_tools/tnh_gen/commands/run.py`: Extracted output pipeline, API settings, and unsupported option validation helpers.

### Next Steps

- [ ] Consider consolidating `_apply_api_settings` and `_validate_run_options` if more setup logic appears.

### Open Questions

- Should we add a small unit test to lock in `run_prompt`’s helper-based output flow?

### References

- `AGENTLOG_TEMPLATE.md`

---

## 2025-12-27 18:45 PST RenderVars Mapping Cleanup

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: tnh-gen-render-vars
**Human Collaborator**: phapman

### Context

Resolved a mypy type mismatch when passing CLI variable maps into GenAI RenderRequest by widening the accepted type.

### Key Decisions

- **Use Mapping for RenderVars**: Expanded RenderVars to `Mapping[str, Any]` to accept mutable mappings without forcing dict casts.
- **Track type duplication**: Added a TODO to consolidate RenderVars into a shared GenAI types module.

### Work Completed

- [x] Updated RenderVars alias to `Mapping[str, Any]` in GenAI domain models (files: `src/tnh_scholar/gen_ai_service/models/domain.py`)
- [x] Aligned tracking/fingerprint RenderVars alias with domain models (files: `src/tnh_scholar/gen_ai_service/infra/tracking/fingerprint.py`)
- [x] Noted follow-up to centralize RenderVars type (files: `src/tnh_scholar/gen_ai_service/models/domain.py`)

### Discoveries & Insights

- **Type alias duplication**: RenderVars is defined in both domain and tracking modules, which risks drift.

### Files Modified/Created

- `src/tnh_scholar/gen_ai_service/models/domain.py`: RenderVars now uses Mapping; added TODO for type consolidation.
- `src/tnh_scholar/gen_ai_service/infra/tracking/fingerprint.py`: RenderVars now uses Mapping.

### Next Steps

- [ ] Consider adding a `gen_ai_service/types.py` for shared aliases like RenderVars.

### Open Questions

- Should RenderVars live alongside other domain models or in a small shared types module?

### References

- `AGENTLOG_TEMPLATE.md`

---

## 2025-12-27 17:00 PST tnh-gen Typing Cleanup

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: tnh-gen-mypy-fixes
**Human Collaborator**: phapman

### Context

Addressed mypy typing errors in tnh-gen CLI command modules as part of ongoing type-check cleanup.

### Key Decisions

- **Typed config values**: Introduced a shared `ConfigValue` alias to unify config value casts and satisfy mypy.
- **Safer optional access**: Replaced direct `TypedDict` optional key access with `.get()` plus casts in human formatting.

### Work Completed

- [x] Fixed mypy `no-any-return`/optional key access issues in config rendering helpers (files: `src/tnh_scholar/cli_tools/tnh_gen/commands/config.py`)
- [x] Added `None` guard for list error format override to satisfy mypy (files: `src/tnh_scholar/cli_tools/tnh_gen/commands/list.py`)

### Discoveries & Insights

- **TypedDict optional keys**: mypy flags direct index access on optional keys even after `key in dict` checks in some contexts.

### Files Modified/Created

- `src/tnh_scholar/cli_tools/tnh_gen/commands/config.py`: Added `ConfigValue` alias, safer optional access, and explicit casts for output rendering.
- `src/tnh_scholar/cli_tools/tnh_gen/commands/list.py`: Guarded `format_override` against `None` before accessing `.value`.

### Next Steps

- [ ] Run full type check to confirm no new mypy regressions.

### Open Questions

- Should we standardize `ConfigValue` usage across other CLI modules for consistency?

### References

- `AGENTLOG_TEMPLATE.md`

---

## 2025-12-28 08:20 PST ADR-TG01.1 CLI Output Modes

**Agent**: GPT-5 (Codex CLI)
**Chat Reference**: adr-tg01.1-initial-push
**Human Collaborator**: phapman

### Context

Implemented ADR-TG01.1 human-friendly CLI defaults with `--api` contract mode and updated tnh-gen output behavior, tests, and VS Code docs.

### Key Decisions

- **Dual-mode output**: Default human-friendly output with `--api` for machine contract output.
- **Centralized format policy**: Consolidated format validation/resolution into a reusable policy module.
- **Subcommand support**: Added `--api` to subcommands to align with ADR usage expectations.

### Work Completed

- [x] Added human-friendly formatting utilities and API/human error handling (files: `src/tnh_scholar/cli_tools/tnh_gen/output/human_formatter.py`, `src/tnh_scholar/cli_tools/tnh_gen/errors.py`)
- [x] Introduced output policy helpers for format resolution/validation (files: `src/tnh_scholar/cli_tools/tnh_gen/output/policy.py`)
- [x] Updated list/run/config/version commands for mode-aware output, validation, and diagnostics (files: `src/tnh_scholar/cli_tools/tnh_gen/commands/list.py`, `src/tnh_scholar/cli_tools/tnh_gen/commands/run.py`, `src/tnh_scholar/cli_tools/tnh_gen/commands/config.py`, `src/tnh_scholar/cli_tools/tnh_gen/commands/version.py`)
- [x] Adjusted CLI context state for new flags and defaults (files: `src/tnh_scholar/cli_tools/tnh_gen/state.py`, `src/tnh_scholar/cli_tools/tnh_gen/tnh_gen.py`)
- [x] Expanded tests for human vs API output, stderr diagnostics, and invalid flag combos (files: `tests/cli_tools/test_tnh_gen.py`)
- [x] Updated VS Code ADR docs to use `--api` (files: `docs/architecture/ui-ux/vs-code-integration/adr-vsc02-tnh-gen-cli-implementation.md`, `docs/architecture/ui-ux/vs-code-integration/adr-vsc01-vscode-integration-strategy.md`)

### Discoveries & Insights

- **Subcommand flag ergonomics**: Users expect `--api` at subcommand level; global-only flags caused Typer exit code 2 failures in tests.

### Files Modified/Created

- `src/tnh_scholar/cli_tools/tnh_gen/output/human_formatter.py`: Created human-readable list/error formatter helpers.
- `src/tnh_scholar/cli_tools/tnh_gen/output/policy.py`: Created format policy resolution/validation helpers.
- `src/tnh_scholar/cli_tools/tnh_gen/output/__init__.py`: Updated module docstring to mention policy utilities.
- `src/tnh_scholar/cli_tools/tnh_gen/errors.py`: API-aware error rendering and stderr trace emission.
- `src/tnh_scholar/cli_tools/tnh_gen/state.py`: Added `api` flag and optional output format defaults.
- `src/tnh_scholar/cli_tools/tnh_gen/tnh_gen.py`: Global callback help updates and context wiring.
- `src/tnh_scholar/cli_tools/tnh_gen/commands/list.py`: Added `--api`, human formatting, API validation, diagnostics.
- `src/tnh_scholar/cli_tools/tnh_gen/commands/run.py`: Added `--api`, human vs API output, warnings to stderr.
- `src/tnh_scholar/cli_tools/tnh_gen/commands/config.py`: Added `--api`, refactored rendering helpers.
- `src/tnh_scholar/cli_tools/tnh_gen/commands/version.py`: Added `--api`, human vs API output handling.
- `src/tnh_scholar/cli_tools/tnh_gen/config_loader.py`: Added `config_files` metadata and override-only loader.
- `tests/cli_tools/test_tnh_gen.py`: Updated/added tests for new mode behavior.
- `docs/architecture/ui-ux/vs-code-integration/adr-vsc02-tnh-gen-cli-implementation.md`: Documented `--api` and stdout/stderr behavior.
- `docs/architecture/ui-ux/vs-code-integration/adr-vsc01-vscode-integration-strategy.md`: Updated CLI examples to use `--api`.

### Next Steps

- [ ] Consider additional documentation updates for `tnh-gen` CLI help/guide if needed.

### Open Questions

- Should `--api` remain both global and subcommand-local long term, or migrate fully to subcommand-local usage?

### References

- `docs/architecture/tnh-gen/adr/adr-tg01.1-human-friendly-defaults.md`
- `docs/architecture/ui-ux/vs-code-integration/adr-vsc02-tnh-gen-cli-implementation.md`

---

---

## Archive

Previous agent session logs are archived in `archive/agentlogs/`:

- [AGENTLOG-12-23-25.md](archive/agentlogs/AGENTLOG-12-23-25.md) - Post-merge hotfix, tnh-gen legacy compatibility, architecture improvements
- [AGENTLOG-12-13-25.md](archive/agentlogs/AGENTLOG-12-13-25.md) - TextObject robustness, ADR-AT03 series implementation
- [AGENTLOG-12-11-25.md](archive/agentlogs/AGENTLOG-12-11-25.md) - tnh-fab deprecation, documentation updates
- [AGENTLOG-12-10-25.md](archive/agentlogs/AGENTLOG-12-10-25.md) - GenAI service implementation, test coverage
- [AGENTLOG-12-07-25.md](archive/agentlogs/AGENTLOG-12-07-25.md) - Early project work, architecture foundations
