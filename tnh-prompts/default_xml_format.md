---
key: default_xml_format
name: Default XML Format
version: "1.0"
description: Formats text sections into XML paragraphs with proper punctuation
task_type: formatting
role: formatting
required_variables:
  - source_language
  - section_title
  - speaker_name
optional_variables: []
inputs:
  - name: source_language
    required: true
    strictness: strict
  - name: section_title
    required: true
    strictness: strict
  - name: speaker_name
    required: true
    strictness: strict
tags:
  - xml
  - formatting
  - paragraphs
default_model: gpt-4o
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Convert the section "{{ section_title }}" by {{ speaker_name }} into publication-ready XML paragraphs in {{ source_language }}.

Requirements:
- Use only `<p>` tags.
- Correct clear logical, transcription, grammatical, or punctuation errors.
- Preserve meaning, tone, and content.
- Do not summarize, omit, or add content.

Output only the final XML text.
