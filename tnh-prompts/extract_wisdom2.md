---
key: extract_wisdom2
name: Extract Wisdom Two
version: "1.0"
description: Extracts detailed insights (35 ideas, 30 quotes, 20 facts) from text for TNH students
role: extraction
required_variables: []
optional_variables: []
inputs: []
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

Extract a detailed structured wisdom summary for TNH students.

Output markdown with these sections only:
- `# <title>`
- `## SUMMARY`
- `## IDEAS`
- `## QUOTES`
- `## FACTS`
- `## REFERENCES`
- `## RECOMMENDATIONS`

Requirements:
- Summary: about 200 words.
- Ideas: 35 items.
- Quotes: 30 exact quotes from the input.
- Facts: 20 factual claims mentioned in the content.
- References: all notable books, art, tools, projects, or inspirations mentioned.
- Recommendations: 30 practical or contemplative takeaways.
- Use `-` bullets where lists are appropriate.
- For ideas, facts, and recommendations, keep each bullet concise, about 10-20 words.
- Do not repeat items or add commentary.
