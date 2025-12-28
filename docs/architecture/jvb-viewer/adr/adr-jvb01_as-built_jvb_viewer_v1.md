---
title: "ADR-JVB01: JVB Parallel Viewer v1 As-Built"
description: "As-built architecture documentation for JVB parallel viewer v1 bilingual journal interface"
owner: "phapman"
author: "Claude Sonnet 4"
status: "accepted"
created: "2025-12-12"
---

# ADR-JVB01: JVB Parallel Viewer v1 As-Built

As-built architecture documentation for JVB parallel viewer v1 bilingual journal interface.

- **Status:** Accepted (as-built)
- **Date:** 2025-12-12
- **Project:** `jvb-parallel-viewer` (JVB / BJV parallel viewer)
- **Related ADRs:** ADR-003 (bundle as-built), ADR-006 (viewer <-> bundle streamlining)

## Context

The JVB viewer is a lightweight, local web UI for exploring a bilingual journal (VI scan + VI OCR + EN translation) with:

- A **scan/image pane** that shows the original page image.
- A **left text pane** (EN) rendered from an English section AST → HTML.
- A **right text pane** (VI) rendered from Vietnamese OCR text → HTML.
- A **section pane** for navigation by logical sections.
- **Page synchronization** driven by HTML anchors of the form `id="p-<page>"`.

This v1 is the first prototype that aligns the viewer and server around a normalized bundle contract produced by `json_builder3.py`.

## Decision

For v1, we standardized the viewer/server/bundle interface around:

- **Section IDs:** `sid` (e.g., `s:<doc_id>:<NN>`)
- **Page span IDs:** `pid` (e.g., `p:<doc_id>:<page>`)
- **Top-level bundle keys:**
  - `sections` — section index (catalog metadata + per-page spans)
  - `sections_body` — section bodies (EN/VI full text + EN AST + pagination)
  - `route_index` — routing maps between pages and sections
- **Page anchors:** the HTML renderers emit
  - `<div id="p-<N>" class="anchor pagebreak"></div>`
  so the viewer can synchronize panes and the scan image to the correct actual page.

Drift-handling heuristics (e.g., swapping `aid`/`sid` in the viewer) were intentionally removed in favor of a single, explicit contract.

## As-Built Architecture

### Components

- **Bundle Builder:** `json_builder3.py`
  - Produces a single JSON bundle per document
  - Defines the contract used by server + viewer

- **Server:** `app.py`
  - Loads bundle(s) into memory (`STATE`)
  - Exposes a small API for bundle, page routing, and per-section HTML

- **Renderers:** `render.py`
  - `render_en_section(en_ast)` renders EN AST → HTML
  - `render_vi_section(vi_text, target_pages=..., show_headers=...)` renders VI text → HTML with anchors

- **Client:** `templates/doc.html`
  - Fetches `/api/doc/{doc_id}/bundle` once
  - Builds UI navigation from `bundle.sections`
  - Fetches per-section EN/VI HTML
  - Requests per-page scan URL and mapping via `/api/doc/{doc_id}/page/{page}`

### Data Model (Viewer-Facing)

This ADR does not duplicate ADR-003’s full bundle schema; it records the subset *consumed* by v1:

- `bundle.sections[*].sid`
- `bundle.sections[*].title_en`, `title_vi`, `author`, `summary`, `keywords`
- `bundle.sections[*].spans[*].page`, `pid`, `en`, `vi`, `align?`
- `bundle.sections_body[*].sid`
- `bundle.sections_body[*].en_ast`
- `bundle.sections_body[*].vi` (pages separated by `\f`)
- `bundle.sections_body[*].pagination.target_pages`
- `bundle.route_index.section_to_pages[sid] -> [page...]`
- `bundle.route_index.page_to_section[str(page)] -> sid`
- `bundle.mapping.offset`, `bundle.mapping.overrides`
- `bundle.pages_count`

### API Surface (v1)

#### Bundle

`GET /api/doc/{doc_id}/bundle`

Returns a normalized payload (server may internally fall back to legacy keys but should emit normalized keys):

- `doc_id`, `title`
- `pages_count`
- `mapping`: `{ offset, overrides }`
- `route_index`: `{ section_to_pages, page_to_section }`
- `sections`: `[SectionIndex]`
- `sections_body`: `[SectionBody]`

#### Page routing + scan image

`GET /api/doc/{doc_id}/page/{page}`

Returns:

- `page` (actual)
- `logical` (logical page number if present, via mapping)
- `section_sid` (section owning this actual page)
- `src` (image URL for the scan pane)

#### Section renders

`GET /api/doc/{doc_id}/en/{sid}` → EN HTML  
`GET /api/doc/{doc_id}/vi/{sid}` → VI HTML

The server resolves `{sid}` against `sections_body[*].sid` and renders HTML through `render.py`.

#### Search (prototype)

`GET /api/doc/{doc_id}/search?q=...`

Searches EN AST text (and titles) and returns hits keyed by `sid` with a snippet.

## Rendering and Sync Rules

### EN page anchors

- EN anchors are derived from `PageBreak` nodes in the EN AST:
  - Each `PageBreak{page:N}` produces:
    - `<div id="p-N" class="anchor pagebreak"></div>`

### VI page anchors

- VI text in `sections_body.vi` is split on `\f` (form-feed).
- `render_vi_section(..., target_pages=[...])` prepends an anchor for each chunk:
  - `<div id="p-<actual>" class="anchor pagebreak"></div>`
- If `target_pages` is not present, anchors fall back to sequential indices (1..N).

### Viewer synchronization

- The viewer listens for scroll/visibility changes on `.anchor.pagebreak` elements.
- When the active anchor changes to `p-N`, the scan pane requests/updates page N (or applies mapping offsets/overrides).

## Implementation Notes (as-built)

### Naming normalization

- The stack moved from ambiguous `aid` usage to:
  - `sid` for sections
  - `pid` for page spans
  - `route_index` for routing (replacing `aid_index`)

### Backward compatibility (server-side only)

`app.py` may temporarily accept legacy bundle fields:

- `aid_index` as a fallback if `route_index` is absent
- `section_blocks` as a fallback if `sections_body` is absent
- legacy section-body keys where `sid` was serialized under `aid`

The viewer (`doc.html`) is v1-normalized and should not carry drift heuristics.

## Testing (v1)

Manual verification checklist:

1. `GET /api/doc/{doc_id}/bundle` includes `sections`, `sections_body`, `route_index`.
2. Section dropdown and sidebar populate from `sections`.
3. Selecting a section triggers:
   - `GET /en/{sid}` and `GET /vi/{sid}` returning non-empty HTML.
4. EN HTML includes anchors: `id="p-<N>"`.
5. VI HTML includes anchors for each page chunk.
6. Page bar requests:
   - `GET /page/{n}` returns `section_sid` and `src`.
7. Scan pane shows correct image for the active anchor page.
8. No console errors; errors are rendered in-page (not silently swallowed).

## Consequences

### Benefits

- The viewer is thinner and more reliable: one contract, no guessing.
- Page synchronization is consistent across EN/VI via shared anchor ids.
- The server becomes the single place to implement compatibility shims.

### Tradeoffs

- Contract changes require coordinated updates across builder/server/viewer.
- The current prototype does not yet formalize schema versioning.

## Follow-ups

- Add a lightweight “bundle adapter” in `app.py` that validates and normalizes bundle shape at load time (and logs all deltas).
- Consider adding an explicit schema version once external consumers exist.
- Populate `sections_body.pagination.breaks` from EN AST to support richer UI markers.
- Add stronger on-screen error reporting for missing sections_body entries or missing pagination targets.
