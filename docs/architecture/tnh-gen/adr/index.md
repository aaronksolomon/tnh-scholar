---
title: "Adr"
description: "Table of contents for architecture/tnh-gen/adr"
owner: ""
author: ""
status: current
created: "2026-05-05"
auto_generated: true
---

# Adr

**Table of Contents**:

<!-- To manually edit this file, update the front matter and keep `auto_generated: true` to allow regeneration. -->

**[ADR-TG01: tnh-gen CLI Architecture](adr-tg01-cli-architecture.md)** - Core command structure, error handling, and configuration for the unified TNH Scholar CLI tool

**[ADR-TG01.1: Human-Friendly CLI Defaults with --api Flag](adr-tg01.1-human-friendly-defaults.md)** - Default to human-readable output for CLI usage, with --api flag for machine-readable contract output

**[ADR-TG02: TNH-Gen CLI Prompt System Integration](adr-tg02-prompt-integration.md)** - Integration pattern for tnh-gen CLI with prompt system via PromptsAdapter

**[ADR-TG03: Typed Completion Outcome and Adapter Diagnostics](adr-tg03-completion-contract.md)** - Normalize transport failure states into a typed domain outcome envelope and structured adapter diagnostics for observable, reliable generation results

**[ADR-TG04: Structured JSON Contract and Scope Boundaries](adr-tg04-structured-json-contract-and-scope.md)** - Define tnh-gen as a prompt-agnostic execution substrate, separate it from higher-level semantic processing and orchestration, and establish the scope for structured JSON contracts.

**[ADR-TG04.1: JSON Contract Runtime Validation](adr-tg04.1-json-contract-runtime-validation.md)** - Define the runtime contract for resolving schema_ref, validating JSON prompt outputs, mapping failures, and serializing structured results in tnh-gen.

**[ADR-TG04.2: Structured JSON Provenance Sidecars](adr-tg04.2-structured-json-provenance-sidecars.md)** - Clarify how tnh-gen preserves first-class provenance for structured JSON outputs without violating JSON artifact purity.

**[ADR-TG04.3: Structured Output Trust Boundaries and Control Surfaces](adr-tg04.3-structured-output-trust-boundaries.md)** - Define how tnh-gen and downstream consumers should treat model-produced structured data, distinguish artifact contracts from control contracts, and prefer deterministic control outside AI-generated payloads.

---

*This file auto-generated.*
