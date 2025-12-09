---
title: "sent-split"
description: "Split text into sentences using NLTK, with newline or space separators."
owner: ""
author: "Codex"
status: current
created: "2025-12-10"
---
# sent-split

CLI tool for splitting text into sentences. Reads from a file (or stdin) and writes to stdout or a specified file. Uses NLTK sentence tokenization.

## Usage

```bash
sent-split [OPTIONS] [INPUT_FILE]
```

If `INPUT_FILE` is omitted, the tool reads from stdin.

## Options

- `-o, --output PATH` — Optional output file (default: stdout).
- `-s, --space` — Separate sentences with spaces instead of newlines.

## Examples

```bash
# Split a text file into sentences (newline-separated)
sent-split notes.txt --output sentences.txt

# Split via stdin and print to stdout
cat notes.txt | sent-split

# Space-separated sentences
sent-split notes.txt --space
```
