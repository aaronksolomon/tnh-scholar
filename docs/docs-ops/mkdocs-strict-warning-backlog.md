---
title: "MkDocs Strict Warning Backlog"
description: "Checklist to drive MkDocs builds to zero warnings in strict mode."
owner: ""
author: ""
status: current
created: "2025-11-25"
---

# MkDocs Strict Warning Backlog

> Tracking all current `mkdocs build --strict` warnings so we can clear them systematically.

## Navigation / Link Breaks

- [x] Remove or replace stale nav references generated into `docs-nav.md` (e.g., `docs-design/planning/roadmap.md`, `docs-design/planning/maintenance.md`, translation experiment files).
- [ ] Fix broken relative links in ADRs/design docs (e.g., `architecture/gen-ai-service/design/migration-plan.md` pointing to `genai-service-strategy.md`, ADR links with doubled `architecture/` segments).
- [ ] Audit `docs/documentation_index.md` for links that do not exist post-reorg; prune or update paths so they resolve within `docs/`.
- [ ] Normalize absolute links in `docs/index.md` and mirrored README (`docs/project/repo-root/repo-readme.md`) to correct site-relative paths.

## Autorefs / Mirrored Root Docs

- [x] Regenerate `docs/project/repo-root/TODO.md` after converting root TODO links to GitHub URLs so mkdocs-autorefs can resolve them.

## Mkdocstrings (Griffe) — Signature / Docstring Alignment

- [ ] `src/tnh_scholar/ai_text_processing/*`: add missing type hints and align docstrings/signatures (ai_text_processing.py, text_object.py, line_translator.py, prompts.py yield docs).
- [ ] `src/tnh_scholar/audio_processing/*`: fix parameters documented but not in signatures (audio_legacy.py, timed_text.py, transcription/* including assemblyai_service.py, srt_processor.py, vtt_processor.py, transcription_service.py, transcription_pipeline.py).
- [ ] `src/tnh_scholar/journal_processing/journal_process.py`: ensure docstrings match signatures/return types for batch/process helpers.
- [ ] `src/tnh_scholar/cli_tools/audio_transcribe/audio_transcribe.py`: align CLI option docs with function signatures.
- [ ] `src/tnh_scholar/logging_config.py`: clean docstring field lists and add missing annotations.
- [ ] `src/tnh_scholar/ocr_processing/*`: add missing params/return annotations in ocr_processing.py and ocr_editor.py.
- [ ] `src/tnh_scholar/text_processing/numbered_text.py`: fix docstring list formatting (`name: description` pair).
- [ ] `src/tnh_scholar/utils/tnh_audio_segment.py`: add annotations for **kwargs overloads.
- [ ] `src/tnh_scholar/video_processing/video_processing_old1.py`: align docstrings with signatures or mark as deprecated appropriately.
- [ ] `src/tnh_scholar/xml_processing/extract_tags.py`: add return type annotation for set.

## Verification

- [ ] Run `poetry run mkdocs build --strict` and confirm zero warnings.
