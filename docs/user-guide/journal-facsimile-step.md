---
title: "Post-pipeline Facsimile Step"
description: "Short note on the experimental facsimile stage that can follow the journal OCR, cleaning, translation, and review pipeline."
owner: ""
author: ""
status: draft
created: "2026-05-25"
updated: "2026-05-26"
---

# Post-pipeline Facsimile Step

The facsimile step is an experimental stage that runs after the journal pipeline has produced its text artifacts: cleaned Vietnamese, English drafts, and reviewed translation output.

## Purpose and Motivation

The pipeline produces traceable text artifacts, but the source material is also a designed page: title treatment, byline placement, column density, and footer layout all shaped how a reader encountered the piece in 1957. 

The facsimile step produces an English rendering that mirrors the original layout, so the Vietnamese original and English translation can be compared at the same page scale. This supports editorial and historical work where the visual structure of the page matters. It is a presentation artifact — it complements the source images and text files.

## Method

The `v1` prototype reconstructs page 7 of *Vũ-trụ-quan Phật học* — the article's opening page — as an English facsimile. It uses the clean source scan as the visual reference, rebuilds the display title using local font assets, samples paper texture from the source page, and places the reviewed TNH-voice translation into a page frame tuned to match the original layout.

## Original Page and Facsimile

![Original Vietnamese opening page of Vũ-trụ-quan Phật học](assets/journal-pipeline/pgvn-17-18-page7-clean.jpg)

*Original opening page of the article, as published in* Phật Giáo Việt Nam *issue 17–18, 1957.*

![Experimental English facsimile prototype of page 7 of Vũ-trụ-quan Phật học](assets/journal-pipeline/pgvn-17-18-page7-facsimile-v1.png)

*Experimental `v1` English facsimile of the opening page. Body text now follows the TNH-voice translation only through the page-7 extent, including the carry-over into the next page break. The display title uses a stylized English rendering rather than a literal title translation.*

## Future Direction

The next step is a hybrid viewer rather than a static print artifact. In that model, the source image or facsimile serves as the visual ground truth, while OCR-derived bounding boxes carry interactive payloads: Vietnamese source text, English translation, and editorial notes, accessible by line, sentence, or paragraph. A web-based review interface would come first, with a potential future VS Code analysis pane for TNH Scholar.

## Assets

- [Original page 7 scan](/user-guide/assets/journal-pipeline/pgvn-17-18-page7-clean.jpg)
- [Page 7 facsimile PNG](/user-guide/assets/journal-pipeline/pgvn-17-18-page7-facsimile-v1.png)
- [Page 7 facsimile PDF](/user-guide/assets/journal-pipeline/pgvn-17-18-page7-facsimile-v1.pdf)
- [Pipeline case study](/user-guide/journal-pipeline-case-study.md)
