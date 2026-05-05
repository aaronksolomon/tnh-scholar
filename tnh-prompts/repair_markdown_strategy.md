---
key: repair_markdown_strategy
name: Repair Markdown Strategy
version: "1.0"
description: Generates a bullet-point strategy for repairing markdown structure
role: analysis
required_variables: []
optional_variables: []
inputs: []
tags:
  - markdown
  - analysis
  - strategy
default_model: gpt-4o-mini
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Suggest a concise bullet-point plan for repairing the markdown structure only.

Requirements:

- Focus on hierarchy, spacing, list structure, and formatting consistency.
- Do not suggest changing substantive content.
- Be precise and concise.

Output only a markdown bullet list using `-`.
