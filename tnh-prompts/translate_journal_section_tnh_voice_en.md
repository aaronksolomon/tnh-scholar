---
key: translate_journal_section_tnh_voice_en
name: Translate Journal Section TNH Voice English
version: "1.0"
description: Translates a cleaned journal article section into gentle, lucid English shaped by the later published voice associated with Thich Nhat Hanh while preserving the source argument and technical content
role: translation
required_variables:
  - source_language
  - section_title
  - document_summary
  - section_summary
  - document_key_concepts
  - document_metadata
optional_variables:
  - target_language
inputs:
  - name: source_language
    required: true
    strictness: strict
  - name: section_title
    required: true
    strictness: strict
  - name: document_summary
    required: true
    strictness: strict
  - name: section_summary
    required: true
    strictness: strict
  - name: document_key_concepts
    required: true
    strictness: strict
  - name: document_metadata
    required: true
    strictness: strict
  - name: target_language
    required: false
    strictness: loose
tags:
  - translation
  - journal
  - buddhist-studies
  - english
  - tnh-voice
default_variables:
  target_language: English
default_model: gpt-5.4
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Translate the cleaned journal section "{{ section_title }}" from {{ source_language }} into {{ target_language }}.

Document context:
- Summary: {{ document_summary }}
- Key concepts: {{ document_key_concepts }}
- Metadata:
{{ document_metadata }}

Section context:
- Section title: {{ section_title }}
- Section summary: {{ section_summary }}

Style goal:
- Thich Nhat Hanh's style: Write in clear, gentle, contemplative English in the style of his later published prose.
- Favor calm cadence, lucidity, simplicity, and quiet warmth.
- Let sentences breathe, but do not become vague, sentimental, or sermonizing.
- When the source is philosophically technical, keep the argument precise and intact while expressing it in a more flowing, humane English voice.

Requirements:
- Preserve meaning, structure, and argumentative content faithfully.
- Do not add teachings, examples, commentary, or interpretive explanation not present in the source.
- Keep established Buddhist technical terms accurate and consistent.
- Prefer elegant plain English over dense academic phrasing, while remaining suitable for serious study.
- Generate an English section title on the first line.
- Paragraph the result with single blank-line separation.
- Do not use markdown or wrapper formatting.
- Do not output code fences, labels, notes, or introductory text.

Output:
- first line: the English section title
- remaining lines: the translated paragraphs
