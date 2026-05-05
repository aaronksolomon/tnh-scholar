---
title: "tnh-setup"
description: "The `tnh-setup` command configures the TNH Scholar environment, prepares local prompt directories, and verifies core runtime prerequisites."
owner: ""
author: ""
status: current
created: "2025-02-01"
updated: "2026-02-01"
---
# tnh-setup

The `tnh-setup` command configures the TNH Scholar environment, prepares local prompt directories, and verifies core runtime prerequisites.

## Usage

```bash
tnh-setup [OPTIONS]
```

## Options

```bash
--skip-env       Skip API key setup check
--skip-prompts  Skip prompt directory setup guidance
--skip-ytdlp-runtime  Skip yt-dlp runtime setup
--verify-only    Only run environment verification
-y, --yes        Assume yes for all prompts
--no-input       Fail if a prompt would be required
--help          Show this message and exit
```

## Configuration Steps

The setup process includes:

1. Directory Creation
   - Creates ~/.config/tnh-scholar/
   - Creates prompts directory for user-level overrides
   - Creates logs directory

2. Prompt Setup
   - Prepares ~/.config/tnh-scholar/prompts/ for local prompt overrides
   - Reports the repo-local default workspace: ./tnh-prompts/
   - Reports bundled runtime prompts at src/tnh_scholar/runtime_assets/prompts/
   - Does not download prompts from an external repository

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

# Skip prompt setup guidance
tnh-setup --skip-prompts

# Skip both
tnh-setup --skip-env --skip-prompts
```

### Verification Only

```bash
tnh-setup --verify-only
```

## Prompt Locations

`tnh-setup` prepares and reports three prompt locations:

- Repo-local default workspace: `./tnh-prompts/` when running inside the repository
- User prompt directory: `~/.config/tnh-scholar/prompts/`
- Bundled runtime prompts: `src/tnh_scholar/runtime_assets/prompts/`

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

### Prompt Setup Issues

- Ensure write permissions in the config directory
- Confirm the repository contains `tnh-prompts/` when working from source
- Use `TNH_PROMPT_DIR` or `--prompt-dir` if you intentionally store prompts elsewhere

## Post-Setup Verification

After running setup, verify:

1. Directory Structure:

   ```plaintext
   ~/.config/tnh-scholar/
   ├── prompts/
   └── logs/
   ```

2. Prompt Files:
   - Check that repo-local prompts are present in `./tnh-prompts/` when working from source
   - Check `~/.config/tnh-scholar/prompts/` for user overrides if you use them
   - Verify file permissions

3. Environment:
   - Confirm API key is set
   - Test basic AI functionality
