---
title: "ADR-TG04.2: Structured JSON Provenance Sidecars"
description: "Clarify how tnh-gen preserves first-class provenance for structured JSON outputs without violating JSON artifact purity."
type: "design-detail"
owner: "aaronksolomon"
author: "Aaron Solomon, OpenAI Codex"
status: accepted
created: "2026-05-01"
parent_adr: "adr-tg04-structured-json-contract-and-scope.md"
related_adrs:
  - "adr-tg04.1-json-contract-runtime-validation.md"
  - "adr-tg01.1-human-friendly-defaults.md"
---
# ADR-TG04.2: Structured JSON Provenance Sidecars

Clarify where provenance lives for structured JSON output artifacts produced by `tnh-gen`.

- **Filename**: `adr-tg04.2-structured-json-provenance-sidecars.md`
- **Status**: Accepted
- **Date**: 2026-05-01
- **Authors**: Aaron Solomon, OpenAI Codex
- **Owner**: aaronksolomon
- **Parent ADR**: [ADR-TG04: Structured JSON Contract and Scope Boundaries](/architecture/tnh-gen/adr/adr-tg04-structured-json-contract-and-scope.md)

---

## Context

ADR-TG04.1 established two requirements that conflict if provenance remains inline:

- structured JSON `--output-file` artifacts must remain canonical JSON text
- provenance is a first-class TNH Scholar concern and should remain durable on disk

The older file-writing convention used YAML frontmatter inline with file content.
That works for text artifacts, but it breaks the ordinary contract of a JSON file.
A JSON artifact that requires TNH-specific frontmatter stripping is no longer a normal JSON artifact.

We want both:

- standard JSON files that downstream tools can parse directly
- retained provenance and source metadata for TNH workflows

---

## Decision

### 1. Structured JSON Output Files Remain Pure JSON

When a prompt output contract is `json`, the primary `--output-file` artifact must contain only canonical JSON text.

No YAML frontmatter or other inline metadata may be prefixed to the JSON artifact.

### 2. Provenance Moves to a Sidecar File

When a structured JSON output is written to disk, provenance is written to a deterministic sidecar YAML file alongside the JSON artifact.

Path rule:

- primary artifact: `<output-path>`
- provenance sidecar: `<output-path>.provenance.yaml`

Examples:

- `sections.json`
- `sections.json.provenance.yaml`

### 3. Sidecar Content Rules

If provenance is enabled, the sidecar stores the same merged metadata that would otherwise have appeared in inline frontmatter:

- TNH Scholar generated markers
- prompt key and prompt version
- model and fingerprint
- trace id and generation timestamp
- preserved source metadata when present

If provenance is disabled but source metadata exists, the sidecar stores the preserved source metadata only.

If neither provenance nor source metadata is present, no sidecar file is written.

### 4. Text Outputs Keep Existing Inline Behavior

This addendum applies only to structured JSON output artifacts.

Text outputs continue using the existing inline frontmatter behavior because text artifacts do not carry the same machine-parseability expectation as JSON files.

---

## Consequences

- JSON artifacts remain standard JSON files and can be consumed by ordinary tooling without custom preprocessing.
- Provenance remains durable and first-class on disk for TNH Scholar workflows.
- Downstream consumers that want both payload and provenance must read two adjacent artifacts instead of one mixed-format file.

---

## Rejected Alternative

### Inline YAML Frontmatter in `.json` Files

Rejected because it redefines a JSON artifact into a TNH-specific pseudo-format and breaks the ordinary expectations of generic JSON tooling, schema validators, editors, and downstream automation.
