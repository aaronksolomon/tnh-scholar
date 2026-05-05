---
key: repair_markdown
name: Repair Markdown
version: "1.0"
description: Repairs and standardizes markdown formatting, structure, and hierarchy while preserving original content
role: formatting
required_variables: []
optional_variables: []
inputs: []
tags:
  - markdown
  - formatting
  - editing
  - structure
default_model: gpt-4o-mini
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Repair the markdown structure without changing the substantive content.

Requirements:
- Standardize heading hierarchy.
- Remove obvious page-number noise, broken symbols, and duplicate structural clutter.
- Improve list formatting, spacing, blockquotes, and paragraph breaks where needed.
- Keep markdownlint-friendly structure: one top-level heading, blank lines around headings and lists, `-` for unordered lists, spaces not tabs, and language tags on fenced code blocks.
- Preserve the document text; do not summarize or rewrite the content itself beyond structural cleanup.

Output only the repaired markdown.
