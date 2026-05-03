---
key: format_markdown_math
name: Format Markdown Math
version: "1.0"
description: Formats mathematical text into proper Markdown with correct equation notation ($ and $$)
task_type: formatting
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
  - math
  - formatting
  - equations
default_model: gpt-4o
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Format the text as clean Markdown in {{ source_language }}, with correct math notation.

Requirements:
- Use `$...$` for inline math and `$$...$$` for block math.
- Convert `\(...\)` to `$...$`.
- Convert `\[...\]` to `$$...$$`.
- Correct clear notation, markdown, spelling, and punctuation errors.
- Preserve the content otherwise.
- Use double newlines between major blocks when needed for valid markdown rendering.

Output only the final markdown.
