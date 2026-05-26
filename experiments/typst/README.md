---
title: "Typst Facsimile Prototype"
description: "Experimental Typst prototype for a first-page facsimile of the 1957 journal article Vũ-trụ-quan Phật học."
status: draft
created: "2026-05-24"
updated: "2026-05-24"
---

# Typst Facsimile Prototype

This directory contains an experimental Typst facsimile-translation of the first page of
*Vũ-trụ-quan Phật học* from *Phật Giáo Việt Nam* issue 17-18 (1957).

## Files

- `vu-tru-page7-facsimile.typ`: standalone Typst source for the prototype page
- `assets/`: generated title and paper-texture assets used by the page

## Intent

This is not a diplomatic facsimile. It is a print-first English translation experiment that
tries to capture some of the journal page's feel:

- warm paper tone
- scan-derived paper texture
- compact serif body text
- OCR-informed title and byline placement
- condensed display title generated from a local font library
- English translated body copy arranged in a measured journal-like frame

## Render

To rebuild the facsimile assets, compile the Typst source, and render a 300 DPI PNG
preview of the first page:

```bash
make typst-facsimile
```

This target calls:

```bash
./scripts/render_typst_facsimile.sh
```

The render script refreshes:

- a paper-texture background from the clean page scan
- a transparent title block generated from a local macOS font

You can override the title font for the asset build:

```bash
TITLE_FONT="/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf" make typst-facsimile
```

To clean generated render artifacts:

```bash
make typst-facsimile-clean
```

## Next Improvements

- tune geometry directly from OCR region exports rather than inferred page ratios
- test alternative condensed title faces and mild text distressing
- add a bottom-left seal or other page furniture only if it improves fidelity
- refine paragraph breaks against the original article page rather than translated copy length
