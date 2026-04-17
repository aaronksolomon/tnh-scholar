---
title: "ADR-TG03: Completion Contract and Adapter Diagnostics"
description: "Introduce a FAILED terminal state in the completion envelope and structured adapter diagnostics for observable, reliable generation results"
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Sonnet 4.6"
status: proposed
created: "2026-04-16"
related_adrs: ["adr-tg01-cli-architecture.md", "adr-tg02-prompt-integration.md"]
---

# ADR-TG03: Completion Contract and Adapter Diagnostics

Establishes a three-state completion contract (`OK` / `INCOMPLETE` / `FAILED`) and a structured adapter diagnostics record, so that empty or unextractable generation results are explicitly represented as failures at every layer — adapter, safety gate, run command, and API output — rather than silently passed as successes.

- **Filename**: `adr-tg03-completion-contract.md`
- **Status**: Proposed
- **Date**: 2026-04-16
- **Authors**: Aaron Solomon, Claude Sonnet 4.6
- **Owner**: aaronksolomon

---

## ADR Editing Policy

**Status**: `proposed` — this ADR is in the design loop and may be freely revised.

---

## Context

### Current State

The `tnh-gen` generation pipeline has a two-state completion model:

- `ProviderStatus.OK` — usable text was extracted
- `ProviderStatus.INCOMPLETE` — text was extracted but the completion was cut off (e.g., `finish_reason == "length"`)

No `FAILED` state exists. Every API call that completes without a network or HTTP error is treated as a success.

This creates a structural gap across four layers:

**Adapter layer** (`gen_ai_service/providers/openai_adapter.py`): extracts `choices[0].message.content or ""`. For models that use structured content parts (e.g., gpt-5 reasoning paths), `message.content` may be `None` even when `completion_tokens > 0` and `finish_reason == "stop"`. The adapter has no detection path for this condition and returns `ProviderStatus.OK` with `text = ""`.

**Safety gate** (`gen_ai_service/safety/safety_gate.py`): `post_check()` is documented as a stub. It appends `"empty-result"` as a warning tag on the completion envelope but does not change `status` or raise. The docstring explicitly notes this is "stubbed for now."

**Run command** (`cli_tools/tnh_gen/commands/run.py`): `_build_success_payload()` always emits `"status": "succeeded"`. `_emit_run_output()` calls `write_output_file()` unconditionally — so an empty `result_text` produces a provenance-only output file with `"status": "succeeded"` in the API payload and exit code `0`.

**Provenance records**: Capture model, tokens, finish_reason, estimated cost. Do not capture which response field was read, what content parts were present, or any classification of why text was absent. When a trace fails, the provenance record is insufficient to diagnose it.

### Problem

Orchestrators and CI pipelines that trust exit code or the `"status"` field are silently deceived when a generation produces no usable text. The failure is invisible. Additionally, as new model generations (gpt-5, gpt-5.4) depart from the `choices[0].message.content` response shape, the number of undetected empty-result failures is expected to increase.

### Scope

Issues: #47 (gpt-5 empty text), #48 (empty result reported as success), #52 (insufficient diagnostics).

Related: [ADR-TG01](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md) §5 (error handling), [ADR-TG01.1](/architecture/tnh-gen/adr/adr-tg01.1-human-friendly-defaults.md) (API payload contract).

---

## Decision

### 1. Add `ProviderStatus.FAILED`

Add a third terminal `ProviderStatus` value:

```
ProviderStatus.OK         — usable text extracted
ProviderStatus.INCOMPLETE — text extracted but completion was truncated
ProviderStatus.FAILED     — API call completed but no usable text could be extracted
```

`FAILED` is semantically distinct from `INCOMPLETE`: `INCOMPLETE` means "text exists but was cut off"; `FAILED` means "no text was produced or none could be extracted."

---

### 2. Structured `FailureReason` on `ProviderResponse`

Add a `failure_reason` field to `ProviderResponse` (populated when `status == FAILED`):

```
FailureReason.EMPTY_CONTENT_WITH_TOKENS   — content field was empty/null but tokens were consumed
FailureReason.CONTENT_FIELD_MISSING       — expected content field absent from response shape
FailureReason.UNSUPPORTED_RESPONSE_SHAPE  — response structure not recognized by adapter
FailureReason.CONTENT_EXTRACTION_ERROR    — exception during content extraction
```

`failure_reason` is `None` when `status == OK` or `INCOMPLETE`.

---

### 3. Harden Adapter Extraction in `openai_adapter.py`

The `from_openai_response()` method gains two detection branches before returning:

**Branch A — empty content with tokens**:
If `text == ""` and `completion_tokens > 0`, set `status = FAILED`, `failure_reason = EMPTY_CONTENT_WITH_TOKENS`. Do not return `OK`.

**Branch B — content field absent**:
If `choices[0].message` is present but `.content` is `None` and `completion_tokens == 0`, set `status = FAILED`, `failure_reason = CONTENT_FIELD_MISSING`.

**Branch C — unexpected response shape**:
If `choices` is empty or the response structure does not conform to the expected schema, set `status = FAILED`, `failure_reason = UNSUPPORTED_RESPONSE_SHAPE`.

These branches are checked before the current `or ""` fallback, which is removed.

---

### 4. Make `post_check()` a Real Gate

`safety_gate.py` `post_check()` is promoted from stub to enforcement:

- If `completion.status == FAILED`: raise `GenerationFailed(failure_reason=completion.failure_reason)`.
- `GenerationFailed` is a new exception in `gen_ai_service/exceptions.py`, carrying `failure_reason` and the full `CompletionEnvelope` for caller inspection.
- `post_check()` does not need to re-derive empty-text detection — it delegates to the status already set by the adapter.

---

### 5. Failure Path in `run.py`

`_emit_run_output()` catches `GenerationFailed` and:

- Emits `"status": "failed"` in the API payload.
- Includes `"failure_reason"` as a structured field (the `FailureReason` string value).
- Writes **no output file**.
- Exits non-zero (exit code `1`, consistent with existing error handling in ADR-TG01 §5).

In `--api` mode, the failure payload follows the existing error envelope schema from ADR-TG01.1, extended with `failure_reason`.

---

### 6. `AdapterDiagnostics` Record

Add an optional `adapter_diagnostics: AdapterDiagnostics | None` field to `ProviderResponse`. Populated on any non-`OK` status. Fields:

| Field | Type | Description |
|-------|------|-------------|
| `content_source` | `str` | Response field path that was read (e.g., `"choices[0].message.content"`) |
| `content_part_count` | `int \| None` | Number of parts in the content array, if parts-style response |
| `raw_finish_reason` | `str` | Raw finish_reason string before mapping to internal enum |
| `extraction_notes` | `str` | Free-form adapter notes on what was found vs. expected |

`AdapterDiagnostics` is included in provenance output when `--api` mode is active and `status != OK`. It is omitted from human-mode output to avoid verbosity.

---

### Data Flow Summary

```
openai_adapter.from_openai_response()
  → sets ProviderStatus.FAILED + FailureReason + AdapterDiagnostics
  ↓
safety_gate.post_check()
  → raises GenerationFailed if FAILED
  ↓
run._emit_run_output()
  → catches GenerationFailed
  → emits {"status": "failed", "failure_reason": "..."}
  → no file write, exit code 1
```

---

## Consequences

### Positive

- Empty results are explicitly represented as failures at every layer.
- Orchestrators get reliable exit codes and machine-readable `failure_reason` fields.
- Adapter failures caused by new model response shapes are diagnosable from provenance alone, without replaying the API call.
- `post_check()` stub is replaced by real enforcement, closing the gap noted in its own docstring.
- The two-branch distinction (`INCOMPLETE` vs. `FAILED`) is clearer than the current single-state model.

### Negative

- `GenerationFailed` is a new exception type. All callers of `GenAIService.generate()` that do not currently handle it will get an unhandled exception — this is a breaking change requiring callers to be audited and updated.
- Adding `AdapterDiagnostics` to `ProviderResponse` increases verbosity in `--api` provenance output for failed calls.
- The `FailureReason` enum is a new contract surface that must be kept stable across model updates.

---

## Alternatives Considered

### Alternative 1: Reuse `INCOMPLETE` for empty-with-tokens

**Approach**: Map empty content with tokens to `INCOMPLETE` rather than introducing `FAILED`.

**Rejected**: `INCOMPLETE` semantically means "text exists but was truncated." Empty-with-tokens is a categorically different condition — the model responded but the adapter could not extract content. Conflating them obscures the root cause in diagnostics.

### Alternative 2: Treat empty result as a retryable warning

**Approach**: On empty result, set a warning flag and allow callers to decide whether to retry or fail.

**Rejected**: The current behavior of writing provenance-only output files and emitting `"status": "succeeded"` is the direct cause of silent orchestration failures (#48). A retry-or-warn approach does not fix that — it defers the decision to callers who may not implement the check.

### Alternative 3: Detect empty results only in `post_check()`

**Approach**: Leave the adapter unchanged; detect empty text in `safety_gate.post_check()`.

**Rejected**: The adapter has the full response object and is the correct place to distinguish *why* content is absent (missing field vs. empty string vs. unexpected shape). `post_check()` sees only the extracted `CompletionEnvelope` and cannot reconstruct this information. Adapter-level detection produces richer diagnostics.

---

## Open Questions

1. **`FailureReason` extensibility**: Should `FailureReason` be a `str`-typed enum (open-ended, extensible by new adapters) or a closed `IntEnum`? Open-ended is more forward-compatible as new model families are added.

2. **Retry integration**: Should `GenerationFailed` carry a `retryable: bool` hint? Some failure reasons (e.g., `CONTENT_EXTRACTION_ERROR` due to a transient parse issue) may be retryable; others (`UNSUPPORTED_RESPONSE_SHAPE`) are not.

3. **Anthropic adapter parity**: The same hardening should eventually be applied to the Anthropic/Claude adapter. Should TG03 scope that now, or defer to a separate ADR once the OpenAI path is proven?

4. **Provenance file on FAILED**: Currently decided: no output file on `FAILED`. Should there be an option to write a provenance-only "failure record" file for audit purposes? This would make the failure visible in the filesystem without creating the impression of a successful generation.

---

## References

- [ADR-TG01: CLI Architecture](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md) — error handling, exit codes, API payload contract
- [ADR-TG01.1: Human-Friendly CLI Defaults](/architecture/tnh-gen/adr/adr-tg01.1-human-friendly-defaults.md) — `--api` flag, payload structure
- [tnh-gen Robustness Review 2026-04](/architecture/tnh-gen/notes/tnh-gen-robustness-review-2026-04.md) — issue analysis and improvement recommendations
- GitHub issues: #47, #48, #52, #54 (tracker)

---

## As-Built Notes & Addendums

*No addendums yet — ADR is in proposed state.*
