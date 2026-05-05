---
title: "Configuration"
description: "TNH Scholar requires some initial configuration to function properly. This guide covers the essential configuration steps and options."
owner: ""
author: ""
status: current
created: "2025-02-01"
---
# Configuration

TNH Scholar requires some initial configuration to function properly. This guide covers the essential configuration steps and options.

## Environment Setup

### OpenAI API Key

TNH Scholar's AI functionality requires an OpenAI API key. To configure this:

1. Obtain an API key from [OpenAI's platform](https://platform.openai.com/api-keys)
2. Set the environment variable:

   ```bash
   # Linux/Mac
   export OPENAI_API_KEY='your-api-key-here'
   
   # Windows
   set OPENAI_API_KEY=your-api-key-here
   ```

In development configuration (where you have downloaded the tnh-scholar repository) you can also use a `.env` file in your project directory:

```bash
OPENAI_API_KEY=your-api-key-here
```

### Directory Structure

TNH Scholar creates and uses the following directory structure:

```plaintext
~/.config/tnh-scholar/
├── prompts/          # User prompt overrides
└── logs/            # Log files
```

## Prompt Configuration

### Prompt Directory

Prompts can be stored in:

1. Repo-local default workspace: `./tnh-prompts/` when running from the `tnh-scholar` repo root
2. User override location: `~/.config/tnh-scholar/prompts/`
3. Custom location specified by `TNH_PROMPT_DIR` environment variable

To use a custom prompt directory:

```bash
export TNH_PROMPT_DIR=/path/to/prompts
```

### Default Prompts

The current prototype workflow uses the tracked repo-local `tnh-prompts/` workspace.
Bundled runtime prompts remain available in `src/tnh_scholar/runtime_assets/prompts/`,
and `~/.config/tnh-scholar/prompts/` can be used for local overrides.

## Configuration File

The system looks for configuration in this order:

1. Command line arguments
2. Environment variables
3. Workspace config: `./.tnh-gen.json` (or `.vscode/tnh-scholar.json`)
4. User-level config: `~/.config/tnh-scholar/tnh-gen.json`

Example configuration file:

```json
{
  "prompt_catalog_dir": "/path/to/prompts",
  "default_model": "gpt-5-mini",
  "max_dollars": 0.30,
  "max_input_chars": 120000,
  "default_temperature": 1.0,
  "api_key": "sk-..."
}
```

## Initial Setup

The `tnh-setup` command automates configuration:

```bash
# Full setup
tnh-setup

# Skip specific steps
tnh-setup --skip-env        # Skip API key check
tnh-setup --skip-prompts   # Skip prompt setup guidance
```

This will:

1. Create necessary directories
2. Prepare the user prompt directory and report prompt locations
3. Check for OpenAI API key
4. Set up basic configuration
