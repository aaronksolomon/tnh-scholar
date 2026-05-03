---
key: translate_lines_thay_audio
name: Translate Lines Thay Audio
version: "1.0"
description: Line-by-line translation of TNH Vietnamese audio transcripts to English preserving line numbers
task_type: translation
role: translation
required_variables:
  - source_language
  - target_language
optional_variables: []
inputs:
  - name: source_language
    required: true
    strictness: strict
  - name: target_language
    required: true
    strictness: strict
tags:
  - translation
  - tnh
  - vietnamese
  - line-by-line
  - audio
default_model: gpt-4o
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Translate each line of `TRANSCRIPT_SEGMENT` from {{ source_language }} into {{ target_language }} in Thich Nhat Hanh / Plum Village style.

Input blocks:
- `PRECEDING_CONTEXT`
- `TRANSCRIPT_SEGMENT`
- `FOLLOWING_CONTEXT`
- Each transcript line is `X:LINE`.

Requirements:
- Translate only `TRANSCRIPT_SEGMENT`.
- Preserve every original line number exactly.
- Preserve the exact number of lines, including empty lines.
- Do not merge, omit, renumber, or reorder lines.
- Use surrounding context only to interpret and improve the target line.
- Correct transcription, grammatical, speaking, and logical errors when needed for a faithful rendering.
- If a line is a bell or similar sound, you may use `[Bell]`.
- If a line is unintelligible, you may use `[Unintelligible]`.

Output format:
```text
TRANSCRIPT_SEGMENT
X:Translated and corrected line
X:Translated and corrected line
...
TRANSCRIPT_SEGMENT
```

Output only the translated segment. Do not add comments or extra formatting.
