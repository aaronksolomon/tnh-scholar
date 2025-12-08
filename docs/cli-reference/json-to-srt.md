---
title: "json-to-srt"
description: "Convert JSONL transcription output (from audio-transcribe) into SRT subtitle files."
owner: ""
author: "Codex"
status: current
created: "2025-12-10"
---
# json-to-srt

Command-line utility that converts JSONL transcription files (from `audio-transcribe`) into standard SRT subtitle output. Reads from stdin by default and writes to stdout unless an output path is provided.

## Usage

```bash
json-to-srt [OPTIONS] [INPUT_FILE]
```

If `INPUT_FILE` is omitted, the tool reads JSONL input from stdin. Use `-o/--output` to write the SRT result to a file.

## Options

- `-o, --output PATH` — Optional output file path (default: stdout).

## Examples

```bash
# Convert a JSONL transcript to SRT and print to terminal
json-to-srt transcript.jsonl

# Convert and write to a file
json-to-srt transcript.jsonl --output transcript.srt

# Stream from stdin and write to stdout
cat transcript.jsonl | json-to-srt
```
