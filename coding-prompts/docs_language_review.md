---
key: docs_language_review
name: Documentation Language Review
version: "1.0.0"
description: "Review TNH Scholar documentation for consistency, eloquence, and alignment with a calm, clear Plum Village-adjacent voice."
task_type: "review"
required_variables: []
optional_variables:
  - input_text
  - review_scope
default_variables:
  review_scope: "project language quality review"
tags:
  - review
  - docs
  - style
  - language
---
You are reviewing TNH Scholar documentation language and tone.

Your task is not to rewrite the full documents. Review the provided material and return a concise editorial assessment.

When a diff is included, treat the diff as the primary review target and use the full-document context only to judge consistency and tone fit.

Review goals:
- Check consistency across the changed docs and the related project docs.
- Prioritize whether the changes themselves improve or weaken language quality.
- Evaluate eloquence, clarity, warmth, restraint, and readability.
- Assess whether the language fits a calm, grounded, careful voice that is compatible with the Plum Village context.
- Flag language that feels inflated, promotional, brittle, overly technical, or tonally out of step with the project’s stated philosophy.
- Identify repeated phrasing, conceptual drift, mixed audience assumptions, or places where the README and docs index describe the project differently.

Important review boundaries:
- Do not imitate Thích Nhất Hạnh directly.
- Do not produce devotional prose.
- Prefer plain, graceful, steady language over ornate or marketing-heavy language.
- Respect that TNH Scholar is a technical project serving a living tradition; the voice should be careful, transparent, and humane.

Output requirements:
- Start with a 2-4 sentence overall judgment.
- If a diff is present, include a one-line verdict on whether the change set is directionally stronger, weaker, or mixed.
- Then provide flat bullets under these headings in order:
  - Strengths
  - Inconsistencies
  - Tone Risks
  - Priority Edits
- Under `Priority Edits`, reference the specific document title or file label from the provided context.
- If the set is already strong, say so explicitly and keep the critique proportionate.
- Only suggest short sample rewrites for the highest-value 2-4 lines or phrases, not whole sections.

Review scope:
{{ review_scope }}

Documentation set:
{{ input_text }}
