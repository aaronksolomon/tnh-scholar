---
key: punctuate_dharma_talk
name: Punctuate Dharma Talk
version: "1.0"
description: Adds punctuation and paragraph breaks to Deer Park and Plum Village Dharma Talk transcriptions
task_type: punctuation
role: punctuation
required_variables:
  - source_language
optional_variables:
  - style_convention
inputs:
  - name: source_language
    required: true
    strictness: strict
  - name: style_convention
    required: false
    strictness: loose
tags:
  - punctuation
  - formatting
  - dharma-talk
  - transcription
default_variables:
  source_language: English
  style_convention: APA
default_model: gpt-4o-mini
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Add punctuation and paragraph breaks to the Dharma Talk transcription in {{ source_language }}.

Requirements:
- Correct punctuation, paragraphing, and obvious typographic errors.
- Use {{ style_convention }} conventions when relevant.
- Use double newlines between paragraphs.
- Preserve the original content and meaning.
- Do not omit content.

Output only the corrected text. Do not add comments or wrapper formatting.
