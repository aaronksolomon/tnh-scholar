---
key: default_clean_numbered
name: Default OCR Clean (Numbered)
version: "1.0"
description: Cleans OCR-generated text and outputs numbered lines in N:LINE format, preserving OCR scan-line boundaries. Compatible with default_section and default_line_translate. Use for line-tracked pipelines; see default_clean for plain-text output.
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
  - numbered
  - pipeline
  - text-processing
default_variables:
  source_language: Vietnamese
default_model: gpt-5.4
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Clean the OCR-generated {{ source_language }} text below and output it as a numbered line transcript.

Corrections to make:
- Fix clear OCR character errors (for example, `f` misread as `t`, or missing or wrong diacritical marks).
- Restore missing diacritical marks using surrounding context.
- Correct obvious typographic errors caused by the scan.
- Do not change proper names except to restore diacritical marks or fix a clear OCR error where the correct form is unambiguous.

Content rules:
- Do not alter the meaning, substance, or logical structure of the text.
- Do not add, remove, or reorder body content.
- Preserve the original scan-line boundaries exactly — do not merge or split lines.
- Blank lines in the body are preserved as empty numbered lines (see format below).

Page artifacts to omit (do not include in output at all):
- Standalone page numbers.
{% if publication_name %}- Lines that consist only of the publication name or a fragment of it: "{{ publication_name }}".
{% endif %}{% if publisher_mark %}- Lines that consist only of the publisher watermark or a fragment of it: "{{ publisher_mark }}".
{% endif %}- Any other obvious non-body text from running headers, footers, or print overlays.

Output format:
- Number every output line sequentially starting from 1.
- Use the format `N:LINE` where N is the line number and LINE is the cleaned text.
- Blank body lines: output as `N:` (number with no content after the colon).
- Omitted artifact lines do not appear in the output and do not consume a line number.

If the input contains no recoverable body text, output only: `blank page`

Output only the numbered cleaned text. Do not add comments, labels, or wrapper formatting.
