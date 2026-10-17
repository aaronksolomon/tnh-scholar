---
key: sr-d-paragraph-blocks
name: Sr. D Paragraph Blocks
version: "1.0"
description: "Insert paragraph breaks into English talk transcripts without changing their words or punctuation."
role: formatting
required_variables: []
optional_variables: []
tags:
  - formatting
  - transcription
default_model: gpt-5-mini
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Format the entire English transcript into readable paragraph blocks.

This is strictly a whitespace-only transformation. Copy every word and every
punctuation mark exactly as provided, in the same order. Your only permitted
change is to replace spaces or existing line breaks between sentences with
paragraph breaks (two newline characters).

Group related sentences into natural paragraphs. Start a new paragraph when
the speaker changes topic, begins a new example, or moves between an example
and an explanation. Avoid making every sentence a separate paragraph.

Preserve all repetitions, false starts, audience interactions, quotations,
lists, stories, greetings, and closing remarks. Do not correct grammar,
punctuation, spelling, names, or transcription errors. Do not summarize,
shorten, rewrite, omit, or add anything. Do not add headings, metadata,
Markdown wrappers, or commentary.

Return the complete transcript, from its first word through its last word,
with blank lines between paragraphs. Before returning it, verify that
removing whitespace from your output produces exactly the same character
sequence as removing whitespace from the input transcript.
