---
key: generate_sections_multi_lang
name: Generate Sections Multi-Language
version: "1.0"
description: Divides multi-language text into logical sections with titles in source language and English
task_type: sectioning
role: sectioning
required_variables:
  - source_language
  - section_count
optional_variables: []
inputs:
  - name: source_language
    required: true
    strictness: strict
  - name: section_count
    required: true
    strictness: strict
tags:
  - sectioning
  - multilingual
  - analysis
default_model: gpt-4o
output_contract:
  mode: json
  schema_ref: tnh.sectioning.generate_sections_multi_lang.v1
output_mode: json
safety_level: safe
schema_version: "1.0"
---

Divide the numbered transcript into approximately {{ section_count }} logical sections.

For each section provide:
- a title in {{ source_language }}
- an English title if the source language is not English
- an English summary
- inclusive start and end line numbers

Also provide an English summary of the full text.

Requirements:
- Input lines are `<NUM:LINE>`.
- Return sections in order.
- Every line must belong to exactly one section.

Return the exact response format expected by the caller.

IMPORTANT: 
- Sections must be given in order.

- Every line in the transcript must belong to a section. 

- Don't leave out any lines, even if they are blank or contain only whitespace.

- Don't include lines in more than one section.
