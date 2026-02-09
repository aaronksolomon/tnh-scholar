---
title: "Adr"
description: "Table of contents for architecture/gen-ai-service/adr"
owner: ""
author: ""
status: processing
created: "2026-02-09"
auto_generated: true
---

# Adr

**Table of Contents**:

<!-- To manually edit this file, update the front matter and keep `auto_generated: true` to allow regeneration. -->

**[ADR-A01: Adopt Object-Service for GenAI Interactions](adr-a01-object-service-genai.md)** - Standardizes GenAI interactions with an Object-Service pattern that separates domain shapes from provider orchestration.

**[ADR-A02: PatternCatalog Integration (V1)](adr-a02-patterncatalog-integration-v1.md)** - Describes the V1 contract for plugging the legacy PatternCatalog into GenAI Service via rendered system prompts.

**[ADR-A08: Configuration / Parameters / Policy Taxonomy](adr-a08-config-params-policy-taxonomy.md)** - Establishes the Config/Params/Policy taxonomy for GenAI Service to prevent parameter soup and clarify ownership.

**[ADR-A09: V1 Simplified Implementation Pathway](adr-a09-v1-simplified.md)** - Defines the minimum viable GenAI Service implementation that preserves architectural seams while shipping quickly.

**[ADR-A11: Model Parameters and Strong Typing Fix](adr-a11-model-parameters-fix.md)** - Enforces typed parameter objects and removes literals from GenAI Service so provider flows stay consistent.

**[ADR-A12: Prompt System & Fingerprinting Architecture (V1)](adr-a12-prompt-system-fingerprinting-v1.md)** - Replaces the Pattern Catalog adapter with a Prompt-first design that yields domain objects plus fingerprints.

**[ADR-A13: Migrate All OpenAI Interactions to GenAIService](adr-a13-migrate-openai-to-genaiservice.md)** - Retires the legacy OpenAI client and standardizes every caller on the typed GenAI Service pipeline.

**[ADR-A14: File-Based Registry System for Provider Metadata](adr-a14-file-based-registry-system.md)** - Establishes a JSONC-based registry system for model capabilities, pricing, and provider metadata with auto-update mechanisms, aligned with VS Code's native configuration format.

**[ADR-A14.1: Registry Staleness Detection and User Warnings](adr-a14.1-registry-staleness-detection.md)** - Implements staleness detection for OpenAI pricing data with configurable warnings and CLI tooling

**[ADR-A15: Thread Safety and Rate Limiting](adr-a15-thread-safety-rate-limiting.md)** - Implements thread-safe GenAIService operations and provider-aware rate limiting for concurrent and batch processing scenarios.

---

*This file auto-generated.*
