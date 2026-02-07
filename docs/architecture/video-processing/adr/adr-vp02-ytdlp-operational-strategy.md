---
title: "ADR-VP02: yt-dlp Operational Strategy"
description: "Operational strategy for yt-dlp coupling, runtime injection, and continuous testing."
owner: "aaronksolomon"
author: "aaronksolomon, Codex, Claude Code"
status: proposed
created: "2026-02-06"
---
# ADR-VP02: yt-dlp Operational Strategy

Define how TNH Scholar stays robust while tightly coupled to yt-dlp’s evolving YouTube extraction behavior.

- **Status**: Proposed
- **Date**: 2026-02-04
- **Owner**: aaronksolomon
- **Authors**: aaronksolomon, Codex, Claude Code

> **Note**: This is a strategy ADR defining operational policy. It does not prescribe specific implementation details.

## Context

TNH Scholar's YouTube tooling depends on yt-dlp, which changes frequently in response to YouTube platform updates. This creates an ongoing reliability risk that cannot be avoided without official APIs (which are unavailable for most public videos). We need a repeatable, low-friction operational strategy that keeps tooling stable while accepting ongoing upstream churn.

We accept upstream churn and prioritize **observability**, **diagnosability**, and **rapid recovery** over permanent immunity.

## Decision

1. **Tight coupling with explicit runtime injection**
   - Keep yt-dlp as the primary backend.
   - Inject runtime options directly into yt-dlp calls (e.g., `js_runtimes`, `remote_components`) instead of relying on implicit config behavior.

2. **Single-source runtime setup**
   - Maintain a dedicated runtime setup tool (`scripts/setup_ytdlp_runtime.py`) to install JS runtimes, `curl_cffi`, and write yt-dlp config.
   - Ensure setup supports both pipx and dev environments with clear failure messages.

3. **Continuous validation**
   - Maintain live integration tests driven by a small URL list.
   - Run a scheduled weekly ops test (local cron) to surface breakage early.

4. **Operational diagnostics**
   - On failure, surface yt-dlp version, runtime availability, and remote component configuration in the CLI output or logs.
   - Keep diagnostic output consistent across `ytt-fetch` and `audio-transcribe` workflows.
   - Both `ytt-fetch` and `audio-transcribe` enforce the same preflight checks and diagnostics for consistency.

5. **Validation URL strategy**
   - Maintain a curated "known-good" URL set with three classes:
     - **Plum Village / TNH ecosystem** (primary realism): Official Plum Village channels representing actual production usage.
     - **Mainstream baseline** (platform realism): Canonical TED talks published ≥10 years ago as YouTube-platform stress tests.
     - **Format diversity**: At least one short video (fast smoke test) and one medium/long video (audio extraction robustness). Avoid Shorts and livestream replays.
   - Store URLs in a single source of truth (test fixture at `tests/fixtures/`).
   - Each validation must verify: metadata extraction succeeds, audio-only download succeeds, output file is non-empty and readable.
   - Governance: rotate URLs quarterly or on repeated failure; keep 2–3 reserve URLs for fast substitution; always use full `watch?v=` URLs.

## Consequences

**Positive:**

- Predictable recovery path when yt-dlp breaks.
- Reduced ambiguity around runtime and config behavior.
- Faster triage with structured diagnostics and scheduled tests.

**Negative:**

- Ongoing maintenance cost (tracking upstream yt-dlp changes).
- Some instability remains unavoidable due to platform changes.

## Alternatives Considered

- **Official YouTube API**: Rejected due to credential constraints and limited access for public videos.
- **Best-effort mode without runtime enforcement**: Rejected due to frequent silent failures and unclear diagnostics.

## Related Documents

- [ADR-VP01: Video Processing Return Types and Configuration](/architecture/video-processing/adr/adr-vp01-video-processing.md) — defines `YTDownloader` abstraction and `DLPDownloader` implementation
- [ytt-fetch CLI Reference](/cli-reference/ytt-fetch.md)
- [audio-transcribe CLI Reference](/cli-reference/audio-transcribe.md)

## Open Questions

*None.*

---

## As-Built Notes & Addendums

### Addendum 1: Validation URL Strategy (2026-02-06)

Decision #5 (Validation URL strategy) added based on cross-agent review. Initial recommended URL set:

**Plum Village (4):**

- "No Way to Happiness, Happiness Is the Way" — `https://www.youtube.com/watch?v=cbYPApa40J0`
- "The Roots of Anger" — `https://www.youtube.com/watch?v=Q_UZCuBuuoU`
- "Stop Running" — `https://www.youtube.com/watch?v=Qch5ISD9Bxo`
- "Self-Respect" — `https://www.youtube.com/watch?v=0yK1p4kz5cs`

**TED (3):**

- "Do Schools Kill Creativity?" (Ken Robinson) — `https://www.youtube.com/watch?v=iG9CE55wbtY`
- "The Power of Vulnerability" (Brené Brown) — `https://www.youtube.com/watch?v=iCvmsMzlF7o`
- "How Great Leaders Inspire Action" (Simon Sinek) — `https://www.youtube.com/watch?v=qp0HIF3SfI4`

**Reserve (curation anchor):**

- Plum Village short-meditation playlist — `https://www.youtube.com/playlist?list=PLHB1Zqu9mBt-eEyT91yZzuMFTI9e0XccO`
