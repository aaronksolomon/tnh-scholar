---
key: default_clean
name: Default OCR Clean
version: "1.0"
description: Cleans OCR-generated text into flowing plain text — fixes character errors, restores diacritical marks, removes page artifacts (headers, footers, watermarks, page numbers), and normalizes paragraph structure. Use for plain-text output pipelines; see default_clean_numbered for line-tracked pipelines.
task_type: cleaning
role: cleaning
required_variables:
  - source_language
optional_variables:
  - publication_name
  - publisher_mark
inputs:
  - name: source_language
    required: true
    strictness: strict
  - name: publication_name
    required: false
    strictness: loose
  - name: publisher_mark
    required: false
    strictness: loose
tags:
  - ocr
  - cleaning
  - text-processing
default_variables:
  source_language: Vietnamese
default_model: gpt-4o
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Clean the OCR-generated {{ source_language }} text below. Produce a minimal, faithful correction.

Corrections to make:
- Fix clear OCR character errors (for example, `f` misread as `t`, or missing or wrong diacritical marks).
- Restore missing diacritical marks using surrounding context.
- Correct obvious typographic errors caused by the scan.
- Do not change proper names except to restore diacritical marks or fix a clear OCR error where the correct form is unambiguous.

Content rules:
- Do not alter the meaning, substance, or logical structure of the text.
- Do not add, remove, or reorder body content.
- You may merge OCR-broken scan lines into natural prose and normalize paragraph breaks.
- Separate paragraphs with a blank line.

Page artifacts to remove (do not include in output):
- Standalone page numbers.
{% if publication_name %}- Lines that consist only of the publication name or a fragment of it: "{{ publication_name }}".
{% endif %}{% if publisher_mark %}- Lines that consist only of the publisher watermark or a fragment of it: "{{ publisher_mark }}".
{% endif %}- Any other obvious non-body text from running headers, footers, or print overlays.

If the input contains no recoverable body text, output only: `blank page`

Output only the cleaned text. Do not add comments, labels, or wrapper formatting.
