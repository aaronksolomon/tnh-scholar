---
key: organize_collate_translation
name: Organize and Collate Translation
version: "1.0"
description: Organizes line-by-line translated Vietnamese Dharma talks into coherent English paragraphs in TNH style
role: editing
required_variables:
  - section_title
optional_variables: []
inputs:
  - name: section_title
    required: true
    strictness: strict
tags:
  - editing
  - translation
  - tnh
  - vietnamese
  - dharma-talk
default_model: gpt-4o
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Organize the translated section "{{ section_title }}" into coherent English paragraphs in Thich Nhat Hanh's style.

Input:
- a section titled "{{ section_title }}"
- line-by-line translated Vietnamese Dharma Talk text

Requirements:
- Group the section into coherent paragraphs.
- Merge or split sentences when needed for clarity and flow.
- Correct clear grammatical, punctuation, and transcription issues.
- Preserve meaning while producing polished, publication-ready English.
- Do not add, omit, summarize, or explain anything.

Output only the cleaned section text.
