---
key: generate_markdown
name: Generate Markdown
version: "1.0"
description: Converts various text formats (transcripts, PDFs, OCR, HTML) into well-structured Markdown
role: formatting
required_variables:
  - source_language
optional_variables: []
inputs:
  - name: source_language
    required: true
    strictness: strict
tags:
  - markdown
  - formatting
  - conversion
  - transcript
default_model: gpt-4o
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Convert the input into clean Markdown in {{ source_language }}.

Possible input sources include transcripts, PDFs, OCR, HTML, web pages, or plain text.

Requirements:
- Preserve all content.
- Improve headings, paragraphing, lists, and overall markdown structure.
- For multi-speaker transcripts, label speaker turns clearly and consistently.
- Preserve transcript notes such as `[music]` or `[applause]`.
- Correct clear spelling, transcription, typographic, and grammatical errors.
- Use `$...$` and `$$...$$` for math. Convert `\(...\)` and `\[...\]` accordingly.
- Do not add commentary or wrapper formatting.

Output only the final markdown.
