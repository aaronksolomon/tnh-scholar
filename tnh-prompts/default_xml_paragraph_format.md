---
key: default_xml_paragraph_format
name: Default XML Paragraph Format
version: "1.0"
description: Formats single paragraph text into XML with proper tags (p, br, lists, quotes, emphasis)
task_type: formatting
role: formatting
required_variables:
  - source_language
optional_variables:
  - speaker_name
inputs:
  - name: source_language
    required: true
    strictness: strict
  - name: speaker_name
    required: false
    strictness: loose
tags:
  - xml
  - formatting
  - paragraphs
default_model: gpt-4o-mini
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Format the input paragraph as XML in {{ source_language }}.

{% if speaker_name %}
Speaker/author: {{ speaker_name }}.
{% endif %}

Requirements:
- Wrap the paragraph in `<p>` tags.
- Use other XML-style tags only when clearly needed, such as `<br>`, `<li>`, `<ol>`, `<ul>`, or `<blockquote>`.
- Correct clear logical, grammatical, speaking, or transcription errors.
- Preserve meaning and content.
- Do not summarize, omit, or add content.

Output only the final XML text.
