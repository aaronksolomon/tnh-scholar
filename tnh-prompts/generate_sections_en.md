---
key: generate_sections_en
name: Generate Sections English
version: "1.0"
description: Divides English text into logical sections with titles, summaries, and line numbers
role: sectioning
required_variables: []
optional_variables:
  - target_section_count
inputs:
  - name: target_section_count
    required: false
    strictness: loose
tags:
  - sectioning
  - english
  - analysis
default_model: gpt-5.4
output_contract:
  mode: json
  schema_ref: tnh.sectioning.generate_sections_en.v1
output_mode: json
safety_level: safe
schema_version: "1.0"
---

Divide the numbered text into {{ target_section_count or "a sensible number of" }} logical sections.

Requirements:
- Input lines are numbered: `<NUM:LINE>`.
- For each section, provide a title, summary, and inclusive start/end line numbers.
- Also provide a summary of the whole text.
- Every line must belong to exactly one section.
- Do not omit or overlap lines, even if blank.
- The first section must start at line 1.
- Each next section must start exactly one line after the previous section ends.
- The final section must end at the final input line.

Return a JSON object matching the required schema exactly.
