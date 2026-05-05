---
key: make_text_concise
name: Make Text Concise
version: "1.0"
description: Transforms verbose text into concise version (~50% reduction) while preserving meaning and voice
role: editing
required_variables: []
optional_variables: []
inputs: []
tags:
  - editing
  - concision
  - condensing
  - clarity
default_model: gpt-4o
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Condense the text to roughly 50% of its original length while preserving meaning, voice, and key phrasing.

Requirements:
- Preserve core ideas, conclusions, memorable phrases, and important examples.
- Remove repetition, excess background, and unnecessary elaboration.
- Improve organization with headings or bullets when useful.
- Keep the result complete and coherent, not summary-like or fragmentary.
- Preserve the author's tone and perspective.

Output only the concise markdown text.
