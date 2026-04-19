---
title: "tnh-gen Robustness Review — April 2026"
description: "Architectural analysis of issues #25, #47–#55 — identifying structural improvement opportunities beyond individual patches"
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Sonnet 4.6"
status: review
created: "2026-04-16"
auto_generated: false
---

# tnh-gen Robustness Review — April 2026

**Context**: A cluster of issues (#47–#55, plus earlier #25) was filed after a 2026-04-16 orchestration session in which `tnh-gen` was used as a delegated worker component. Issue #54 is the tracker. This document analyzes the issues collectively to identify architectural improvement opportunities — the goal is not patchwork but sound structural design.

---

## Issue Inventory

| Issue | Title | Type |
|-------|-------|------|
| #25 | Frontmatter preservation gap in tnh-gen output | Architecture / bug |
| #47 | gpt-5 can return empty text with nonzero completion tokens | Adapter correctness |
| #48 | Empty generation results reported as success; provenance-only files written | Contract / pipeline |
| #49 | Bundled prompt validation warnings flood normal CLI output | UX / catalog loading |
| #50 | OpenAI model registry and pricing metadata are stale | Operational / data |
| #51 | Root-level config/api flags easy to misuse during run debugging | Ergonomics / CLI design |
| #52 | Provider/adapter diagnostics too thin to debug empty-result failures | Observability |
| #53 | Ad hoc delegated use needs a clean per-run prompt catalog override | Ergonomics / orchestration |
| #54 | Robustness tracker for orchestration-session failures | Meta / tracker |
| #55 | Control surface should be more agent-ergonomic for delegated/scripted use | Ergonomics / synthesis |

---

## Architectural Analysis

The issues cluster into five structural themes. Each theme spans multiple issues — addressing only one issue in isolation would leave the underlying gap intact.

### Theme 1: No Typed Domain Failure Contract (Issues #47, #48, #52)

**Current state**: `ProviderStatus` already includes `FAILED` at the transport layer, but the rest of the pipeline behaves as if it does not exist. The safety gate's `post_check()` is documented as a stub; it appends an `"empty-result"` warning but does not change envelope shape. `_build_success_payload()` in `run.py` always emits `"status": "succeeded"`. `openai_adapter.py` extracts `choices[0].message.content or ""` with no detection path for content-absent-with-tokens.

**Structural gap**: A completed API call that returns empty text with nonzero `completion_tokens` is not represented as a typed failure in the domain layer. Transport state, warning strings, and CLI payload assembly disagree about what happened.

**Structural improvement needed**: Keep `ProviderStatus.FAILED` at the transport seam, but add a typed domain failure envelope: `CompletionEnvelope(outcome, result, failure, provenance, ...)`. A structured `failure_reason` should be set on `ProviderResponse`, mapped into a typed `CompletionFailure`, and carried all the way to CLI/API output. The safety gate should stop treating this as a soft warning, and `run.py` should branch on typed envelope outcome rather than always constructing a success payload.

Files touched: `gen_ai_service/providers/openai_adapter.py`, `gen_ai_service/models/transport.py`, `gen_ai_service/models/domain.py`, `gen_ai_service/mappers/completion_mapper.py`, `gen_ai_service/safety/safety_gate.py`, `cli_tools/tnh_gen/commands/run.py`.

This single change closes #47 and #48 and substantially reduces the diagnostic gap in #52.

---

### Theme 2: Adapter Diagnostics Are Opaque (Issue #52)

**Current state**: The provenance record captures trace_id, model, prompt fingerprint, token counts, finish_reason, and estimated cost. It does not capture: raw response shape, content-part type extracted, the extraction path taken within the adapter, or any classification of why text was empty.

**Structural gap**: When the adapter produces an unexpected result (new model, structural change in response format), there is no way to distinguish "content was in the wrong field" from "model genuinely returned nothing" from "adapter logic branched incorrectly." Debugging requires manually replaying the API call.

**Structural improvement needed**: A bounded `AdapterDiagnostics` record attached to `ProviderResponse` (optional, populated when `status != OK`). Fields: `content_source` (which response field was used), `content_part_count` (if the response has parts), `raw_finish_reason` (string before mapping), `extraction_notes` (free-form for adapter-specific observations). This record should be included in provenance output when `--api` mode is active.

Files touched: `gen_ai_service/providers/openai_adapter.py`, `gen_ai_service/models.py`, `cli_tools/tnh_gen/output/provenance.py`.

---

### Theme 3: CLI Control Surface Fragmentation (Issues #51, #53, #55)

**Current state**: Session-level controls (`--config`, `--api`, `--format`, `--quiet`, `--no-color`) are in the Typer root callback. Execution controls are on `run`. The result is that natural invocations like `tnh-gen run --config path/to/cfg.json` fail with "No such option." The `--prompt-dir` flag was accepted in an ADR-TG01 addendum (2026-01-02) but is not implemented. Budget gate failures give no guidance on how to raise the limit. There is no documented "agent-safe" invocation profile.

**Structural gap**: The CLI was designed for human-first interactive use. As `tnh-gen` is used as a delegated component in orchestration pipelines, the flag-placement convention becomes a friction point. Orchestrators cannot self-correct from a misplaced flag — they fail silently or noisily.

**Structural improvements needed**:

1. **Implement `--prompt-dir`** (already accepted in ADR-TG01 addendum): add to `cli_callback()` in `tnh_gen.py` and thread through `config_loader.py` as a highest-precedence override. This closes #53.

2. **Forwarded flag aliases on `run`**: Accept `--config`, `--api`, and `--prompt-dir` on the `run` subcommand, forwarding them to the root context initialization path. This does not change the underlying session model — it only removes the user-facing cliff. Alternatively, intercept misplaced-flag errors and emit a corrected invocation hint.

3. **Budget gate UX**: When `SafetyBlocked` fires due to budget, emit the budget value, the estimated cost, and the flag or config key needed to raise the limit.

4. **Agent invocation profile**: Document a minimal, reliable `tnh-gen` invocation pattern for scripted/orchestration use — flag order, expected stdout/stderr contract, exit codes. This belongs in the CLI user guide, but the design decision about what the contract is belongs in an ADR addendum.

Files touched: `cli_tools/tnh_gen/tnh_gen.py`, `cli_tools/tnh_gen/config_loader.py`, `cli_tools/tnh_gen/commands/run.py`, ADR-TG01 (addendum).

---

### Theme 4: Catalog Warning Architecture (Issue #49)

**Current state**: `PromptsAdapter` validates prompts during catalog access/loading, not just at process startup, and prompt warnings are logged individually as each prompt is loaded. In default CLI execution those logs typically surface on stderr. There is no batching, no suppression option, no distinction between "prompt is broken and unusable" and "prompt uses an older schema that still executes," and no quiet path even when `--quiet` is passed.

**Structural gap**: For a catalog with many bundled prompts, the warning volume overwhelms stderr even for an unrelated operation like `tnh-gen list --keys-only`. The warnings look identical to runtime errors. Agents and CI pipelines cannot distinguish environmental noise from actual failures.

**Structural improvement needed**: Separate catalog validation health from per-invocation stderr output.

1. **Lazy or post-load aggregation**: Collect validation issues into a structured `CatalogHealth` report during loading, not inline stderr writes.
2. **Surface via `config show`**: Make catalog health queryable: `tnh-gen config show --catalog-health` emits the aggregated report as JSON.
3. **Severity tiers**: Distinguish `ERROR` (prompt is unusable) from `WARNING` (prompt has non-critical metadata issues). Only `ERROR`-level catalog problems should surface in normal stderr.
4. **Respect `--quiet`**: In quiet mode, suppress all catalog health output.

Files touched: `gen_ai_service/pattern_catalog/adapters/prompts_adapter.py`, `prompt_system/adapters/*_catalog_adapter.py`, `prompt_system/service/loader.py`, `cli_tools/tnh_gen/tnh_gen.py`, `cli_tools/tnh_gen/commands/config.py`.

---

### Theme 5: Frontmatter Blindness in the Run Pipeline (Issue #25)

**Current state**: `_read_input_text()` is `path.read_text()` — it passes raw file content including any YAML frontmatter to the model. `write_output_file()` prepends a fresh provenance-only frontmatter block unconditionally. Any original YAML frontmatter in the input (ADR metadata, article metadata, etc.) is destroyed and the model may generate unintended content based on it.

**Structural gap**: The run pipeline has no concept of frontmatter-bearing input files. A `Frontmatter` class already exists at `src/tnh_scholar/metadata/metadata.py` and is used by `text_object`, `prompt_system`, and `srt_translate` — but it is not wired into `tnh-gen`.

**Structural improvement needed**: A new pipeline step between input read and AI execution:

1. `_read_input_text()` calls `Frontmatter.extract()` → returns `(clean_body, original_metadata)`.
2. `clean_body` is passed to the AI.
3. `write_output_file()` receives `original_metadata` and merges it with the generated provenance block using `Frontmatter.embed()` (or equivalent), preferring original metadata keys for non-provenance fields and appending/overwriting provenance-specific keys.

This is a contained change to `commands/run.py` and `output/provenance.py` with no changes to the AI execution path.

Files touched: `cli_tools/tnh_gen/commands/run.py`, `cli_tools/tnh_gen/output/provenance.py`.

---

## Simple Corrections (Non-Architectural)

The following are data or configuration corrections that can be applied independently:

- **Registry data (#50)**: Add `gpt-5.4` to `src/tnh_scholar/runtime_assets/registries/providers/openai.jsonc`; update `last_updated` to current date. Separately, evaluate whether registry staleness warnings belong at `WARNING` log level rather than stderr by default, since they are environmental noise for users who are not managing the registry.

- **gpt-5 adapter extraction path (#47, partial)**: Even before the full typed failure-envelope contract is built, `from_openai_response()` can be hardened to detect `text == ""` with `completion_tokens > 0` and return a `FAILED` transport response with a descriptive `failure_reason`. This is a one-function change that improves observability immediately and aligns with the existing transport enum.

---

## Proposed Improvement Sequence

The themes have dependencies. A reasonable execution order:

| Priority | Theme | Issues Closed | Prerequisite |
|----------|-------|---------------|--------------|
| 1 | Adapter hardening (partial #47 fix) | #47 (partial) | None — contained to one function |
| 2 | Typed failure envelope + outcome mapping | #47, #48, #52 | Adapter hardening provides the signal |
| 3 | Implement `--prompt-dir` (accepted ADR) | #53 | None — already designed |
| 4 | Forwarded run aliases + budget UX | #51, #55 (partial) | None |
| 5 | Catalog warning aggregation | #49 | None |
| 6 | Frontmatter pipeline step | #25 | None |
| 7 | Adapter diagnostics record | #52 (full) | FAILED contract (Priority 2) |
| 8 | Agent invocation profile doc | #55 (full) | Priorities 3–4 completed |

Priorities 1–4 can all proceed in parallel; they touch different files. Priorities 5–6 are independent of the others. Priority 7 builds on the contract work from Priority 2.

---

## ADR Coverage

The following themes are new enough to warrant new ADR entries or addendums:

| Theme | Recommendation |
|-------|---------------|
| Typed failure envelope + adapter diagnostics | New ADR (TG03 or GenAI Service ADR addendum) |
| `--prompt-dir` implementation | ADR-TG01 addendum update (already accepted; mark implemented) |
| Forwarded run aliases | ADR-TG01 addendum (design decision: accept or reject the forwarding pattern) |
| Catalog warning aggregation | ADR-TG02 addendum (prompt integration behavior) |
| Frontmatter pipeline step | ADR-TG01 addendum (run pipeline extension) |

Registry staleness management does not require an ADR; it is an operational data maintenance concern.

---

## References

- [ADR-TG01: CLI Architecture](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md)
- [ADR-TG01.1: Human-Friendly Defaults](/architecture/tnh-gen/adr/adr-tg01.1-human-friendly-defaults.md)
- [ADR-TG02: Prompt System Integration](/architecture/tnh-gen/adr/adr-tg02-prompt-integration.md)
- GitHub issue tracker: #25, #47–#55 (tracker: #54)

---

*Prepared: 2026-04-16*
