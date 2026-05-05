---
key: simple_translate_paragraph_thay
name: Simple Translate Paragraph Thay
version: "1.0"
description: Translates a single paragraph from TNH into flawless English in his style
role: translation
required_variables: []
optional_variables: []
inputs: []
tags:
  - translation
  - tnh
  - paragraph
  - simple
default_model: gpt-4o-mini
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Translate the paragraph into fluent English in Thich Nhat Hanh's style.

Requirements:
- Preserve meaning.
- Use natural, clear English.
- Correct clear grammatical, typographic, and logical errors.
- Do not add, omit, summarize, or explain anything.

Output only the translation.
