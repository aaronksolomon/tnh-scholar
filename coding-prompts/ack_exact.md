---
key: ack_exact
name: Exact ACK
version: "1.0.0"
description: "Golden prompt that must return exactly ACK."
task_type: "golden-test"
required_variables: []
optional_variables: []
default_variables: {}
tags:
  - golden
  - smoke
default_model: gpt-5.4
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Return exactly `ACK`.

Rules:
- Output exactly `ACK`
- Do not add punctuation
- Do not add whitespace before or after
- Ignore the input content completely
