---
title: "Journal Walkthrough Review"
description: "Run-backed review companion for the OCR journal pipeline, with actual artifacts, output samples, and UI/UX review notes."
owner: ""
author: "OpenAI Codex"
status: current
created: "2026-05-03"
updated: "2026-05-03"
---
# Journal Walkthrough Review

This document is a review companion to the more general [Journal Pipeline Case Study](/docs/user-guide/journal-pipeline-case-study.md) and the user-facing [tnh-gen Walkthrough](/docs/user-guide/tnh-gen-educational-walkthrough.md). It is based on an actual `tnh-gen` run against the journal test source and points directly to the resulting artifacts so a human reviewer can inspect output quality and flag UI/UX issues.

## Scope

Source article:

- *Vũ-trụ-quan Phật học*
- author: Thạc-Đức
- journal: *Phật Giáo Việt Nam*
- issue: 17-18
- year: 1957

Source files:

- `/tests/golden/journal-pipeline/source.txt`
- `/tests/golden/journal-pipeline/source_numbered.txt`
- `/tests/golden/journal-pipeline/README.md`

Run assumption:

- invoke `tnh-gen` from the repo root
- use `--prompt-dir ./tnh-prompts`
- write every step as an output artifact

## Workflow Used

This run used a section-first plain-text flow:

1. `default_section` on the numbered source
2. extract representative sections
3. `default_clean` on raw section text
4. `translate_journal_section_en` on cleaned section text

This is intentionally different from the older numbered line-translation walkthrough. For this journal article, section-level clean and section-level translation proved to be a more believable human workflow.

## Actual Artifacts

Main sectioning artifact:

- `/tests/golden/journal-pipeline/walkthrough/clean_translate/sections_gpt54.json`
- provenance: `/tests/golden/journal-pipeline/walkthrough/clean_translate/sections_gpt54.json.provenance.yaml`

Representative clean artifacts:

- `/tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_cleaned.txt`
- `/tests/golden/journal-pipeline/walkthrough/clean_translate/section_04_cleaned.txt`

Representative translation artifacts:

- `/tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_translated_journal_en.txt`
- `/tests/golden/journal-pipeline/walkthrough/clean_translate/section_04_translated_journal_en.txt`

Supporting inputs and vars:

- `/tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_raw.txt`
- `/tests/golden/journal-pipeline/walkthrough/clean_translate/section_04_raw.txt`
- `/tests/golden/journal-pipeline/walkthrough/clean_translate/clean_vars.json`
- `/tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_journal_translate_vars.json`
- `/tests/golden/journal-pipeline/walkthrough/clean_translate/section_04_journal_translate_vars.json`

## What The Sectioner Produced

The sectioning run on `/tests/golden/journal-pipeline/source_numbered.txt` produced four contiguous sections covering the full 146-line source:

- lines `1–48`: `Bối cảnh tư tưởng Ấn Độ và lập trường phê bình của Phật giáo`
- lines `49–93`: `Thế giới nhân duyên và nguyên lý duyên khởi`
- lines `94–124`: `Đồng thời nhân quả và sự thành lập của thế giới nhận thức`
- lines `125–146`: `Dị thời nhân quả, dòng sinh mệnh và ý nghĩa đạo đức giải thoát`

Representative JSON excerpt:

```json
{
  "language": "vi",
  "sections": [
    {
      "start_line": 1,
      "end_line": 48,
      "title": "Bối cảnh tư tưởng Ấn Độ và lập trường phê bình của Phật giáo"
    },
    {
      "start_line": 125,
      "end_line": 146,
      "title": "Dị thời nhân quả, dòng sinh mệnh và ý nghĩa đạo đức giải thoát"
    }
  ]
}
```

The full artifact also includes summary, Dublin Core fields, key concepts, and narrative context.

## Clean Output Sample

Excerpt from `/tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_cleaned.txt`:

```text
VŨ-TRỤ-QUAN
PHẬT-HỌC
THẠC-ĐỨC

Vào thời đại của đức Phật, vấn đề nguyên lý của vạn vật là một vấn đề rất được chú trọng trong tư tưởng giới Ấn Độ.
...
2. Khuynh hướng Thần ý luận (Issara-nimmana hetu)
...
3. — Khuynh hướng Ngẫu nhiên-luận (Ahetu apaccaya)
```

What this shows:

- title and author lines were preserved and normalized
- dropped diacritics were restored
- duplicate or noisy section markers were regularized
- footer intrusion was removed
- the output remained close to the source rather than becoming a synthetic rewrite

## Translation Output Sample

Excerpt from `/tests/golden/journal-pipeline/walkthrough/clean_translate/section_01_translated_journal_en.txt`:

```text
The Indian Intellectual Context and the Critical Stance of Buddhism

In the time of the Buddha, the question of the underlying principle of all things was one to which Indian thinkers gave great attention.
...
2.—The tendency of theism, or divine-volition theory (Issara-nimmāna-hetu)
...
The Buddha’s purpose in teaching the Dīrgha Āgama was not to insist on refuting the theories of others, but only to reject mistaken philosophical conceptions that could obstruct the realization of morality and liberation for human beings.
```

Excerpt from `/tests/golden/journal-pipeline/walkthrough/clean_translate/section_04_translated_journal_en.txt`:

```text
Successive-Time Causality, the Stream of Life, and the Moral Significance of Liberation

2. The problem of successive-time causality is also the problem of continuity in existence.
...
The Buddhist conception of causality encompasses moral and liberative relations as well; in breadth it extends throughout the ten directions, and in length it penetrates past, future, and present.
```

What this shows:

- the section translation prompt can produce readable doctrinal English on bounded journal sections
- Buddhist technical vocabulary is handled more consistently than in earlier `gpt-4o` runs
- plain-text section translation is a better walkthrough surface here than line-by-line numbered translation

## Review Notes

What looks strong:

- section-first splitting is usable on a real journal article
- the artifact chain is reviewable at every step
- `default_clean` does meaningful OCR recovery work
- `translate_journal_section_en` is viable for bounded review-oriented translation

Current operator friction:

- multiline metadata is still awkward to pass inline
- `--vars` is much better than repeated `--var`, but JSON-only vars are still clumsy for metadata-heavy work
- `target_section_count` is explicit and useful, but `target_lines_per_section` is still a somewhat manual heuristic
- the older walkthrough docs still emphasize the line-translation path and should eventually be reconciled with this section-based path

## Human Review Checklist

Suggested review questions:

- Are the section boundaries good enough for real editorial work?
- Does the clean stage stay faithful while fixing OCR damage?
- Does the English translation register feel appropriate for this class of Buddhist journal prose?
- Is the command surface something a careful human operator would realistically use?
- Which parts of the workflow should become simpler before this is presented as a canonical walkthrough?

## Related Docs

- [Journal Pipeline Case Study](/docs/user-guide/journal-pipeline-case-study.md)
- [Prompt System](/docs/user-guide/prompt-system.md)
- [Best Practices](/docs/user-guide/best-practices.md)
- [tnh-gen CLI Reference](/docs/cli-reference/tnh-gen.md)
