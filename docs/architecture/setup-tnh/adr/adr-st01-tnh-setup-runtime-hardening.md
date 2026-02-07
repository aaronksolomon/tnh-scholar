---
title: "ADR-ST01: tnh-setup Runtime Hardening"
description: "Harden tnh-setup to ensure yt-dlp runtime readiness and clearer environment verification."
owner: "aaronksolomon"
author: "Codex"
status: proposed
created: "2026-02-02"
---
# ADR-ST01: tnh-setup Runtime Hardening

Improve tnh-setup to deliver out-of-the-box robustness for CLI tools, with explicit runtime setup and verification for yt-dlp dependencies.

- **Status**: Proposed
- **Date**: 2026-02-02
- **Owner**: aaronksolomon
- **Authors**: Codex

## Context

TNH Scholar CLI tools (notably `ytt-fetch` and `audio-transcribe`) depend on yt-dlp, which increasingly requires external runtime support (JS runtimes and `curl_cffi`) to avoid SABR and bot detection failures. Current user experience requires manual environment setup and troubleshooting, which undermines the goal of “out-of-the-box robust” tooling with minimal user intervention. The project permits breaking changes in 0.x releases, so we can optimize for clarity and reliability rather than backwards compatibility.

## Decision

1. **Harden `tnh-setup` for runtime readiness**
   - Integrate a guided yt-dlp runtime setup step (JS runtime + `curl_cffi`).
   - Provide explicit environment verification output after setup.
   - Emit clear warnings when verification fails.

2. **Standardize runtime setup tooling**
   - Add a dedicated runtime setup script in `scripts/setup_ytdlp_runtime.py`.
   - Add a Makefile target `make ytdlp-runtime` and invoke it from `make build-all`.
   - Write `~/.config/yt-dlp/config` with an absolute JS runtime path to avoid PATH fragility.

3. **Enforce preflight validation in `ytt-fetch`**
   - Always verify runtime prerequisites before running.
   - Fail fast with actionable guidance if prerequisites are missing.

4. **Typer migration plan for `tnh-setup`**
   - Adopt Typer for a clearer CLI UX and more structured help text.
   - Backwards compatibility is not required for this phase.

## Consequences

**Positive**
- Users get reliable CLI behavior without manual environment tailoring.
- Failures surface early with clear remediation steps.
- yt-dlp runtime stability increases via explicit config and dependency checks.

**Negative**
- Slightly more setup time during `tnh-setup`.
- Additional moving parts (script + config file) to maintain.

## Alternatives Considered

- **Keep setup minimal**: Rejected due to frequent yt-dlp breakage and poor UX.
- **Rely on README-only guidance**: Rejected as too passive for reliable ops.

## Open Questions

- Should `audio-transcribe` enforce the same preflight validation as `ytt-fetch`?
- Should we add a non-interactive `--yes/--no-input` default for setup automation?

---

## As-Built Notes & Addendums

*None.*
