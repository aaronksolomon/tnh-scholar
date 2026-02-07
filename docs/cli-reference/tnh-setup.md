---
title: "tnh-setup"
description: "The `tnh-setup` command configures the TNH Scholar environment, setting up necessary directories and downloading default prompts."
owner: ""
author: ""
status: current
created: "2025-02-01"
updated: "2026-02-01"
---
# tnh-setup

The `tnh-setup` command configures the TNH Scholar environment, setting up necessary directories and downloading default prompts.

## Usage

```bash
tnh-setup [OPTIONS]
```

## Options

```bash
--skip-env       Skip API key setup check
--skip-prompts  Skip prompt download
--skip-ytdlp-runtime  Skip yt-dlp runtime setup
--verify-only    Only run environment verification
-y, --yes        Assume yes for all prompts
--no-input       Fail if a prompt would be required
--help          Show this message and exit
```

## Configuration Steps

The setup process includes:

1. Directory Creation
   - Creates ~/.config/tnh_scholar/
   - Creates prompts directory
   - Creates logs directory

2. Prompt Download
   - Offers to download default prompts from GitHub
   - Prompts are saved to ~/.config/tnh_scholar/prompts/
   - Maintains directory structure from repository

3. Environment Check
   - Verifies OpenAI API key configuration
   - Provides guidance if key is missing

4. yt-dlp Runtime Setup
   - Offers to install a JS runtime (deno/node/bun)
   - Offers to install curl_cffi for impersonation support

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

# Skip prompt download
tnh-setup --skip-prompts

# Skip both
tnh-setup --skip-env --skip-prompts
```

### Verification Only

```bash
tnh-setup --verify-only
```

## Default Prompts

When downloading prompts, the following are included:

- default_punctuate.md
- default_section.md
- default_line_translation.md
- default_xml_format.md
- default_xml_paragraph_format.md

## Environment Variables

The setup process checks for and uses:

- OPENAI_API_KEY: Required for AI functionality
- TNH_PROMPT_DIR: Optional custom prompt directory

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

### Prompt Download Issues

- Check internet connection
- Verify GitHub access
- Ensure write permissions in config directory
- Check disk space

## Post-Setup Verification

After running setup, verify:

1. Directory Structure:

   ```plaintext
   ~/.config/tnh_scholar/
   ├── prompts/
   └── logs/
   ```

2. Prompt Files:
   - Check that prompt files are present
   - Verify file permissions
   - Ensure proper formatting

3. Environment:
   - Confirm API key is set
   - Test basic AI functionality
