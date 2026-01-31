---
title: "ADR-JVB02: JVB VS Code Parallel Viewer Strategy"
description: "Strategy ADR for integrating the JVB parallel viewer into the tnh-scholar VS Code extension, enabling scholarly review of scanned journal pages with OCR reconciliation and translation editing."
owner: "phapman"
author: "Claude Opus 4.5"
status: proposed
created: "2026-01-28"
type: strategy
related_adrs: ["adr-jvb01_as-built_jvb_viewer_v1.md", "adr-vsc01-vscode-integration-strategy.md"]
---

# ADR-JVB02: JVB VS Code Parallel Viewer Strategy

Strategy for integrating the JVB (Journal of Vietnamese Buddhism) parallel viewer into the tnh-scholar VS Code extension, enabling scholarly review of scanned historical journal pages alongside OCR text and English translations.

- **Status**: Proposed
- **Date**: 2026-01-28
- **Owner**: Aaron Solomon
- **Author**: Claude Opus 4.5
- **Tags**: strategy, vscode, jvb, viewer, ocr, translation

---

## ADR Editing Policy

**IMPORTANT**: This ADR is in `proposed` status. It may be rewritten or edited as needed to refine the design. Once moved to `accepted`, only addendums may be appended.

---

## Context

### Background

The JVB (Journal of Vietnamese Buddhism / Phật Giáo Việt Nam) corpus consists of scanned historical journal pages from the 1950s requiring:

1. **OCR text extraction** from Vietnamese script (diacritics-heavy)
2. **Translation** to English for accessibility
3. **Scholarly review** to reconcile OCR errors and refine translations
4. **Structural annotation** (sections, headings, articles)

### Previous Work

**v1 Browser Prototype** ([ADR-JVB01](/architecture/jvb-viewer/adr/adr-jvb01_as-built_jvb_viewer_v1.md)):

- Flask server + custom HTML/JS viewer
- 4-pane layout: scan image, EN text, VI text, section navigation
- Page synchronization via HTML anchors
- **Limitation**: Bespoke UI required significant engineering effort; maintenance burden high

**v2 Strategy Draft** ([JVB Viewer V2 Strategy](/architecture/jvb-viewer/design/jvb-viewer-v2-strategy.md)):

- Proposed projection-first architecture with per-page JSON as canonical artifact
- Overlay viewer concept (text positioned over scan images)
- Dual OCR source reconciliation (Google OCR vs AI vision)
- **Status**: Draft, paused pending VS Code integration foundation

### Current State

The VS Code integration foundation is now complete:

- **tnh-gen CLI**: Unified CLI for GenAI operations ([ADR-TG01](/architecture/tnh-gen/adr/adr-tg01-cli-architecture.md))
- **VS Code Extension Walking Skeleton**: Basic prompt execution working ([ADR-VSC01](/architecture/ui-ux/vs-code-integration/adr-vsc01-vscode-integration-strategy.md))
- **VS Code as Platform Strategy**: Established direction for all TNH Scholar UIs ([VS Code as UI Platform](/architecture/ui-ux/design/vs-code-as-ui-platform.md))

This ADR formalizes the JVB viewer integration into the VS Code extension, building on the v2 strategy concepts.

---

## Decision

### Core Principles

1. **Projection-First Architecture**: Per-page JSON is the canonical artifact; all views (overlay, side-by-side, export) are projections
2. **VS Code Native**: Leverage VS Code's extension APIs (webviews, custom editors, panels) rather than external browser apps
3. **Dual-Source Reconciliation**: First-class support for comparing/choosing between OCR sources (Google OCR vs AI vision)
4. **Incremental Review**: Enable sentence-by-sentence review workflow with status tracking (draft → reviewed → final)

### High-Level Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                    VS Code Extension                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────────────────┐   │
│  │   JVB Viewer        │  │   Control Panel                 │   │
│  │   (Custom Editor    │  │   (Bottom Panel or Sidebar)     │   │
│  │    or Webview)      │  │                                 │   │
│  │                     │  │   - OCR Source Chooser          │   │
│  │   - Scan Image      │  │   - Translation Editor          │   │
│  │   - Text Overlay    │  │   - Status Controls             │   │
│  │   - Sentence Select │  │   - Navigation                  │   │
│  └─────────────────────┘  └─────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                     Per-Page JSON Files                         │
│                  (Git-tracked, small diffs)                     │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions (To Be Refined in Sub-ADRs)

#### 1. Viewer Implementation Approach

**Options under consideration**:

- **Custom Editor Provider**: Register for `.jvb.json` files, full editor integration
- **Webview Panel**: Standalone panel opened via command, more flexible
- **Hybrid**: Custom editor for viewing, panel for controls

**Decision**: TBD in [ADR-JVB02.1](/architecture/jvb-viewer/adr/adr-jvb02.1-ui-ux-design.md)

#### 2. Pane Layout Strategy

**Options under consideration**:

- **Single webview with split layout**: All UI in one webview (simpler state management)
- **Editor + Bottom Panel**: Main viewer in editor area, controls in bottom panel
- **Editor + Sidebar**: Main viewer in editor area, navigation/controls in sidebar

**Decision**: TBD in [ADR-JVB02.1](/architecture/jvb-viewer/adr/adr-jvb02.1-ui-ux-design.md)

#### 3. Data Model

Build on v2 strategy's per-page JSON format with refinements:

- Word-level bounding boxes for precise overlay positioning
- Sentence groupings with `word_ids` references
- Dual `sources[]` array for OCR alternatives
- `chosen` field for reconciliation decisions
- `status` field for review workflow tracking

**Full schema**: TBD in [ADR-JVB02.2](/architecture/jvb-viewer/adr/adr-jvb02.2-data-model-api-contract.md)

#### 4. Backend Integration

**Options under consideration**:

- **File-only**: Extension reads/writes JSON directly, no backend service
- **tnh-gen CLI**: Use existing CLI for OCR processing, AI translation
- **Dedicated HTTP service**: FastAPI service for heavy operations (future)

**Initial approach**: File-only for viewing/editing; tnh-gen CLI for AI operations

### Sub-ADR Structure

This strategy ADR is supported by detailed sub-ADRs:

| ADR | Type | Scope |
|-----|------|-------|
| **ADR-JVB02.1** | `design-detail` | UI-UX design: mockups, pane layouts, user workflows |
| **ADR-JVB02.2** | `design-detail` | Data model: JSON schema, API contracts |
| **ADR-JVB02.3** | `implementation-guide` | Phase-by-phase implementation plan |

### Implementation Milestones

Adapted from v2 strategy, refined for VS Code integration:

- **M0 (Prototype)**: Static HTML mockup in VS Code webview — validate overlay rendering approach
- **M1 (Core Viewer)**: Load per-page JSON, render overlay on scan image, basic navigation
- **M2 (Reconciliation UI)**: Dual-source diff view, source chooser, status controls
- **M3 (Full Workflow)**: Section navigation, translation editing, batch operations
- **M4 (Beta)**: Export capabilities, theming, performance optimization

---

## Consequences

### Positive

- **Leverages existing investment**: Builds on VS Code extension foundation and tnh-gen CLI
- **Git-native workflow**: Per-page JSON enables small diffs, PR-based review
- **Familiar environment**: Scholars comfortable with VS Code can adopt quickly
- **Incremental delivery**: Walking skeleton approach allows early validation

### Negative

- **VS Code dependency**: Users must install VS Code (mitigated by vscode.dev for light use)
- **Webview complexity**: Custom rendering in webviews requires careful state management
- **Learning curve**: Extension development requires TypeScript/VS Code API knowledge

### Risks

- **Webview performance**: Large scan images + many word bboxes may impact rendering
- **State synchronization**: Keeping webview state in sync with JSON files
- **OCR quality**: Viewer success depends on upstream OCR quality

---

## Alternatives Considered

### 1. Continue with Browser-Based Viewer

**Rejected**: High maintenance burden, diverges from VS Code platform strategy, duplicates effort.

### 2. Electron Standalone App

**Rejected**: Adds deployment complexity, loses VS Code ecosystem benefits, harder to maintain.

### 3. Web-Only (vscode.dev)

**Deferred**: Web extension support is limited; start with desktop, add web later.

---

## Open Questions

1. **Custom Editor vs Webview Panel**: Which approach better fits the review workflow?
2. **State persistence**: How to handle unsaved changes, dirty state indicators?
3. **Multi-page navigation**: Side-by-side page comparison? Thumbnail strip?
4. **Keyboard shortcuts**: What shortcuts optimize the reconciliation workflow?
5. **Accessibility**: How to make the overlay viewer accessible (screen readers)?
6. **Collaboration**: Future Live Share integration for multi-user review?

---

## Historical References

<details>
<summary>View superseded design documents (maintainers/contributors)</summary>

### Earlier Design Explorations

- **[JVB Viewer V2 Strategy](/architecture/jvb-viewer/design/jvb-viewer-v2-strategy.md)** (2025-09-19)
  *Status*: Draft strategy note, foundational concepts incorporated into this ADR

- **[ADR-JVB01: JVB Parallel Viewer v1 As-Built](/architecture/jvb-viewer/adr/adr-jvb01_as-built_jvb_viewer_v1.md)** (2025-12-12)
  *Status*: Documents browser-based v1 prototype (not superseded, historical reference)

</details>
