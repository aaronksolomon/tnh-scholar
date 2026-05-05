---
key: extract_wisdom_mini
name: Extract Wisdom Mini
version: "1.0"
description: Extracts concise insights (5-10 each of ideas, quotes, facts) from text for TNH students
role: extraction
required_variables: []
optional_variables: []
inputs: []
tags:
  - extraction
  - wisdom
  - analysis
  - tnh
  - concise
default_model: gpt-4o-mini
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Extract a concise structured wisdom summary for TNH students.

Output markdown with these sections only:
- `# <title>`
- `## SUMMARY`
- `## IDEAS`
- `## QUOTES`
- `## FACTS`
- `## REFERENCES`
- `## RECOMMENDATIONS`

Requirements:
- Summary: about 60 words.
- Ideas, quotes, facts, and recommendations: 5-10 items each.
- Quotes must be exact quotes from the input.
- References should include all notable books, art, tools, projects, or inspirations mentioned.
- Use `-` bullets where lists are appropriate.
- For ideas, facts, and recommendations, keep each bullet concise, about 10-20 words.
- Do not repeat items or add commentary.
