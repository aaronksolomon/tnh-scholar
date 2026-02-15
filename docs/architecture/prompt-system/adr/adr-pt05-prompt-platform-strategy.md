---
title: "ADR-PT05: Prompt Platform Strategy"
description: "Establishes TNH Scholar's prompt platform architecture for multi-module prompt libraries, schema layering, and robust client integration."
owner: "aaronksolomon"
author: "GPT-5 Codex, Aaron Solomon"
status: wip
created: "2026-02-15"
related_adrs:
  - "adr-pt04-prompt-system-refactor.md"
  - "adr-cf02-prompt-catalog-discovery.md"
  - "adr-os01-object-service-architecture-v3.md"
  - "adr-a12-prompt-system-fingerprinting-v1.md"
  - "adr-oa05-prompt-library-specification.md"
  - "adr-oa06-planner-evaluator-contract.md"
---

# ADR-PT05: Prompt Platform Strategy

Establishes TNH Scholar's prompt platform architecture for multi-module prompt libraries, schema layering, and robust client integration.

- **Status**: WIP
- **Type**: Strategy ADR
- **Date**: 2026-02-14
- **Owner**: Aaron Solomon
- **Author**: GPT-5 Codex, Aaron Solomon

---

## ADR Editing Policy

**IMPORTANT**: How you edit this ADR depends on its status.

- **`proposed` status**: ADR is in the design loop. We may **rewrite** or edit the document as needed to refine the design.
- **`accepted`, `wip`, `implemented` status**: Implementation has begun or completed. **NEVER edit** the original Context/Decision/Consequences sections. Only append addendums.

---

## Context

Prompt usage in TNH Scholar has expanded from a single primary flow to multiple subsystem needs:

- GenAI end-to-end generation (`tnh-gen`, `gen_ai_service`)
- Agent orchestration (`RUN_AGENT`, `EVALUATE`, policy/gate paths)
- Translation, summarization, review, and other domain-specific modules
- Future subsystems not yet defined

The current system has useful foundations but also structural pressure:

1. Prompt schemas are not yet unified across use cases.
2. Catalog key semantics are effectively flat in key lookup paths, which conflicts with namespace growth.
3. Client responsibilities are not fully standardized around one platform contract.
4. Prompt contracts are not compile-validated end-to-end against workflow and evaluator schemas.

Without a platform-level strategy, prompt libraries will fragment by subsystem and create incompatible contracts.

The Prompt Platform is a peer infrastructure subsystem within TNH Scholar. It is not subordinate to, nor defined by, any specific consumer. All consuming systems are treated as equal clients of the platform.

---

## Decision

### 1. Adopt a Prompt Platform Architecture

TNH Scholar will treat prompt management as a **shared platform subsystem** with multiple clients.

Platform responsibilities:

- Prompt catalog discovery and resolution
- Prompt metadata and contract schema validation
- Template rendering and safety constraints
- Fingerprint/provenance support
- Compatibility and version lifecycle policy

Client responsibilities:

- Context assembly for rendering
- Execution of rendered prompts (CLI runner, GenAI provider, evaluator)
- Consumption of structured outputs in client-specific workflows

### 1a. Object-Service Contract (OS01 Alignment)

The prompt platform MUST conform to [ADR-OS01](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md):

- Domain layer defines protocols and canonical models only.
- Infrastructure layer implements adapters, mappers, and transport clients.
- `Config` is provided at initialization; `Params` are provided per call.
- `Settings` are environment/application-level only.
- `Policy` models define behavior toggles/precedence; they are not ad-hoc literals in service logic.
- Prompt clients consume typed response envelopes/typed result objects, not untyped dictionaries.

Required platform taxonomy:

| Concept | Prompt Platform Form |
|---------|----------------------|
| Settings | `PromptPlatformSettings` (`BaseSettings`) |
| Config | `PromptCatalogConfig`, transport configs |
| Params | `RenderParams`, `CatalogQueryParams`, validation params |
| Policy | Render policy, validation policy, compatibility policy |
| Domain Protocols | `PromptCatalogPort`, `PromptRendererPort`, `PromptValidatorPort` |
| Adapters/Mappers | catalog adapters + key/path + metadata mappers |

### 2. Standardize Schema Layering

Prompt schemas will be layered into two levels.

#### A. Platform Envelope Schema

A canonical prompt envelope schema (target: `prompt_manifest.v2`) defines shared fields:

- identity: `prompt_id`, `version`, namespace key
- classification: `role`, capabilities, tags
- output contract declaration (`output_contract`)
- optional contract references: `input_contract_ref`, `output_contract_ref`
- lifecycle metadata: status, owner, deprecation

Role taxonomy note:

- The platform validates that `role` is present.
- Valid role sets are namespace-scoped and defined by namespace contracts (for example, agent-orchestration OA05 defines its role set).

#### B. Use-Case Contract Schemas

Use-case schemas define specific input/output contracts and evolve independently, for example:

- `planner_decision.v1`
- `planner_evidence.v1`
- `translation_output.v1`
- `summary_output.v1`

Rule:

- Every prompt MUST satisfy the platform envelope schema.
- Use-case contract schemas are optional at the platform level, but when referenced by prompt output mode rules they are enforced uniformly.

Schema lineage note:

- `prompt_manifest.v2` is intentional: it denotes the platform envelope that supersedes the current legacy v1-era prompt metadata shape implemented through PT04/A12-era models.
- This ADR uses `v2` to distinguish the new platform envelope contract from existing legacy metadata contracts already in active use.

### 2a. Output Modes (Explicit and Lightweight)

The platform supports three output modes:

1. `text` (default unstructured):
   - `output_contract: { mode: "text" }`
   - No `schema_ref` required.
2. `json` (structured JSON):
   - `output_contract: { mode: "json", schema_ref: "..." }`
   - `schema_ref` is REQUIRED.
3. `artifacts` (artifact-producing prompts):
   - `output_contract: { mode: "artifacts", artifacts: [...] }`
   - `artifacts` list is REQUIRED.
   - Artifact declarations must be structurally valid; semantic interpretation is client-defined.

The platform does not assume JSON output for all prompts.

### 2b. Input Strictness Levels

Input declarations support two strictness levels:

- `loose`:
  - Input fields are informational.
  - Partial binding allowed.
- `strict`:
  - Inputs declared `required: true`.
  - Must be satisfiable at compile or render time by platform validation.

Platform enforcement:

- Declared strictness MUST be enforced by platform validators.
- `required: true` is always enforced by platform validators.

### 2c. Normative Platform Rules

- Every prompt MUST validate against the envelope schema.
- `output_contract` MUST exist for every prompt, but may be minimal.
- Contract schema references are optional at platform level.
- Platform compile validation behavior is uniform across all clients.
- Platform guarantees structural correctness; clients own behavioral and workflow semantics.

### 3. Namespace-First Catalog Model

The platform will support namespace-oriented prompt libraries via subdirectory keys.

Canonical key model:

- `canonical_key` is path-relative and excludes version suffixes.
- `version` is a separate envelope field.
- Immutable reference form is derived as: `<canonical_key>.v<version>`.
- Example:
  - `canonical_key`: `agent-orch/planner/evaluate_harness_report`
  - `version`: `1`
  - immutable reference: `agent-orch/planner/evaluate_harness_report.v1`

Directory model (illustrative):

```text
prompts/
  core/
    task/
    policy/
  agent-orch/
    planner/
    task/
    policy/
  translation/
    task/
    eval/
```

Rules:

- Duplicate canonical keys are forbidden.
- Filename-stem-only lookup is deprecated.
- Key-to-path and path-to-key mappers must be bijective.

### 4. Multi-Client Integration Contract

Prompt clients must use platform contracts instead of re-implementing prompt semantics.

Example client categories (non-exhaustive):

- `gen_ai_service`: provider-routed prompt execution and provenance
- Agent orchestration: workflow-level prompt composition and evaluation
- Application modules (translation, summarization, review, etc.)
- Future subsystems integrating prompt-driven logic

Each client may define additional policy and params layers, but cannot bypass platform schema validation.
Each client integration must be expressed through protocol boundaries and typed adapters.

### 5. Validation and Compile Gates

Validation is required at three layers.

#### Layer 1: Prompt Artifact Validation

- Frontmatter/envelope validity
- Template syntax validity
- Output contract mode validity
- Contract reference validity when present

#### Layer 2: Catalog Integrity Validation

- Key uniqueness
- Namespace policy checks
- Version lifecycle checks (current/deprecated/archived)

#### Layer 3: Client Compile Validation

- Referenced prompt keys exist.
- Declared output mode is structurally valid.
- Declared `schema_ref` exists when `mode: "json"`.

Clients may perform additional validation internally, but platform compile validation behavior does not branch per client.

**Future expansion note (post-MVP):**

- If platform-level client options are later needed (for example, profile-based compile gates or optional strictness tiers), they must be introduced as an explicit ADR addendum or decimal follow-on ADR.
- Any such expansion must preserve deterministic default behavior and avoid per-client branching by default.

### 6. Compatibility and Evolution Policy

Compatibility policy:

- Envelope schema evolves with explicit versioning (`v2`, future `v3`).
- Contract schemas evolve per use case (`x.y` version policy per domain).
- Breaking prompt behavior requires new prompt version.

Migration policy:

- Legacy prompt schema remains supported temporarily via adapter compatibility mode.
- New feature development targets envelope `v2` only.
- Removal of legacy mode follows explicit deprecation window and ADR addendum.

### 7. Robustness and Safety Requirements

The prompt platform must enforce:

- deterministic rendering for identical inputs
- strict required-input handling (or explicit policy override)
- no arbitrary template-time filesystem imports
- auditable prompt fingerprint/provenance linkage
- typed, actionable validation errors

### 8. Governance and Ownership

Governance model:

- Envelope schema ownership is centralized.
- Namespaces own their use-case contract schemas.
- Cross-namespace breaking changes require an ADR update.
- Governance remains intentionally lightweight at MVP stage.

---

## Consequences

### Positive

- Enables prompt reuse across peer subsystems without coupling any client to another client’s execution semantics.
- Supports extension via namespaced subdirectories and contract schemas.
- Avoids early schema explosion by requiring only envelope-level constraints platform-wide.
- Reduces enforcement variability and configuration branches in MVP.
- Improves robustness through explicit validation gates and compatibility rules.
- Reduces prompt drift with versioned schemas and lifecycle governance.

### Negative

- Introduces additional up-front design and migration work.
- Raises authoring burden for prompt metadata and contracts.
- Requires updates to current key mapping and catalog adapters.

---

## Alternatives Considered

### A. Separate prompt systems per subsystem

Rejected: duplicates infrastructure, fragments standards, and increases maintenance cost.

### B. Keep a flat prompt namespace

Rejected: does not scale for module growth and creates collision risk.

### C. Runtime-only validation

Rejected: defers failures too late; compile-time validation is needed for robust orchestration and module safety.

---

## MVP Resolutions

The following questions are resolved for MVP:

1. Namespace registration uses inferred directory layout (no explicit namespace manifest in MVP).
2. Contract schemas are colocated per namespace in MVP.
3. Legacy prompt metadata compatibility mode targets removal after one minor version cycle.

Versioning policy alignment:

- TNH Scholar 0.x policy allows immediate breaking changes and immediate removals.
- The one-minor-cycle window above is a scoped prompt-platform migration choice for internal schema compatibility mode, not a global compatibility guarantee.

---

## Implementation Strategy (Phased)

### Phase 1: Platform Contract Foundations

- Define `prompt_manifest.v2` and canonical key grammar.
- Implement path-relative key mapping and collision checks.
- Add compatibility adapter for legacy prompt metadata.
- Define typed domain models/protocols for manifest + contract references.

### Phase 2: Validation Pipeline

- Add artifact, catalog, and client compile validators.
- Introduce schema validation CI checks for prompts and contract refs.
- Add deterministic fixture sets for planner/task/policy prompts.
- Ensure validation services emit typed result models (errors/warnings/envelope), not raw dict payloads.

### Phase 3: Client Alignment

- Align `gen_ai_service` prompt adapter with platform keys and envelope schema.
- Align agent orchestration OA05/OA06 references with platform contract refs.
- Add module namespace onboarding guide for new subsystem prompt libraries.
- Add explicit mappers at client boundaries where client transport/domain shapes differ.

### Phase 4: Legacy Retirement

- Mark legacy key semantics deprecated.
- Remove stem-based lookup paths after migration window.
- Promote platform-only mode as default and documented standard.

---

## Related ADRs

- [ADR-PT04: Prompt System Refactor Plan (Revised)](/architecture/prompt-system/adr/adr-pt04-prompt-system-refactor.md)
- [ADR-CF02: Prompt Catalog Discovery Strategy](/architecture/configuration/adr/adr-cf02-prompt-catalog-discovery.md)
- [ADR-OS01: Object-Service Architecture v3](/architecture/object-service/adr/adr-os01-object-service-architecture-v3.md)
- [ADR-A12: Prompt System & Fingerprinting Architecture (V1)](/architecture/gen-ai-service/adr/adr-a12-prompt-system-fingerprinting-v1.md)
- [ADR-OA05: Prompt Library Specification](/architecture/agent-orchestration/adr/adr-oa05-prompt-library-specification.md)
- [ADR-OA06: Planner Evaluator Contract](/architecture/agent-orchestration/adr/adr-oa06-planner-evaluator-contract.md)
