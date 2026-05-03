---
key: simple_punctuate
name: Simple Punctuate
version: "1.0"
description: Add punctuation to text while preserving original words
task_type: punctuation
role: punctuation
required_variables: []
optional_variables:
  - source_language
  - style_convention
inputs:
  - name: source_language
    required: false
    strictness: loose
  - name: style_convention
    required: false
    strictness: loose
tags:
  - punctuation
  - formatting
  - editing
default_variables:
  source_language: "English"
  style_convention: "APA"
default_model: gpt-5-mini
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---
Add punctuation and paragraph breaks to the input text in {{ source_language }}.

Requirements:
- Correct punctuation, paragraphing, and obvious typographic errors.
- Use {{ style_convention }} conventions when relevant.
- Use double newlines between paragraphs.
- Preserve the original wording and meaning.
- Do not omit content.

Output only the corrected text. Do not add comments or wrapper formatting.
