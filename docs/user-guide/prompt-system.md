---
title: "TNH Scholar Prompt System"
description: "How to use, locate, and create prompts for tnh-gen text processing pipelines."
owner: ""
author: ""
status: current
created: "2025-01-19"
updated: "2026-04-28"
---

# TNH Scholar Prompt System

The TNH Scholar Prompt System manages the text processing templates that power `tnh-gen`. Prompts are Jinja2-templated Markdown files with YAML frontmatter, stored in prompt directories and loaded by name at runtime.

> **Terminology note**: Earlier versions of the project called these files *patterns* and the management layer *PatternManager*. The current system uses *prompts* and `PromptCatalog`. The two terms refer to the same concept; the older terminology appears in legacy notebooks and archived code.

---

## Core Concepts

### Prompt File

A prompt file is a `.md` file with two parts:

- **YAML frontmatter** — metadata, required/optional variables, model defaults, output contract
- **Template body** — the instruction text, using `{{ variable }}` for Jinja2 substitution

Example:

```markdown
---
key: example_prompt
name: Example Prompt
version: "1.0"
description: Processes text in a given language and style
required_variables:
  - source_language
optional_variables:
  - style_convention
default_variables:
  source_language: English
  style_convention: APA
default_model: gpt-4o-mini
output_mode: text
schema_version: "1.0"
---

Process the input text in {{ source_language }} using {{ style_convention }} conventions.

Output only the processed text.
```

When a variable has a `default_variables` entry, it can be omitted from the command line and the default applies. Required variables with no default must be supplied via `--var` or `--vars`.

### Prompt Catalog

The `PromptCatalog` is the runtime interface that discovers and loads prompts from the prompt directory. It is used internally by `tnh-gen` and can also be used programmatically.

---

## Using Prompts

### Through tnh-gen CLI

The primary interface for prompts is `tnh-gen`:

```bash
# List all available prompts
tnh-gen list

# Run a prompt with an input file
tnh-gen run --prompt default_punctuate \
  --input-file transcript.txt \
  --var source_language=Vietnamese

# Pass variables from a JSON file (useful for complex or reused variable sets)
tnh-gen run --prompt default_line_translate \
  --input-file cleaned.txt \
  --vars sections.json \
  --var source_language=Vietnamese \
  --var target_language=English \
  --var style=scholarly

# Inline variable overrides take precedence over --vars file values
tnh-gen run --prompt default_section \
  --input-file cleaned_numbered.txt \
  --vars base_vars.json \
  --var target_section_count=4
```

See [tnh-gen CLI Reference](/cli-reference/tnh-gen.md) for the full variable precedence rules and output options.

### Programmatic Usage

For developers integrating the prompt system into tools or scripts:

```python
from tnh_scholar.ai_text_processing import Prompt, PromptCatalog

# Initialize the catalog from the prompt directory
catalog = PromptCatalog(prompt_dir)

# Load a prompt by key
prompt = catalog.load("default_punctuate")

# Render the template with variable values
rendered = prompt.apply_template({
    "source_language": "Vietnamese",
    "style_convention": "APA"
})
```

---

## Prompt Location

By default, runtime prompt discovery checks:

```
./tnh-prompts/
~/.config/tnh-scholar/prompts/
src/tnh_scholar/runtime_assets/prompts/
```

For repo-local work in `tnh-scholar`, the default workspace is:

```bash
./tnh-prompts/
```

Use `--prompt-dir` or `TNH_PROMPT_DIR` only when you intentionally want to override that default:

```bash
# In .bashrc, .zshrc, or similar:
export TNH_PROMPT_DIR=/path/to/prompts
```

Or in a `.env` file for development installations.

Resolution order:

1. `TNH_PROMPT_DIR` environment variable (if set)
2. Workspace prompt directory: `./tnh-prompts/`
3. User prompt directory: `~/.config/tnh-scholar/prompts/`
4. Bundled runtime prompts in `src/tnh_scholar/runtime_assets/prompts/`

When `tnh-gen run --prompt my_prompt` is invoked, the system searches for `my_prompt.md` in the prompt directory and its subdirectories.

### Default Prompts

The repo-local `tnh-prompts/` workspace and bundled runtime prompts include the core prompts used by the current pipelines:

| Key | File | Purpose |
|-----|------|---------|
| `default_clean` | `default_clean.md` | OCR artifact removal, plain text output (Track A) |
| `default_clean_numbered` | `default_clean_numbered.md` | OCR artifact removal, `N:LINE` numbered output (Track B) |
| `default_punctuate` | `default_punctuate.md` | Add punctuation and paragraph breaks |
| `default_section` | `default_section.md` | Divide numbered transcript into sections with metadata |
| `default_line_translate` | `default_line_translate.md` | Line-by-line translation with section context |

These can be customised by creating a prompt with the same key in your prompt directory — your version takes precedence.

---

## Creating Prompts

A valid prompt file requires:

1. A unique `key` in the frontmatter
2. Valid Jinja2 template syntax in the body
3. All variables referenced in the body declared in `required_variables` or `optional_variables`

Minimal example:

```markdown
---
key: my_reformat
name: My Reformat Prompt
version: "1.0"
description: Reformats input text
required_variables:
  - source_language
default_variables:
  source_language: English
default_model: gpt-4o-mini
output_mode: text
schema_version: "1.0"
---

Reformat the following {{ source_language }} text with consistent paragraph spacing.

Output only the reformatted text.
```

Save the file as `my_reformat.md` in your prompt directory. It is immediately available as:

```bash
tnh-gen run --prompt my_reformat --input-file input.txt
```

### Version Control

Prompt files are ordinary files. If they live in a git-tracked workspace such as
`tnh-prompts/`, changes are versioned through normal repository commits. User-level
prompt directories under `~/.config/tnh-scholar/` are local by default unless you
choose to place them under version control yourself.

---

## Best Practices

### Prompt Naming

- Use `lowercase_with_underscores`
- Include the purpose: `default_clean`, `translate_section_thay_en`
- Prefix with `default_` only for the canonical, general-purpose versions

### Template Design

- Declare all variables in frontmatter — required or optional
- Provide `default_variables` values wherever reasonable to reduce command-line verbosity
- End every prompt with an explicit output instruction ("Output only the cleaned text. Do not add comments.")
- Keep prompts single-purpose; chain them in pipelines rather than combining tasks

### Testing

- Test new prompts with a small representative sample before running on full documents
- For prompts that feed into each other (e.g., `default_clean_numbered` → `default_section`), verify the output format of each stage matches what the next stage expects
- Store test inputs and expected outputs alongside the prompt or in a golden test directory
