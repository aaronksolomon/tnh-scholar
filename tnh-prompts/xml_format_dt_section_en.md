---
key: xml_format_dt_section_en
name: XML Format Dharma Talk Section English
version: "1.0"
description: Formats English Dharma talk transcriptions into XML paragraphs in Plum Village style
task_type: formatting
role: formatting
required_variables:
  - section_title
  - metadata
optional_variables: []
inputs:
  - name: section_title
    required: true
    strictness: strict
  - name: metadata
    required: true
    strictness: strict
tags:
  - xml
  - formatting
  - dharma-talk
  - english
  - plum-village
default_model: gpt-4o
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Format the section "{{ section_title }}" as publication-ready XML paragraphs in Plum Village style.

Metadata:
{{ metadata }}

Requirements:
- First line: `<section-title>{{ section_title }}</section-title>`
- Remaining content: `<p>` tags only.
- Correct clear logical, speaking, transcription, grammatical, and punctuation errors.
- Preserve meaning and content.
- Do not summarize, omit, or add content.

Output only the final XML text.
