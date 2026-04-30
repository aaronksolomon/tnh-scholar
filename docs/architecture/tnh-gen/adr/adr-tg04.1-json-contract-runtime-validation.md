---
title: "ADR-TG04.1: JSON Contract Runtime Validation"
description: "Define the runtime contract for resolving schema_ref, validating JSON prompt outputs, mapping failures, and serializing structured results in tnh-gen."
type: "design-detail"
owner: "aaronksolomon"
author: "Aaron Solomon, OpenAI Codex"
status: accepted
created: "2026-04-30"
parent_adr: "adr-tg04-structured-json-contract-and-scope.md"
related_adrs:
  - "adr-tg03-completion-contract.md"
  - "adr-tg02-prompt-integration.md"
  - "adr-tg01.1-human-friendly-defaults.md"
  - "adr-pt05-prompt-platform-strategy.md"
---
# ADR-TG04.1: JSON Contract Runtime Validation

Define the runtime contract for JSON-output prompts in `tnh-gen`, including schema artifact resolution, validation flow, CLI/API serialization, and failure mapping.

- **Filename**: `adr-tg04.1-json-contract-runtime-validation.md`
- **Status**: Accepted
- **Date**: 2026-04-30
- **Authors**: Aaron Solomon, OpenAI Codex
- **Owner**: aaronksolomon
- **Parent ADR**: [ADR-TG04: Structured JSON Contract and Scope Boundaries](/architecture/tnh-gen/adr/adr-tg04-structured-json-contract-and-scope.md)

---

## ADR Editing Policy

**Status**: `accepted` — preserve the original decision sections. Future changes should be tracked by addendum or follow-on ADR.

---

## Context

TG04 establishes that:

- `tnh-gen` is a prompt-agnostic runner
- JSON mode guarantees structural correctness, not semantic correctness
- `schema_ref` refers to a contract schema rather than necessarily to a Python model

What TG04 intentionally leaves open is the runtime contract detail:

1. what artifact format backs `schema_ref`
2. how `schema_ref` is resolved at runtime
3. how JSON output is validated
4. how validation failures map into CLI and domain outcomes
5. how structured results appear in `--api`

These are not optional details. Without them, `schema_ref` remains an opaque string and runtime validation is only aspirational.

---

## Decision

### 1. `schema_ref` Resolves to JSON Schema Artifacts

The first supported contract artifact format is JSON Schema stored as files.

This ADR does not define a new custom schema language.

The runtime convention is:

- contract files live under `schemas/prompt-contracts/`
- files are UTF-8 JSON documents
- each file contains one JSON Schema document suitable for validating the prompt output payload

### 2. Dotted `schema_ref` Resolution Convention

The dotted reference form resolves to a hierarchical file path.

Resolution rule:

- `tnh.sectioning.default_section.v1`
- becomes
- `tnh/sectioning/default_section/v1.schema.json`

under a prompt-contract schema root.

Search roots follow the same precedence model as other TNH runtime assets:

1. workspace: `<workspace>/schemas/prompt-contracts/`
2. user: `<user-config>/schemas/prompt-contracts/`
3. built-in: `<runtime_assets>/schemas/prompt-contracts/`

This allows:

- repo-local schema development
- user overrides or experimentation
- packaged built-in defaults

### 3. Catalog and Runtime Responsibilities

Validation occurs at two distinct layers.

#### A. Catalog / Compile Validation

Prompt validation and catalog health checks must verify:

- JSON prompts declare `output_contract.schema_ref`
- the referenced schema artifact exists
- the schema artifact is itself structurally valid JSON Schema

Catalog validation does not execute the prompt or validate provider output.

#### B. Runtime Validation

`tnh-gen run` for a JSON prompt must:

1. resolve the schema artifact from `schema_ref`
2. obtain provider output in JSON form
3. parse the returned JSON
4. validate it against the resolved JSON Schema
5. treat validation failure as invocation failure

Runtime validation remains authoritative even if catalog validation already passed.

### 4. Provider-Native Structured Output Is Preferred but Not Required

When the selected provider/model supports structured output assistance, the runtime should prefer provider-native structured output facilities for JSON prompts.

Examples:

- JSON-object mode
- schema-constrained structured output

But provider-native support is not the universal contract.

The authoritative guarantee is local contract validation against the resolved schema artifact.

This means:

- providers without native structured-output support may still run JSON prompts
- prompt wording plus local parse/validate remains a valid fallback path
- the runtime must not silently skip local validation just because the provider claimed structured output support

### 5. Legacy `output_mode` Compatibility

New JSON prompts must use:

```yaml
output_contract:
  mode: json
  schema_ref: ...
```

Legacy `output_mode: json` without a resolvable `output_contract.schema_ref` is not sufficient for maintained JSON prompt behavior.

Compatibility normalization may continue at the metadata layer, but runtime JSON validation requires a resolved schema artifact.

### 6. Distinguish Pre-Invocation Contract Errors from Post-Invocation Validation Failures

There are two separate failure classes.

#### A. Pre-Invocation Contract Errors

Examples:

- `schema_ref` missing
- schema artifact not found
- schema artifact malformed

These are setup/configuration failures.

They raise `ConfigurationError` before provider invocation and surface through the normal CLI error path.

Under the current CLI contract, these are input/configuration failures.

#### B. Post-Invocation Contract Validation Failures

Examples:

- provider returned non-JSON text
- provider returned parseable JSON that does not satisfy the schema

These are generation-result format failures.

They must:

- map to a typed failed completion outcome
- use a new failure reason: `CONTRACT_VALIDATION_FAILED`
- map to CLI exit code `4` (`FORMAT_ERROR`)

This extends the TG03 taxonomy rather than bypassing it.

### 7. `--api` Envelope Shape for JSON Prompts

For JSON prompts in API mode, the result payload must expose structured data explicitly.

Success and incomplete payloads must include:

- `result.json`: the validated parsed JSON object
- `result.schema_ref`: the applied schema reference
- `result.text`: always present for JSON prompts and set to the canonical JSON serialization of `result.json`

Illustrative shape:

```json
{
  "status": "succeeded",
  "result": {
    "json": {
      "sections": [
        {"title": "Example", "start_line": 1}
      ]
    },
    "schema_ref": "tnh.sectioning.default_section.v1",
    "text": "{\"sections\":[{\"title\":\"Example\",\"start_line\":1}]}",
    "model": "gpt-5",
    "provider": "openai",
    "usage": {
      "prompt_tokens": 123,
      "completion_tokens": 45,
      "total_tokens": 168
    },
    "finish_reason": "stop"
  }
}
```

For text prompts, `result.json` and `result.schema_ref` are omitted.
`result.text` remains present for text prompts as the primary result field.

### 8. Normal CLI and Output-File Behavior for JSON Prompts

For JSON prompts in normal human CLI use:

- stdout may remain human-oriented
- but `--output-file` must write canonical JSON text representing the validated payload

This output is the supported machine-usable artifact for downstream chaining.
If the run fails with `CONTRACT_VALIDATION_FAILED`, no output file is written, consistent with TG03 failed-outcome handling.

### 9. Clarify `--vars` Chaining Semantics

`--vars` accepts a top-level JSON object whose keys become variable bindings.

Supported pattern:

```json
{
  "sections": [...],
  "document_summary": "..."
}
```

This can be passed as `--vars` and later referenced by prompts through those variable names.

Unsupported assumption:

- arbitrary JSON is not automatically flattened into variables
- `tnh-gen` does not auto-project nested structures into multiple top-level vars beyond normal object semantics

If a downstream prompt expects a complex object, that object must appear under a declared variable key.

### 10. Prompt Authoring Guidance for JSON Prompts

Maintained JSON prompts should include both contract metadata and natural-language contract guidance.

Canonical example:

```markdown
---
key: example_json_prompt
name: Example JSON Prompt
version: "1.0"
description: Produce structured metadata for downstream processing
output_contract:
  mode: json
  schema_ref: tnh.example.metadata.v1
---

Return valid JSON matching the declared schema.

Required top-level fields:
- `title`: string
- `language`: string
- `sections`: array of objects with `title` and `start_line`

Do not return commentary, markdown fences, or explanatory prose.
```

## Consequences

### Positive

- `schema_ref` becomes a real runtime contract instead of an opaque string.
- API consumers get explicit structured payloads.
- Human CLI workflows gain a canonical JSON artifact path for chaining.
- Consumer systems such as `ai_text_processing` can project validated JSON safely.

### Negative

- Schema artifacts now become a maintained part of the runtime surface.
- TG03 and CLI type contracts require coordinated updates.
- Existing JSON prompts may temporarily fail until schemas are authored and aligned.

### Risks

- Poorly designed schemas may validate structurally while still allowing low-value outputs.
- Provider-native structured-output support may vary by model and require careful fallback testing.
- Prompt authors may overestimate what `--vars` chaining can do automatically.

---

## Alternatives Considered

### Alternative 1: Leave `schema_ref` as an Opaque Documentation String

**Rejected**: This fails the central runtime-contract goal and leaves golden-path JSON behavior unreliable.

### Alternative 2: Require Provider-Native Structured Output for All JSON Prompts

**Rejected**: Too restrictive and too provider-specific for the base contract.

### Alternative 3: Expose Only `result.text` in API Mode

**Rejected**: Machine consumers should not need to reparsed nested JSON strings to recover structured data.

---

## Open Questions

1. Which current JSON prompts should be treated as the first required maintained schema set? The obvious initial candidates are `default_section`, `section_by_break`, `generate_sections_en`, `generate_sections_multi_lang`, and `translate_json`.

## Resolved Clarifications

- Schema artifacts are JSON-only initially. YAML authoring is out of scope for the first contract and may be considered later only via explicit addendum.
- Missing schema artifacts for declared JSON prompts are catalog-health errors, not warnings.

---

## References

- [ADR-TG04: Structured JSON Contract and Scope Boundaries](/architecture/tnh-gen/adr/adr-tg04-structured-json-contract-and-scope.md)
- [ADR-TG03: Typed Completion Outcome and Adapter Diagnostics](/architecture/tnh-gen/adr/adr-tg03-completion-contract.md)
- [ADR-TG02: TNH-Gen CLI Prompt System Integration](/architecture/tnh-gen/adr/adr-tg02-prompt-integration.md)
- [ADR-TG01.1: Human-Friendly CLI Defaults with --api Flag](/architecture/tnh-gen/adr/adr-tg01.1-human-friendly-defaults.md)
- [ADR-PT05: Prompt Platform Strategy](/architecture/prompt-system/adr/adr-pt05-prompt-platform-strategy.md)
