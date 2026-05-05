---
key: extract_wisdom_section
name: Extract Wisdom Section
version: "1.0"
description: Extracts insights from a named section of text for TNH students
role: extraction
required_variables:
  - section_title
optional_variables: []
inputs:
  - name: section_title
    required: true
    strictness: strict
tags:
  - extraction
  - wisdom
  - analysis
  - tnh
  - section
default_model: gpt-4o
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Extract structured insights from the section "{{ section_title }}" for TNH students.

Output markdown with these sections only:
- `# {{ section_title }}`
- `## SUMMARY`
- `## IDEAS`
- `## QUOTES`
- `## FACTS`
- `## REFERENCES`
- `## RECOMMENDATIONS`

Requirements:
- Quotes must be exact quotes from the input.
- References should include all notable books, art, tools, projects, or inspirations mentioned.
- Use `-` bullets where lists are appropriate.
- Do not repeat items or add commentary.
