---
key: test
name: Test
version: "1.0"
description: Test prompt for GenAI service module - summarizes input into single sentence
task_type: testing
role: testing
required_variables: []
optional_variables: []
inputs: []
tags:
  - test
  - development
default_model: gpt-4o-mini
output_contract:
  mode: text
output_mode: text
safety_level: safe
schema_version: "1.0"
---

Summarize the input in a single coherent sentence.

Return only the sentence.
