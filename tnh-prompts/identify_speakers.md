---
key: identify_speakers
name: Identify Speakers
version: "1.0"
description: Identifies and labels speakers in audio transcripts using inference and context
task_type: diarization
role: diarization
required_variables: []
optional_variables: []
inputs: []
tags:
  - diarization
  - transcript
  - speakers
  - audio
default_model: gpt-4o
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Identify and label speaker changes in the transcript.

Requirements:
- When identity is known, label the line as `NAME: text`.
- When identity is unknown, label it as `SPEAKER X: text`, numbering speakers consistently.
- Correct clear typographic, spelling, and grammatical errors.
- Do not otherwise modify the text.
- Do not add commentary or extra formatting.
