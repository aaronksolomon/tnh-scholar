---
key: extract_wisdom1
name: Extract Wisdom One
version: "1.0"
description: Extracts insights, quotes, facts, and recommendations from text for TNH students
task_type: extraction
role: extraction
required_variables:
  - metadata
optional_variables: []
inputs:
  - name: metadata
    required: true
    strictness: strict
tags:
  - extraction
  - wisdom
  - analysis
  - tnh
default_model: gpt-4o
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Extract structured insights for TNH students.

Source metadata:
{{ metadata }}

Output markdown with these sections only:
- `# <title>`
- `## SUMMARY`
- `## IDEAS`
- `## QUOTES`
- `## FACTS`
- `## REFERENCES`
- `## RECOMMENDATIONS`

Requirements:
- Summary: about 100 words.
- Ideas: 10-50 items.
- Quotes: 10 exact quotes from the input.
- Facts: factual claims mentioned in the content.
- References: all notable books, art, tools, projects, or inspirations mentioned.
- Recommendations: practical or contemplative takeaways.
- Use `-` bullets where lists are appropriate.
- Do not repeat items or add commentary.
