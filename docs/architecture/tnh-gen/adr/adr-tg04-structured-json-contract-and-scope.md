---
title: "ADR-TG04: Structured JSON Contract and Scope Boundaries"
description: "Define tnh-gen as a prompt-agnostic execution substrate, separate it from higher-level semantic processing and orchestration, and establish the scope for structured JSON contracts."
owner: "aaronksolomon"
author: "Aaron Solomon, OpenAI Codex"
status: accepted
created: "2026-04-30"
related_adrs:
  - "adr-tg01-cli-architecture.md"
  - "adr-tg01.1-human-friendly-defaults.md"
  - "adr-tg02-prompt-integration.md"
  - "adr-tg03-completion-contract.md"
  - "adr-at03-object-service-refactor.md"
  - "adr-at04-ai-text-processing-platform-strat.md"
  - "adr-pt04-prompt-system-refactor.md"
  - "adr-pt05-prompt-platform-strategy.md"
  - "adr-tg04.1-json-contract-runtime-validation.md"
---
# ADR-TG04: Structured JSON Contract and Scope Boundaries

Define `tnh-gen` as a prompt-agnostic execution substrate that supports text and structured JSON outputs through prompt-declared contracts, while leaving semantic validation, chunk orchestration, and domain-specific post-processing to higher-level consumer systems.

- **Filename**: `adr-tg04-structured-json-contract-and-scope.md`
- **Status**: Accepted
- **Date**: 2026-04-30
- **Authors**: Aaron Solomon, OpenAI Codex
- **Owner**: aaronksolomon

---

## ADR Editing Policy

**Status**: `accepted` — preserve the original decision sections. Future changes should be tracked by addendum or follow-on ADR.

---

## Context

### 1. Current Tension

`tnh-gen` was designed as a general prompt runner, not a sectioning-specific tool. In practice, current prompts include both:

- plain text transformations
- structured JSON-producing prompts such as `section_by_break`, `default_section`, and `translate_json`

But the architecture currently leaves several questions under-specified:

1. What exactly does `schema_ref` mean at runtime?
2. Does `tnh-gen` require a concrete Python response model per JSON prompt?
3. Is `tnh-gen` responsible for section splitting, batching, or semantic validation?
4. How should existing typed consumer systems such as `ai_text_processing` relate to `tnh-gen`?

### 2. What the Existing Systems Suggest

The repository contains two overlapping but distinct architectural lines:

#### A. `ai_text_processing`

`ai_text_processing` is a specialized subsystem built around `TextObject`, `NumberedText`, `AIResponse`, sectioning, and line-based translation workflows.

It is still active code with real consumers, including:

- `srt_translate`
- audio multilingual services
- internal sectioning and translation flows

In this subsystem, `AIResponse` is a domain-specific structured response envelope used to support known processing workflows.

#### B. `tnh-gen`

`tnh-gen` is a newer, more generic CLI and execution surface built around:

- prompt discovery and rendering
- GenAI provider execution
- provenance and contract output
- human CLI use plus future machine consumers through `--api`

The `tnh-gen` design does not clearly define sectioning-specific semantics as part of the base tool. It is better understood as a prompt-agnostic runner.

### 3. Gaps in the Current Design Record

The docs and walkthroughs show chained workflows where output from one `tnh-gen` run is used as input or variables for another run. This pattern exists in user-facing materials, including golden-path examples, but is not clearly elevated into an ADR-level architectural contract.

Similarly, the prompt-platform ADRs require JSON prompts to declare `schema_ref`, but do not fully specify:

- whether `schema_ref` resolves to a Python model, a schema artifact, or another contract object
- how `tnh-gen` validates JSON outputs at runtime
- how generic structured-output support should coexist with domain-specific typed consumers such as `ai_text_processing`

This ADR resolves the scope and identity questions. The concrete runtime validation mechanism is defined separately in [ADR-TG04.1: JSON Contract Runtime Validation](/architecture/tnh-gen/adr/adr-tg04.1-json-contract-runtime-validation.md).

### 4. Design Constraint

The repository direction suggests that `tnh-gen` should not be defined around the needs of one current consumer such as `ai_text_processing`.

At the same time, `tnh-gen` must preserve enough contract discipline that consumer systems can rely on structured outputs safely.

That implies a layered design:

- `tnh-gen` owns generic prompt execution and structural contract validation
- consumer systems own semantic interpretation, projection into domain models, and multi-step orchestration

---

## Decision

### 1. Define `tnh-gen` as Prompt-Agnostic

`tnh-gen` is a prompt-agnostic execution substrate.

Its responsibilities are:

- load and validate prompt metadata
- render prompts with caller variables
- execute prompts through the GenAI provider stack
- surface outputs in human CLI mode and machine-readable API mode
- enforce declared output contracts for text and JSON modes

`tnh-gen` is not defined as a sectioning tool, translation workflow engine, or chunk orchestration system.

### 2. Define the Meaning of JSON Output Mode

For prompts declaring:

```yaml
output_contract:
  mode: json
  schema_ref: ...
```

the runtime meaning is:

1. the prompt expects machine-readable JSON output
2. the JSON output must be structurally validated against the declared contract referenced by `schema_ref`
3. success means the output satisfies the declared structural contract

This guarantees structural correctness only.

It does **not** guarantee:

- semantic correctness
- quality of section boundaries
- faithfulness of translation
- suitability for downstream chunking or orchestration

### 3. `schema_ref` Refers to a Contract Schema, Not Necessarily a Python Model

`schema_ref` is a reference to a runtime-validatable contract schema.

It is **not** defined as a required one-to-one mapping to a concrete Python response model for every prompt.

This allows `tnh-gen` to support arbitrary structured JSON prompt outputs without requiring the codebase to predeclare a Pydantic model for every possible prompt shape.

Typed Python models remain allowed, but only as optional consumer-side projections over validated JSON contracts.

### 4. Base Runtime Behavior for JSON Prompts

For JSON prompts, `tnh-gen` must:

- obtain model output in a machine-usable JSON form
- validate that output against the contract identified by `schema_ref`
- treat contract-validation failure as invocation failure, not soft warning noise

The concrete runtime mechanism, failure taxonomy, and API envelope details are defined in [ADR-TG04.1: JSON Contract Runtime Validation](/architecture/tnh-gen/adr/adr-tg04.1-json-contract-runtime-validation.md).

### 5. Human CLI Mode Is a First-Class Requirement

The primary near-term requirement is that real user CLI workflows succeed.

For JSON prompts in normal CLI use:

- stdout behavior must remain usable for humans
- `--output-file` must write canonical machine-usable JSON bodies suitable for downstream chaining

For `--api` mode:

- the same validated structure must be surfaced inside the API envelope for future consumers

This means the design must not optimize only for API mode. User CLI workflows and golden tests are first-class contract surfaces.

### 6. Chained `tnh-gen` Workflows Are Supported, but Orchestration Semantics Live Above `tnh-gen`

It is valid to use output from one `tnh-gen` invocation as input to another invocation.

Examples:

- JSON object output used as `--vars` when the top-level shape matches variable-binding expectations
- text output used as later `--input-file`
- validated structured output consumed by another tool

However, `tnh-gen` does not own higher-order workflow semantics such as:

- fan-out over generated sections
- chunk scheduling
- retry policy over many derived tasks
- semantic review of intermediate outputs

Those belong to higher-level orchestration layers, scripts, UI integrations, or future dedicated tools.

### 7. Section Splitting and Semantic Review Are Not Core `tnh-gen` Responsibilities

Prompts such as `default_section` and `section_by_break` may produce structured section metadata, but `tnh-gen` itself is not a general-purpose "split this file into chunks and distribute work" framework.

Section splitting for downstream distributed processing is expensive and semantically loaded. The base runner should not absorb that responsibility.

Likewise, semantic validation of sectioning quality belongs to:

- assistant CLI review loops
- dedicated validation prompts
- future orchestration or pipeline systems
- domain-specific consumers such as `ai_text_processing`

### 8. `ai_text_processing` Is a Consumer System, Not the Definition of `tnh-gen`

`ai_text_processing` remains an active specialized subsystem with its own domain types and workflows.

Its contract with `tnh-gen` is:

- `tnh-gen` must preserve robust structured-output discipline
- consumer systems may project validated JSON into domain-specific types such as `AIResponse`

But:

- `AIResponse` does not define the universal `tnh-gen` JSON contract
- `tnh-gen` should not be redesigned around one consumer subsystem

### 9. Typed Consumer Projections Remain Valid

After JSON output has been structurally validated, a consumer may optionally map it into a typed domain model.

Examples:

- `ai_text_processing` may project validated sectioning JSON into `AIResponse`
- future orchestrators may project validated outputs into their own domain objects

This projection layer is explicitly downstream from the base `tnh-gen` contract.

### 10. Prompt Specifications Must Be Clearer About Structured Outputs

For JSON prompts, prompt authors must declare:

- `output_contract.mode: json`
- `output_contract.schema_ref`

Prompt specifications should also be explicit, in natural language, about:

- the expected top-level fields
- ordering or coverage constraints where relevant
- whether output is intended for downstream machine consumption

This improves both human maintainability and runtime validation alignment.

---

## Consequences

### Positive

- `tnh-gen` gets a clearer identity as a generic execution substrate.
- Structured JSON support can scale to arbitrary prompt shapes.
- Existing specialized systems such as `ai_text_processing` remain compatible.
- Human CLI workflows and API consumers are both served by the same structural contract.
- The architecture separates structural validation from semantic correctness cleanly.

### Negative

- Structural validation alone will not satisfy all real-world quality needs.
- Downstream orchestration and semantic review remain additional work outside the base tool.
- Schema management becomes a first-class architectural concern.
- Runtime validation details still require concrete implementation work; this ADR alone does not imply that the mechanism is already present in code.

### Risks

- If schema artifacts are weak or underspecified, structural validation may create false confidence.
- Chained prompt workflows may appear more "officially supported" than their orchestration semantics really are.
- Consumers may still be tempted to smuggle domain-specific behavior back into `tnh-gen`.
- Some referenced upstream ADRs in this area, especially PT05 and AT04, remain non-final; future alignment work may still be required across the ADR set.

---

## Alternatives Considered

### Alternative 1: Make `tnh-gen` Sectioning-Aware

Treat sectioning prompts as special built-ins and add native chunk-splitting and follow-on batching behavior to the CLI.

**Rejected**: This narrows a generic prompt runner into one workflow family and pushes expensive semantic orchestration into the wrong layer.

### Alternative 2: Require a Concrete Python Model per JSON Prompt

Map every prompt `schema_ref` directly to a checked-in Pydantic model.

**Rejected**: This does not scale to arbitrary structured prompt shapes and overfits `tnh-gen` to current known consumers.

### Alternative 3: Permit JSON Prompts Without Runtime Validation

Treat `schema_ref` as documentation only and rely on prompt wording plus ad hoc consumer parsing.

**Rejected**: This is too weak for live golden tests, CLI chaining, or future API consumers.

### Alternative 4: Move All Structured Processing Back Into `ai_text_processing`

Use `ai_text_processing` as the primary structured-output engine and treat `tnh-gen` as a thin wrapper.

**Rejected**: This reverses the architecture direction toward a more prompt-agnostic execution surface and limits future extensibility.

---

## Open Questions

1. What concrete schema artifact format should back `schema_ref` at runtime?
2. How should prompt-catalog validation report missing or invalid runtime schema references?
3. What is the minimum required prompt-authoring guidance for machine-consumable JSON prompts?
4. Which current documented chained workflows should be promoted into explicit supported examples versus left as exploratory patterns?

---

## References

- [ADR-TG01: tnh-gen CLI Architecture](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md)
- [ADR-TG01.1: Human-Friendly CLI Defaults with --api Flag](/architecture/tnh-gen/adr/adr-tg01.1-human-friendly-defaults.md)
- [ADR-TG02: TNH-Gen CLI Prompt System Integration](/architecture/tnh-gen/adr/adr-tg02-prompt-integration.md)
- [ADR-TG03: Typed Completion Outcome and Adapter Diagnostics](/architecture/tnh-gen/adr/adr-tg03-completion-contract.md)
- [ADR-AT03: Minimal AI Text Processing Refactor for tnh-gen](/architecture/ai-text-processing/adr/adr-at03-object-service-refactor.md)
- [ADR-AT04: AI Text Processing Platform Strategy](/architecture/ai-text-processing/adr/adr-at04-ai-text-processing-platform-strat.md)
- [ADR-PT04: Prompt System Refactor Plan (Revised)](/architecture/prompt-system/adr/adr-pt04-prompt-system-refactor.md)
- [ADR-PT05: Prompt Platform Strategy](/architecture/prompt-system/adr/adr-pt05-prompt-platform-strategy.md)
