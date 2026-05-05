---
key: translate_journal_section_en
name: Translate Journal Section English
version: "1.0"
description: Translates a cleaned journal article section into readable scholarly English using document and section context from prior sectioning output
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

Requirements:
- Produce clear, faithful, lightly scholarly English suitable for a Buddhist studies journal workflow.
- Preserve meaning while improving punctuation, grammar, transcription, and flow where needed.
- Use the document and section context to keep terminology and argumentation consistent with the larger article.
- Keep established Buddhist technical terms accurate and consistent.
- Generate an English section title on the first line.
- Paragraph the result with single blank-line separation.
- Do not add, omit, summarize, or explain content.
- Do not use markdown or wrapper formatting.
- Do not output code fences, labels, notes, or introductory text.

Output:
- first line: the English section title
- remaining lines: the translated paragraphs
