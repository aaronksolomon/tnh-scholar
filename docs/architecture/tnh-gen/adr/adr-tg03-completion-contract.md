---
title: "ADR-TG03: Typed Completion Outcome and Adapter Diagnostics"
description: "Normalize transport failure states into a typed domain outcome envelope and structured adapter diagnostics for observable, reliable generation results"
owner: "aaronksolomon"
author: "Aaron Solomon, Claude Sonnet 4.6"
status: proposed
created: "2026-04-16"
related_adrs: ["adr-tg01-cli-architecture.md", "adr-tg02-prompt-integration.md"]
---

# ADR-TG03: Typed Completion Outcome and Adapter Diagnostics

Establishes a typed domain outcome contract for generation results and a structured adapter diagnostics record, so that empty or unextractable generation results are explicitly represented as failures at every layer — adapter, mapper, service, run command, and API output — rather than silently passed as successes.

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

The `tnh-gen` generation pipeline currently has an inconsistent status model across layers:

- `ProviderStatus.OK` — usable text was extracted
- `ProviderStatus.INCOMPLETE` — text was extracted but the completion was cut off (e.g., `finish_reason == "length"`)
- `ProviderStatus.FAILED` — already exists in transport models but is not meaningfully produced or propagated

This creates a structural gap across four layers:

**Adapter layer** (`gen_ai_service/providers/openai_adapter.py`): extracts `choices[0].message.content or ""`. For models that use structured content parts (e.g., gpt-5 reasoning paths), `message.content` may be `None` even when `completion_tokens > 0` and `finish_reason == "stop"`. The adapter has no detection path for this condition and returns `ProviderStatus.OK` with `text = ""`.

**Mapper/domain layer** (`gen_ai_service/mappers/completion_mapper.py`, `gen_ai_service/models/domain.py`): transport status is flattened into warnings on `CompletionEnvelope`. The domain envelope has `result`, `provenance`, `policy_applied`, and `warnings`, but no typed success/failure outcome or failure payload.

**Safety gate** (`gen_ai_service/safety/safety_gate.py`): `post_check()` is documented as a stub. It appends `"empty-result"` as a warning tag on the completion envelope but does not change the envelope shape or block output.

**Run command** (`cli_tools/tnh_gen/commands/run.py`): `_build_success_payload()` always emits `"status": "succeeded"`. `_emit_run_output()` calls `write_output_file()` unconditionally — so an empty `result_text` produces a provenance-only output file with `"status": "succeeded"` in the API payload and exit code `0`.

**Provenance records**: Capture model, tokens, finish_reason, estimated cost. Do not capture which response field was read, what content parts were present, or any classification of why text was absent. When a trace fails, the provenance record is insufficient to diagnose it.

### Problem

Orchestrators and CI pipelines that trust exit code or the `"status"` field are silently deceived when a generation produces no usable text. The failure is invisible. Additionally, as new model generations (gpt-5, gpt-5.4) depart from the `choices[0].message.content` response shape, the number of undetected empty-result failures is expected to increase.

The deeper architectural problem is not just missing failure detection; it is that success/failure semantics live partly in transport enums, partly in warning strings, and partly in ad hoc CLI payload construction. That violates the object-service rule that canonical behavior should be represented in typed domain models, not reconstructed in app glue.

### Scope

Issues: #47 (gpt-5 empty text), #48 (empty result reported as success), #52 (insufficient diagnostics).

Related: [ADR-TG01](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md) §5 (error handling), [ADR-TG01.1](/architecture/tnh-gen/adr/adr-tg01.1-human-friendly-defaults.md) (API payload contract).

---

## Decision

### 1. Normalize Transport Status Into a Typed Domain Outcome

Keep transport-layer `ProviderStatus` values as the provider-seam contract:

```
ProviderStatus.OK         — usable text extracted
ProviderStatus.INCOMPLETE — text extracted but completion was truncated
ProviderStatus.FAILED     — API call completed but no usable text could be extracted
```

But stop treating those transport values as the application contract. Instead, `CompletionEnvelope` becomes a typed domain envelope with explicit outcome state:

```python
class CompletionOutcomeStatus(str, Enum):
    SUCCEEDED = "succeeded"
    INCOMPLETE = "incomplete"
    FAILED = "failed"


class CompletionFailure(BaseModel):
    reason: FailureReason
    message: str
    retryable: bool = False
    adapter_diagnostics: AdapterDiagnostics | None = None


class CompletionEnvelope(BaseModel):
    outcome: CompletionOutcomeStatus
    result: CompletionResult | None = None
    failure: CompletionFailure | None = None
    provenance: Provenance
    policy_applied: dict
    warnings: list[str] = Field(default_factory=list)
```

Mapping rules:

- `ProviderStatus.OK` → `CompletionOutcomeStatus.SUCCEEDED`
- `ProviderStatus.INCOMPLETE` → `CompletionOutcomeStatus.INCOMPLETE`
- `ProviderStatus.FAILED` → `CompletionOutcomeStatus.FAILED`

`FAILED` remains semantically distinct from `INCOMPLETE`: `INCOMPLETE` means "usable text exists but was cut off"; `FAILED` means "no usable text was produced or extracted."

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

This keeps root-cause classification at the adapter boundary, where the raw provider response is still available.

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

### 4. Keep `post_check()` as a Compatibility Hook, Not an Outcome Gate

The typed `CompletionEnvelope` is now the only authoritative success/failure contract. `safety_gate.py` `post_check()` remains available as a future policy hook, but it does not append soft warnings or reinterpret adapter outcomes:

- If `envelope.outcome == FAILED`, callers trust that terminal state directly.
- If `envelope.outcome == INCOMPLETE`, callers may surface warnings already attached elsewhere, but `post_check()` does not rewrite the outcome.
- `post_check()` does not re-derive empty-text detection; it trusts the adapter/mapper path that already classified the response.
- `run.py` branches directly on `envelope.outcome`; `service.generate()` does not mutate the envelope after mapping.

---

### 5. Failure Path in `run.py`

`run.py` switches from "always build success payload, then maybe error later" to branching directly on the typed domain envelope:

- When `envelope.outcome == SUCCEEDED`: emit `"status": "succeeded"` and permit file output.
- When `envelope.outcome == INCOMPLETE`: emit `"status": "incomplete"` with result + warnings, and permit output according to CLI policy.
- When `envelope.outcome == FAILED`: emit `"status": "failed"` plus a typed `failure` object, write **no output file**, and exit non-zero.

In `--api` mode, the payload follows the existing envelope contract from ADR-TG01.1, extended with a structured `failure` object rather than a single flat `failure_reason` field:

```json
{
  "status": "failed",
  "failure": {
    "reason": "empty_content_with_tokens",
    "message": "Provider returned no extractable text after consuming completion tokens.",
    "retryable": false,
    "adapter_diagnostics": {
      "content_source": "choices[0].message.content",
      "content_part_count": null,
      "raw_finish_reason": "stop",
      "extraction_notes": "message.content was null; completion_tokens=128"
    }
  }
}
```

---

### 6. `AdapterDiagnostics` Record

Add an optional `adapter_diagnostics: AdapterDiagnostics | None` field to `ProviderResponse`. Populated on any non-`OK` status. Fields:

| Field | Type | Description |
|-------|------|-------------|
| `content_source` | `str` | Response field path that was read (e.g., `"choices[0].message.content"`) |
| `content_part_count` | `int \| None` | Number of parts in the content array, if parts-style response |
| `raw_finish_reason` | `str` | Raw finish_reason string before mapping to internal enum |
| `extraction_notes` | `str` | Free-form adapter notes on what was found vs. expected |

`AdapterDiagnostics` is included in API-mode output when `outcome != SUCCEEDED`. It is omitted from default human output to avoid verbosity.

---

### Data Flow Summary

```
openai_adapter.from_openai_response()
  → sets ProviderStatus.FAILED + FailureReason + AdapterDiagnostics
  ↓
completion_mapper.provider_to_completion()
  → maps transport status into CompletionEnvelope(outcome=FAILED, failure=...)
  ↓
service.generate()
  → returns typed CompletionEnvelope without flattening failure into warnings
  ↓
run command
  → branches on envelope.outcome
  → emits {"status": "failed", "failure": {...}}
  → no file write, exit code 1
```

---

## Consequences

### Positive

- Empty results are explicitly represented as failures at every layer.
- Orchestrators get reliable exit codes and machine-readable typed `failure` payloads.
- Adapter failures caused by new model response shapes are diagnosable from provenance alone, without replaying the API call.
- `post_check()` no longer introduces soft warning noise that can contradict the typed outcome contract.
- The distinction between transport status and domain outcome becomes explicit instead of leaking through warning strings and CLI dict assembly.

### Negative

- `CompletionEnvelope` is a breaking contract change for all typed callers of `GenAIService.generate()` and related helpers.
- Adding `AdapterDiagnostics` to failed API output increases payload size and complexity.
- The `FailureReason` enum is a new contract surface that must be kept stable across model updates.

---

## Alternatives Considered

### Alternative 1: Reuse `INCOMPLETE` for empty-with-tokens

**Approach**: Map empty content with tokens to `INCOMPLETE` rather than introducing `FAILED`.

**Rejected**: `INCOMPLETE` semantically means "text exists but was truncated." Empty-with-tokens is a categorically different condition — the model responded but the adapter could not extract content. Conflating them obscures the root cause in diagnostics.

### Alternative 2: Represent failure only as an exception

**Approach**: Keep the domain envelope success-shaped and signal empty-result failures exclusively by raising `GenerationFailed`.

**Rejected**: Exceptions are appropriate for transport and policy faults, but a provider-completed call that produced no usable text is still a typed business outcome. Encoding that state only in control flow would keep failure semantics out of the domain model and preserve the current split between typed service behavior and ad hoc CLI payload assembly.

### Alternative 3: Treat empty result as a retryable warning

**Approach**: On empty result, set a warning flag and allow callers to decide whether to retry or fail.

**Rejected**: The current behavior of writing provenance-only output files and emitting `"status": "succeeded"` is the direct cause of silent orchestration failures (#48). A retry-or-warn approach does not fix that — it defers the decision to callers who may not implement the check.

### Alternative 4: Detect empty results only in `post_check()`

**Approach**: Leave the adapter unchanged; detect empty text in `safety_gate.post_check()`.

**Rejected**: The adapter has the full response object and is the correct place to distinguish *why* content is absent (missing field vs. empty string vs. unexpected shape). `post_check()` sees only the extracted `CompletionEnvelope` and cannot reconstruct this information. Adapter-level detection produces richer diagnostics.

---

## Open Questions

1. **`FailureReason` extensibility**: Should `FailureReason` be a `str`-typed enum (open-ended, extensible by new adapters) or a closed `IntEnum`? Open-ended is more forward-compatible as new model families are added.

2. **Retry integration**: Should `CompletionFailure.retryable` be inferred centrally from `FailureReason`, or set adapter-by-adapter? Some failure reasons (e.g., `CONTENT_EXTRACTION_ERROR` due to a transient parse issue) may be retryable; others (`UNSUPPORTED_RESPONSE_SHAPE`) are not.

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
