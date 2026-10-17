---
key: sr-d-paragraph-grammar
name: Sr. D Paragraph Grammar
version: "1.1"
description: "Correct grammar and punctuation in one English transcript paragraph while preserving its meaning and content."
role: editing
required_variables: []
optional_variables: []
tags:
  - grammar
  - transcription
default_model: gpt-5.6-sol
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Correct the grammar and punctuation of this single English paragraph from
a Dharma talk by Sister Dang Nghiem, for readability.

Make the smallest necessary edits. Preserve the speaker's voice, meaning,
sentence order, and all teachings, explanations, examples, questions,
quotations, repetitions for emphasis, audience interactions, and details.
Repair agreement, tense, articles, sentence boundaries, and clear grammatical
errors. Do not summarize, shorten, embellish, or remove sentences. Do not
guess at ambiguous names or facts. Leave deliberate fragments and direct
speech intact when grammatical correction would change their meaning.
Keep named teachings such as the Five Mindfulness Trainings intact; do not
insert punctuation inside a named term. Preserve religious qualifiers and
the specific identity of people or groups.

Do not delete repeated sentences or substantive wording. A paragraph may
begin or end mid-thought; do not invent context or complete missing thoughts.
If no correction is needed, return the paragraph unchanged.

Return exactly one paragraph of plain text. No headings, comments, explanations,
code fences, or additional paragraph breaks.
