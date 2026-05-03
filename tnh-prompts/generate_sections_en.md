---
key: generate_sections_en
name: Generate Sections English
version: "1.0"
description: Divides English text into logical sections with titles, summaries, and line numbers
task_type: sectioning
role: sectioning
required_variables:
  - section_count
optional_variables: []
inputs:
  - name: section_count
    required: true
    strictness: strict
tags:
  - sectioning
  - english
  - analysis
default_model: gpt-4o
output_contract:
  mode: json
  schema_ref: tnh.sectioning.generate_sections_en.v1
output_mode: json
safety_level: safe
schema_version: "1.0"
---

Divide the numbered text into {{ section_count }} logical sections.

Requirements:
- Input lines are `<NUM:LINE>`.
- For each section, provide a title, summary, and inclusive start/end line numbers.
- Also provide a summary of the whole text.
- Every line must belong to exactly one section.
- Do not omit or overlap lines.

Return a JSON object matching the required schema exactly.
