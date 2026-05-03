---
key: default_line_translate
name: Default Line Translate
version: "1.0"
description: Line-by-line translation preserving line numbers and structure (tightly coupled to translate processor)
task_type: translation
role: translation
required_variables:
  - source_language
  - target_language
  - style
  - metadata
optional_variables: []
inputs:
  - name: source_language
    required: true
    strictness: strict
  - name: target_language
    required: true
    strictness: strict
  - name: style
    required: true
    strictness: strict
  - name: metadata
    required: true
    strictness: strict
tags:
  - translation
  - line-by-line
  - transcript
default_model: gpt-4o
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Translate the transcript segment line by line from {{ source_language }} to {{ target_language }} in the style of {{ style }}.

Context metadata:
{{ metadata }}

Input blocks:
- `PRECEDING_CONTEXT`
- `TRANSCRIPT_SEGMENT`
- `FOLLOWING_CONTEXT`
- Each transcript line is `X:LINE`.

Requirements:
- Translate only `TRANSCRIPT_SEGMENT`.
- Preserve every original line number exactly.
- Preserve the exact number of lines, including empty or whitespace-only lines.
- Do not merge, omit, renumber, or reorder lines.
- Use surrounding context only to interpret and improve the target line.
- Correct obvious errors only when needed for a faithful translation.

Output format:
```text
TRANSCRIPT_SEGMENT
X:Translated line
X:Translated line
...
TRANSCRIPT_SEGMENT
```

Output only the translated segment. Do not add comments or extra formatting.
