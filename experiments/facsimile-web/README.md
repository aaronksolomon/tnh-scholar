---
title: "Facsimile Web Overlay Prototype"
description: "Static HTML prototype for image-grounded facsimile overlays with region-level Vietnamese and English payloads."
status: draft
created: "2026-05-25"
updated: "2026-05-25"
---

# Facsimile Web Overlay Prototype

This prototype tests the v2 direction for facsimile interaction:

- keep the page image as the visual ground truth
- layer OCR-like bounding boxes over it
- attach Vietnamese and English payloads to each region
- let hover, click, and right-click drive inspection behavior

## Files

- `page7-overlay.html`: static entry page
- `page7-data.js`: region data and translation payloads
- `page7-overlay.css`: presentation layer
- `page7-overlay.js`: interaction layer

## Why This Shape

This is a better fit than recreating the whole page as live HTML text:

- the image preserves facsimile control
- the overlay layer can change without disturbing the page rendering
- region data can later become line-level or sentence-level
- the same data model can feed a simple web app or a VS Code side pane

## Current Interaction

- hover a region to preview it
- click a region to pin it in the inspector
- right-click a region to switch the inspector between:
  - Vietnamese only
  - English only
  - both

## Serve Locally

From the repo root:

```bash
python3 -m http.server 8027
```

Then open:

```text
http://localhost:8027/experiments/facsimile-web/page7-overlay.html
```

## Next Step

The prototype currently uses hand-curated region groupings based on OCR output. The next
useful improvement is to replace those manual groupings with exported OCR region data and
sentence alignment metadata so the overlay can scale beyond a single page.
