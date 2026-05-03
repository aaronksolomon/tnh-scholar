---
key: translate_section_dt_en
name: Translate Section Dharma Teacher English
version: "1.0"
description: Translates Plum Village monastic Dharma talks into English in TNH/Plum Village style
task_type: translation
role: translation
required_variables:
  - source_language
  - section_title
  - metadata
optional_variables: []
inputs:
  - name: source_language
    required: true
    strictness: strict
  - name: section_title
    required: true
    strictness: strict
  - name: metadata
    required: true
    strictness: strict
tags:
  - translation
  - dharma-talk
  - plum-village
  - english
default_model: gpt-4o
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Translate the section "{{ section_title }}" from {{ source_language }} into English in Plum Village / TNH style.

Metadata:
{{ metadata }}

Requirements:
- Generate an English section title.
- Preserve meaning while improving punctuation, grammar, transcription, and flow where needed.
- Paragraph the result with single blank-line separation.
- Do not add, omit, summarize, or explain content.
- Do not use markdown or wrapper formatting.

Output:
- first line: the English title
- remaining lines: the translated paragraphs
