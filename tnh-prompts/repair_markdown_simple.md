---
key: repair_markdown_simple
name: Repair Markdown Simple
version: "1.0"
description: Repairs markdown structure with consistent numbered sections and heading hierarchy
task_type: formatting
role: formatting
required_variables: []
optional_variables: []
inputs: []
tags:
  - markdown
  - formatting
  - structure
  - sections
default_model: gpt-4o-mini
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Repair the markdown structure with consistent numbered headings.

Requirements:
- Convert numbered structural elements into headings, for example `## 1. ...`, `### 2.1 ...`, and deeper levels as needed.
- Use one top-level `#` title only.
- Keep heading numbering and nesting consistent.
- Use `-` for unordered lists.
- Keep headings surrounded by blank lines.
- Remove trailing whitespace and leave a final newline.
- Change only structure and formatting, not substantive content.

Output only the repaired markdown.
