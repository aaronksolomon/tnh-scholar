---
title: "ADR-TG04.3: Structured Output Trust Boundaries and Control Surfaces"
description: "Define how tnh-gen and downstream consumers should treat model-produced structured data, distinguish artifact contracts from control contracts, and prefer deterministic control outside AI-generated payloads."
type: "design-detail"
owner: "aaronksolomon"
author: "OpenAI Codex"
status: proposed
created: "2026-05-03"
parent_adr: "/architecture/tnh-gen/adr/adr-tg04-structured-json-contract-and-scope.md"
related_adrs:
  - "/architecture/tnh-gen/adr/adr-tg04.1-json-contract-runtime-validation.md"
  - "/architecture/tnh-gen/adr/adr-tg04.2-structured-json-provenance-sidecars.md"
  - "/architecture/tnh-gen/adr/adr-tg03-completion-contract.md"
  - "/architecture/prompt-system/adr/adr-pt05-prompt-platform-strategy.md"
---
# ADR-TG04.3: Structured Output Trust Boundaries and Control Surfaces

Define the trust model for structured outputs produced through `tnh-gen`, including where shape guarantees are sufficient, where semantic skepticism must remain, and how deterministic control should be separated from AI-generated content.

- **Filename**: `adr-tg04.3-structured-output-trust-boundaries.md`
- **Status**: Proposed
- **Date**: 2026-05-03
- **Author**: OpenAI Codex
- **Owner**: aaronksolomon
- **Parent ADR**: [ADR-TG04: Structured JSON Contract and Scope Boundaries](/architecture/tnh-gen/adr/adr-tg04-structured-json-contract-and-scope.md)

---

## ADR Editing Policy

**Status**: `proposed` — this ADR is in the design loop and may be rewritten while the proposal is being refined.

---

## Context

### 1. Structural Reliability Has Improved, but Semantic Reliability Has Not Become Deterministic

The current `tnh-gen` structured-output line already establishes an important boundary:

- `tnh-gen` guarantees structural validation, not semantic correctness
- prompt-declared `schema_ref` contracts are enforced locally at runtime
- JSON artifacts remain machine-usable JSON, with provenance preserved separately

Those decisions are established in:

- [ADR-TG04: Structured JSON Contract and Scope Boundaries](/architecture/tnh-gen/adr/adr-tg04-structured-json-contract-and-scope.md)
- [ADR-TG04.1: JSON Contract Runtime Validation](/architecture/tnh-gen/adr/adr-tg04.1-json-contract-runtime-validation.md)
- [ADR-TG04.2: Structured JSON Provenance Sidecars](/architecture/tnh-gen/adr/adr-tg04.2-structured-json-provenance-sidecars.md)

What remains under-specified is the practical trust boundary for downstream engineering decisions.

Recent work on live golden runs for maintained JSON prompts reinforces that the system can receive outputs that are:

- valid JSON
- schema-valid after local normalization and validation
- still semantically suspect or contaminated by prompt/schema influence

That combination is not a bug in the layered design. It is a reminder that structural validity and semantic trust are separate concerns.

### 2. Recent Live Golden Evaluation Shows the Gray Area Clearly

Recent live golden evaluation of maintained JSON prompts shows that prompts can succeed structurally while still exposing model quirks such as schema echo or over-fitting to the described contract shape.

This matters because it creates a dangerous ambiguity:

- the system may be tempted to treat validated JSON as ordinary deterministic program state
- but the underlying producer remains a probabilistic model rather than a conventional module or API implementation

If this ambiguity is not made explicit, downstream code may drift toward using rich AI-generated payloads as hidden control surfaces.

### 3. `tnh-gen` Was Originally Artifact-Oriented; Control-Surface Interest Is Newer

`tnh-gen` was designed first as a general prompt runner oriented around human use, prompt rendering, execution, provenance, and artifact production.

That original posture aligns much more naturally with artifact contracts than with control contracts.

Interest in small machine-actionable structured outputs has grown later, largely because of:

- agent orchestration experiments
- evaluator-style workflows
- interest in semi-autonomous or bounded automatic loops

This newer interest does not invalidate the original artifact-oriented design, but it does create pressure to keep artifact and control concerns legible rather than blending them into one ambiguous surface.

At the time of this ADR, there is no clear maintained runtime consumer that performs important branching directly from the new `tnh-gen` JSON-contract outputs.

The closest existing programmatic analogue is the older `ai_text_processing` / `TextObject` path, which already consumes typed sectioning output for downstream processing, including SRT-related flows, but does so through its own domain-specific response models rather than through the newer `tnh-gen` JSON-contract interface.

### 4. Modern OpenAI Structured Output Support Changes the Trade Space, but Not the Core Epistemic Limit

OpenAI's current official API guidance is materially stronger than the earlier "please emit JSON" era:

- Structured Outputs are preferred over legacy JSON mode
- the Responses API provides a dedicated structured-output surface
- newer GPT-5-series models expose structured-output support as a first-class feature
- refusals are documented as an explicit separate outcome
- strict mode exists, but only for a supported subset of JSON Schema

This improves the engineering usefulness of structured output contracts.

It does **not** change the more fundamental limitation:

- AI-generated payloads are still not equivalent to deterministic, semantically trustworthy program state

The improved model/runtime contract narrows formatting risk. It does not remove interpretation risk.

### 5. `tnh-gen` Needs a More Explicit Distinction Between Artifact Transport and Control Flow

Current `tnh-gen` usage includes two broad classes of structured outputs:

1. rich artifacts intended for human review or downstream consumption
2. smaller outputs that may tempt the system to drive decisions such as branching, retries, or workflow routing

These classes should not be treated as equally trustworthy.

Without an explicit design rule, higher-level systems may accidentally let rich model-produced JSON become de facto control logic.

### 6. A Cleaner Future Separation May Be Desirable, but It Is Not Today's Decision

One plausible long-term direction is to separate artifact-oriented and control-oriented surfaces into distinct CLI systems that may share underlying code.

Illustrative future shape:

- an artifact-oriented CLI surface, potentially continuing the current `tnh-gen` role
- a control-oriented or orchestration-oriented CLI surface with narrower contracts and distinct operator expectations

Such a split could improve:

- consumer clarity
- flag and option design
- testing expectations
- programmatic safety

But that is a larger product and architecture choice. It should not be smuggled into today's structured-output hardening work as an incidental side effect.

### 7. Current Runtime Posture Is Already Hybrid Rather Than Fully Strict

The present service path uses provider-assisted JSON schema output when possible, but still treats local validation as authoritative and does not rely on provider-native strict enforcement as the sole contract.

That is an appropriate current posture, but it also means the architecture should explicitly state what local validation does and does not buy us:

- it buys shape discipline
- it does not buy semantic certainty

This ADR formalizes that boundary.

---

## Decision

### 1. Define Structured Output as a Typed Transport Boundary, Not a Semantic Truth Boundary

Within `tnh-gen` and its consumers, a successful structured-output run means:

- the provider returned output that could be interpreted as JSON
- the local runtime validated the payload against the declared contract
- the payload is safe to treat as a typed transport artifact

It does **not** mean:

- the content is semantically correct
- the reasoning behind the content is trustworthy
- the payload is safe to use directly as deterministic control logic

The architectural meaning of success remains intentionally limited to validated structure plus normal completion semantics.

### 2. Distinguish Artifact Contracts from Control Contracts

Structured-output contracts should be treated as belonging to one of two categories.

#### A. Artifact Contracts

Artifact contracts describe rich generated payloads intended for:

- human review
- storage
- inspection
- later projection into domain models
- downstream AI-assisted processing

Examples include:

- section inventories
- document summaries
- translated nested content
- metadata bundles

Artifact contracts may be structurally rich and semantically open-ended.

They are valid outputs, but they are not preferred direct drivers of branching or orchestration.

#### B. Control Contracts

Control contracts describe small bounded outputs intended to influence deterministic system behavior.

Examples include:

- pass/fail or approve/reject decisions
- bounded route selections
- enumerated workflow next-step recommendations
- explicit retry or no-retry decisions
- small evidence vectors with fixed keys and bounded value domains

Control contracts must be designed more conservatively than artifact contracts.

They should prefer:

- closed object schemas
- bounded enums and booleans
- low nesting depth
- minimal optionality
- explicit no-op / abstain / unable-to-decide states

### 3. Deterministic Control Flow Must Remain Code-Owned by Default

The default design rule is:

- deterministic orchestration, routing, retries, persistence, and failure policy belong to ordinary code

Model output may inform these decisions, but should not silently replace them.

This means:

- branch selection should prefer code-owned rules over inference from rich generated artifacts
- retry policy should not depend on free-form or rich semantically open payloads
- absence of a valid control contract should degrade to deterministic fallback behavior rather than heuristic improvisation

### 4. Rich AI-Generated JSON Must Not Become Hidden Control Logic

A system must not treat a large semantically rich payload as though it were a trustworthy control object merely because it passed schema validation.

Examples of discouraged patterns:

- routing based on ad hoc interpretation of section titles or summaries
- using model-generated narrative metadata as an implicit execution plan
- deriving workflow branching from broad artifact payloads that were not authored as explicit control contracts

If control decisions are needed, a dedicated control contract should be introduced rather than overloading artifact outputs.

**Scope boundary**: This ADR does **not** decide to split `tnh-gen` into multiple CLI products or rename existing surfaces. Today's decision is smaller: clarify trust boundaries, preserve `tnh-gen`'s artifact-oriented primary posture, and allow bounded control-contract exploration without letting it silently redefine the whole surface. CLI or module separation remains deferred future work (see Decision §12).

### 5. Local Validation Remains Authoritative for Runtime Acceptance, but Validation Scope Must Be Named Honestly

Local contract validation remains required and authoritative for deciding whether a structured output run is acceptable at the transport level.

But validation scope must be described honestly:

- contract validation proves structural conformance
- contract validation does not prove content quality, factuality, coverage, or decision correctness

This wording should be reflected consistently in docs, tests, and higher-level orchestration design.

### 6. Schema-Echo Repair Is Rejected as a Maintained Runtime Behavior

Model outputs that echo schema wrapper structure instead of returning the contracted instance payload must be treated as contract failures rather than silently repaired into success.

Examples include outputs that return shapes resembling schema objects such as:

- top-level `type: object`
- nested `properties` maps containing instance-like values
- other mixed schema-instance hybrids

These responses indicate that the model has not cleanly respected the requested payload boundary.

The system should therefore:

- fail the run under the normal contract-validation failure path
- preserve the raw output for debugging and evaluation
- treat the incident as signal for prompt, schema, or model improvement rather than as a payload to rewrite into success

This is an intentional design choice. The architecture prefers explicit failure over hidden transport-layer repair for malformed or contaminated structured outputs.

The schema-echo normalization shim previously present in the runtime acceptance path has been removed. (`src/tnh_scholar/gen_ai_service/service.py`)

### 7. Prefer Strict Provider-Constrained Output for Control Contracts When the Schema Fits the Supported Subset

When a control contract can be expressed within the provider's supported structured-output subset, the system should prefer provider-constrained strict output plus local validation.

This preference is strongest for:

- small decision objects
- evaluator outputs
- routing recommendations
- machine-only control surfaces

This is a preference, not a universal requirement, because:

- supported schema subsets are narrower than full JSON Schema
- some maintained artifact contracts are intentionally broader and more expressive
- local validation still remains necessary as the system-of-record contract check

### 8. Artifact Contracts May Continue to Use a Hybrid "Provider Assistance Plus Local Validation" Posture

For richer artifact outputs, it is acceptable to continue using a hybrid posture in which:

- provider-native structured output is used where helpful
- local parse and schema validation remain mandatory
- some artifact schemas may remain outside the strict supported subset

This preserves flexibility for semantically rich generated artifacts without overstating their reliability.

This hybrid posture does **not** include silent schema-echo repair. Hybrid means provider assistance plus local acceptance checks, not provider assistance plus heuristic payload rewriting.

### 9. If a Structured Output Will Influence Important Branching, Introduce a Second Validation Layer

When structured output meaningfully influences execution behavior, a second validation layer is required before acting on it.

Valid second-layer forms include:

- deterministic code-side checks on extracted fields
- domain-specific invariants applied after schema validation
- reduction into a smaller bounded control contract
- explicit evaluator steps whose output is itself bounded and reviewable

Schema validity alone is not sufficient justification for consequential branching. The second layer is what makes the boundary between "structurally received" and "trusted for action" explicit.

### 10. Golden Testing Must Evaluate More Than Parseability

For maintained JSON prompts, golden testing should distinguish at least these concerns:

- parse and schema success
- refusal or incomplete outcome rate
- schema-echo or contract contamination
- semantic plausibility for the prompt's intended use
- control-surface safety when the result is intended to influence branching

A green structural golden run is necessary but not sufficient evidence for safe architectural use.

Golden reporting should distinguish at least:

- clean success
- contract failure
- refusal or incomplete outcome
- contamination events such as schema echo

Contamination events should be counted as failures to be fixed, not as repaired successes.

### 11. Initial Acceptance Scope: Harden the Artifact-Oriented Surface Without Collapsing It Into a Control CLI

The immediate architectural direction is intentionally narrower than a CLI split.

Work scoped to this ADR's acceptance should focus on:

- updating maintained `tnh-gen` structured-output usage to current OpenAI GPT-5-family capabilities where appropriate
- improving structured-data handling and validation posture
- schema-echo normalization has been removed from maintained runtime acceptance behavior (Decision §6)
- using golden evaluation to demonstrate bounded human-operator usability for maintained walkthroughs and prompt examples
- preserving a simple path where validated section outputs can be parsed and fed into subsequent bounded `tnh-gen` calls by ordinary deterministic code

This is enough to prove practical usability for artifact-oriented structured outputs without prematurely redefining `tnh-gen` as a control-first orchestration surface.

The response to schema contamination going forward is:

- tighten prompt wording
- tighten schema design where feasible
- move maintained prompts toward stronger GPT-5-family structured-output usage
- let malformed or contaminated outputs fail visibly during evaluation

### 12. Deferred Scope: Product-Surface Separation and Dedicated Control CLI Decisions

The following questions are explicitly deferred:

- whether artifact and control surfaces should become separate CLIs
- what those CLIs should be named
- whether shared code should be extracted into distinct modules before any CLI split
- how a future control-oriented CLI should relate to conductor, evaluator, or review-loop systems

These are valid future questions, but they should be evaluated after the current artifact-oriented hardening and model-refresh work has been validated.

### 13. Model Upgrades Should Be Evaluated in Terms of Trust Boundary Compression, Not Only Raw Quality

GPT-5-series structured-output support may reduce formatting and contract-adherence failures compared with older `gpt-4o`-family prompt defaults.

That should be evaluated empirically.

But even if a newer model substantially improves contract adherence, the architecture should not collapse the distinction between:

- "better at returning schema-shaped data"
- "safe to treat as deterministic semantic control state"

The second claim remains out of scope for the base `tnh-gen` contract.

---

## Consequences

### Positive

- Makes the system's trust model explicit rather than implied.
- Preserves the value of structured outputs without overstating what they guarantee.
- Reduces the risk that future orchestration layers accidentally encode control logic inside rich AI artifacts.
- Provides a cleaner design language for evaluator-style workflows and future conductor integrations.
- Aligns current runtime behavior with a more honest contract vocabulary.
- Creates a principled basis for comparing `gpt-4o`-family and GPT-5-family structured-output behavior.
- Avoids normalizing malformed model output into apparently healthy machine state.

### Negative

- Introduces more conceptual categories for prompt and workflow authors to understand.
- May require some existing or planned prompt outputs to be split into artifact and control variants rather than one mixed-purpose payload.
- Raises the bar for using model output in branching logic, which may slow some workflow experiments.
- Makes some prompt schemas feel "over-constrained" when authors want one payload to do both reporting and routing.
- Removing schema-echo repair may cause some currently tolerated runs to fail until prompts, schemas, or model choices are improved.

---

## Alternatives Considered

### 1. Treat Validated JSON Output as Ordinary Program State

Rejected because structural validation alone does not justify semantic trust. Recent golden evaluation already shows that schema-valid payloads may still contain model-specific contamination or interpretation risk.

### 2. Silently Repair Schema-Echo Contamination into Success

Rejected because it moves malformed model output across the transport boundary as if it were a valid maintained contract result. Hidden repair obscures provider behavior, weakens evaluation, and creates an unreliable precedent for future control-surface work.

### 3. Reject Structured Outputs for Anything Other Than Human Display

Rejected because modern structured-output support is too useful to ignore. Typed containers, local validation, and explicit failure mapping materially improve reliability for many machine-assisted workflows.

### 4. Rely Entirely on Provider-Native Strict Structured Output

Rejected because:

- supported schema subsets are narrower than the repo's current contract needs
- provider-native constraints do not replace local validation and failure taxonomy
- a single-provider guarantee should not fully define the TNH Scholar architectural contract

### 5. Let Rich Artifact Payloads Drive Control Flow Informally

Rejected because it blurs the boundary between content generation and deterministic orchestration, making the system harder to reason about, test, and debug.

---

## Open Questions

1. **Deferred**: Prompt metadata should eventually declare whether a JSON contract is an `artifact` contract or a `control` contract, enabling tooling and catalog health checks to surface control-surface risk. This is deferred pending prompt metadata design work.
2. Should `tnh-gen` expose stricter operator-visible signals when a prompt schema is outside the provider's strict structured-output subset?
3. Should future evaluator prompts require explicit closed schemas with abstain states before they are allowed to influence workflow routing?
4. Should the prompt catalog health view report control-surface risk separately from ordinary schema validity?
5. Should maintained JSON prompt defaults move from `gpt-4o` / `gpt-4o-mini` to GPT-5-family models after a comparative golden evaluation?
6. Which maintained artifact schemas can be tightened enough to fit stronger provider-constrained structured-output modes without losing needed expressiveness?
7. After near-term hardening, does the operator and consumer experience still justify one shared CLI surface, or is a dedicated control-oriented CLI warranted?

---

## References

- [ADR-TG04: Structured JSON Contract and Scope Boundaries](/architecture/tnh-gen/adr/adr-tg04-structured-json-contract-and-scope.md)
- [ADR-TG04.1: JSON Contract Runtime Validation](/architecture/tnh-gen/adr/adr-tg04.1-json-contract-runtime-validation.md)
- [ADR-TG04.2: Structured JSON Provenance Sidecars](/architecture/tnh-gen/adr/adr-tg04.2-structured-json-provenance-sidecars.md)
- OpenAI Structured Outputs guide (platform.openai.com): <https://developers.openai.com/api/docs/guides/structured-outputs>
- OpenAI Responses API migration guide (platform.openai.com): <https://developers.openai.com/api/docs/guides/migrate-to-responses>
- OpenAI Models overview (platform.openai.com): <https://developers.openai.com/api/docs/models>
