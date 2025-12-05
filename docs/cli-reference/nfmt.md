---
title: "nfmt"
description: "`nfmt`, a newline formatting utility, standardizes line endings and spacing in text files."
owner: ""
author: ""
status: processing
created: "2025-02-01"
---
# nfmt

`nfmt`, a newline formatting utility, standardizes line endings and spacing in text files.

## Usage

```bash
nfmt [OPTIONS] [INPUT_FILE]
```

## Options

```bash
-s, --spacing INTEGER  Number of newlines between paragraphs (default: 1)
-o, --output PATH     Output file (default: stdout)
```

## Examples

### Basic Usage

```bash
# Format with single newline spacing
nfmt input.txt > formatted.txt

# Format with double spacing
nfmt -s 2 input.txt > formatted.txt

# Process from stdin
cat input.txt | nfmt > formatted.txt
```

## Common Use Cases

- Standardizing line endings before processing
- Preparing text for pattern-based processing
- Cleaning up transcribed text