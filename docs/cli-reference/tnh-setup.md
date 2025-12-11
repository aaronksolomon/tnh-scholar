---
title: "tnh-setup"
description: "The `tnh-setup` command configures the TNH Scholar environment, setting up necessary directories and downloading default patterns."
owner: ""
author: ""
status: current
created: "2025-02-01"
---
# tnh-setup

The `tnh-setup` command configures the TNH Scholar environment, setting up necessary directories and downloading default patterns.

## Usage

```bash
tnh-setup [OPTIONS]
```

## Options

```bash
--skip-env       Skip API key setup check
--skip-patterns  Skip pattern download
--help          Show this message and exit
```

## Configuration Steps

The setup process includes:

1. Directory Creation
   - Creates ~/.config/tnh_scholar/
   - Creates patterns directory
   - Creates logs directory

2. Pattern Download
   - Offers to download default patterns from GitHub
   - Patterns are saved to ~/.config/tnh_scholar/patterns/
   - Maintains directory structure from repository

3. Environment Check
   - Verifies OpenAI API key configuration
   - Provides guidance if key is missing

## Examples

### Complete Setup

```bash
# Run full setup
tnh-setup
```

### Selective Setup

```bash
# Skip API key check
tnh-setup --skip-env

# Skip pattern download
tnh-setup --skip-patterns

# Skip both
tnh-setup --skip-env --skip-patterns
```

## Default Patterns

When downloading patterns, the following are included:

- default_punctuate.md
- default_section.md
- default_line_translation.md
- default_xml_format.md
- default_xml_paragraph_format.md

## Environment Variables

The setup process checks for and uses:

- OPENAI_API_KEY: Required for AI functionality
- TNH_PATTERN_DIR: Optional custom pattern directory

## Troubleshooting

### Missing API Key

If the OpenAI API key is not found, the setup tool displays guidance:

```
>>>>>>>>>> OpenAI API key not found in environment. <<<<<<<<<

For AI processing with TNH-scholar:

1. Get an API key from https://platform.openai.com/api-keys
2. Set the OPENAI_API_KEY environment variable:

   export OPENAI_API_KEY='your-api-key-here'  # Linux/Mac
   set OPENAI_API_KEY=your-api-key-here       # Windows

For OpenAI API access help: https://platform.openai.com/
```

### Pattern Download Issues

- Check internet connection
- Verify GitHub access
- Ensure write permissions in config directory
- Check disk space

## Post-Setup Verification

After running setup, verify:

1. Directory Structure:

   ```plaintext
   ~/.config/tnh_scholar/
   ├── patterns/
   └── logs/
   ```

2. Pattern Files:
   - Check that pattern files are present
   - Verify file permissions
   - Ensure proper formatting

3. Environment:
   - Confirm API key is set
   - Test basic AI functionality