---
title: "ADR-A11: Model Parameters and Strong Typing Fix"
description: "Enforces typed parameter objects and removes literals from GenAI Service so provider flows stay consistent."
owner: ""
author: "Aaron Solomon, GPT-5.0"
status: processing
created: "2025-11-15"
---
# ADR-A11: Model Parameters and Strong Typing Fix

Mandates typed models for all GenAI parameters and forbids literal dict plumbing to align with Config/Params/Policy rules.

**Status:** Proposed  
**Date:** 2025-10-19  
**Author:** Aaron Solomon and GPT-5 (TNH-Scholar project)

---

## Context

During early implementation of the `GenAIService`, hardcoded string literals and ad‑hoc `dict` structures appeared in several layers (notably within provider adapters and pattern rendering). These elements conflicted with the project’s established design principles of strong typing, configuration‑driven behavior, and zero literals in application logic.

This ADR refines the model‑parameter handling strategy to align with **ADR‑A08 (Config Params Policy)** and to enforce consistency between the orchestrator, providers, and policy layers.

---

## Decision

1. All parameters, settings, and payloads exchanged between internal components must use **typed models** rather than `dict` objects.
2. No hardcoded default values or strings will appear within application code paths. Defaults originate from:
   - `Settings` (`pydantic.BaseSettings`) configuration
   - Policy files under `runtime_assets/policies`
   - Pattern metadata (e.g., `model_hint`, `default_params`)
3. All provider communication uses **typed transport models**: `ProviderRequest`, `ProviderResponse`, and `Usage`.
4. All message data uses the strongly‑typed `Message` and `Role` classes.
5. Provider adapters perform the only dict conversions necessary at SDK boundaries.
6. Parameters such as `temperature`, `max_output_tokens`, and `seed` are encapsulated in a typed `ResolvedParams` model derived from ADR‑A08.
7. The orchestrator constructs a `ProviderRequest` from these models; no intermediate dicts are permitted.

---

## Details of Implementation

- **New models**: `ProviderRequest`, `ProviderResponse`, and `Usage` were added to `models/transport.py`.
- **CompletionParams** and **ResolvedParams** models unify configuration and runtime parameters.
- **Provider adapters** (e.g., `OpenAIAdapter`) were refactored to remove literal defaults and use only values passed through typed parameters.
- **SafetyGate**, **PatternCatalog**, and **Service** now reference typed `Message` objects rather than dicts.
- All orchestrator flows depend on `Settings` for defaults and ADR‑A08 policy merges.
- The `Config.ParamsPolicy` merges precedence as: Call → Pattern → Policy → Settings.

---

## Consequences

- Ensures compile‑time and IDE‑level validation of all parameters.
- Reduces configuration drift between environments.
- Improves readability and debugging by eliminating untyped or ad‑hoc dict structures.
- Establishes a consistent contract between service layers (orchestrator ↔ adapter ↔ provider).
- Facilitates future automatic code generation and static analysis.

---

## Related

- **ADR‑A08:** Config Params Policy  
- **ADR‑A09:** Simplified V1 Implementation  
- **Design Guide:** Strong Typing and Abstraction Preferences (Section 1.3)
