---
title: "TNH FAB Design Document"
description: "First-generation design of the `tnh-fab` CLI covering core commands, usage patterns, and processing goals."
owner: ""
author: ""
status: current
created: "2025-01-21"
---
# TNH FAB Design Document

First-generation design of the `tnh-fab` CLI covering core commands, usage patterns, and processing goals.

## Overview
`tnh-fab` is a command-line text processing tool that provides standalone but pipeable text processing operations, with a focus on simplicity and flexibility. It is part of the `tnh-scholar` suite of tools.

## Core Functionality
- Text punctuation
- Section creation and management 
- Translation (line-by-line and block)
- General text processing with patterns

## Command Structure
```bash
tnh-fab <command> [options] [input_file]
```

Commands:
- `punctuate`: Add punctuation and structure to text
- `section`: Create text sections
- `translate`: Perform line-by-line translation
- `process`: Execute pattern-based text processing (typically outputting XML format)

## Global Options
```
-d, --output-dir DIR     Output directory (default: current)
-v, --verbose            Detailed logging
-l, --language LANG     Source language code of input text (auto-detect if not specified)
```

## Command-Specific Options

### Punctuate
```
-p, --pattern NAME       Pattern name for punctuation (uses default if not specified)
-y, --style STYLE       Punctuation style (default: APA)
-o, --output FILE       Output file (default: stdout or FILE_punct.txt)
```

### Section
```
-p, --pattern NAME      Pattern name for sectioning
-n, --num NUM          Target number of sections
-o, --output FILE      Output JSON file (default: stdout or FILE_sections.json)
```

### Translate
```
-p, --pattern NAME      Pattern for translation (uses default if not specified)
-t, --template FILE     Template values file
-o, --output FILE      Output file (default: stdout)
-r, --target LANG       The target output language code (default is 'en,' English)
```

### Process
```
-p, --pattern NAME      Pattern for processing (REQUIRED)
-g, --paragraph         Use line separated paragraphs as sections.
-s, --sections FILE     JSON file containing section data
-t, --template FILE     Template values file
-f, --format FORMAT     Output format: txt/json/yaml (default: txt)
-o, --output FILE      Output file (default: stdout)
```

## Usage Examples

### Basic Usage
```bash
# Punctuate text
tnh-fab punctuate input.txt
tnh-fab punctuate -l vi input.txt > punctuated.txt

# Create sections
tnh-fab section input.txt -n 5 -o sections.json
cat input.txt | tnh-fab section > sections.json

# Translate text
tnh-fab translate input.txt -p vi_en
cat input.txt | tnh-fab translate -p vi_en > translated.txt

# Process with pattern
tnh-fab process -p format_xml -s sections.json input.txt
cat sections.json | tnh-fab process -p format_xml input.txt

# Process by paragraphs
tnh-fab process -g -p format_xml input.txt
```

### Pipeline Examples
```bash
# Punctuate and section
cat input.txt | tnh-fab punctuate | tnh-fab section > sections.json

# Section and process
tnh-fab section input.txt | tnh-fab process -p format_xml > output.xml

# Translate and process
cat input.txt | tnh-fab translate | tnh-fab process -p format_md
```

## Configuration

### Directory Structure
```
~/.config/tnh_scholar/
├── patterns/           # Pattern files
│   ├── punctuate/
│   ├── section/
│   ├── translate/
│   └── process/
└── tnh-fab/
    └── settings.yaml   # Default configurations
```

### Default Configuration (settings.yaml)
```yaml
defaults:
  punctuate:
    pattern: default_punctuate
    style: APA
    language: auto
  section:
    pattern: default_section
    num_sections: auto
    review_count: 3
  translate:
    pattern: default_translate
  process:
    format: txt

pattern_path: ~/.config/tnh_scholar/patterns
```

## Input/Output Handling

### Input Sources
- File specified as argument
- STDIN (piped input)
- Section data (JSON format)
- Template files (YAML format)

### Output Handling
- STDOUT (default for piping)
- Specified output file (-o)
- Default file naming (if no -o): input_stage.ext
- JSON output for sections

## Pattern Management
- Uses existing PatternManager class for pattern resolution
- Uses configured Pattern path

## Special Notes
1. Translation is implemented as a standalone command (`translate`) for line-by-line processing, however can also be accomplished as a process pattern option for section translation
2. Each command is standalone but designed for pipeline compatibility
3. All commands default to STDIN/STDOUT unless specific files are provided
4. Section data is always in JSON format for compatibility

---
---

# TNH-FAB PROCESS: detailed Specification

## Overview
The `process` command applies pattern-based text processing using optional section data. It can receive input from files and/or STDIN, with flexible output options. Typical usage is XML output.

## Command Format
```bash
tnh-fab process [options] [input_file]
```

## Options
```
-p, --pattern NAME      Pattern name for processing (REQUIRED)
-s, --sections FILE     JSON file containing section data
-g, --paragraph         Process text by newliine separated paragraphs
-t, --template FILE     Template values file (YAML format)
-k, --key-values PAIRS  Space-separated key:value pairs (e.g., speaker:"Name" title:"Title")
-f, --format FORMAT     Output format: XML/txt (default: XML)
-o, --output FILE      Output file (default: stdout)
```

## Input Handling

### Input Sources
- Text content can come from:
  - File specified as argument
  - STDIN
- Section data can come from:
  - JSON file specified with -s
  - STDIN when paired with input file

### Input Scenarios

1. **Single File Input**
   ```bash
   tnh-fab process -p format_xml input.txt
   ```
   - Processes input.txt directly

2. **STDIN Only**
   ```bash
   cat input.txt | tnh-fab process -p format_xml
   cat input.txt | tnh-fab process -g -p format_xml  # process by paragraphs
   ```
   - Processes text from STDIN

3. **File + Sections File**
   ```bash
   tnh-fab process -p format_xml -s sections.json input.txt
   ```
   - Processes input.txt using sections from sections.json

4. **STDIN + Sections File**
   ```bash
   cat input.txt | tnh-fab process -p format_xml -s sections.json
   ```
   - Processes STDIN text using sections from sections.json

5. **Section Stream + Input File**
   ```bash
   tnh-fab section input.txt | tnh-fab process -p format_xml input.txt
   ```
   - Processes input.txt using sections from STDIN

### Input Validation
- When sections are provided (via -s or STDIN):
  - Validates JSON format matches TextObject schema
  - Checks source_file field in TextObject if present
  - Warns if source_file doesn't match input file name
  - Validates section line ranges against input text

## Template Value Handling

### Priority Order (highest to lowest)
1. Command line key-values (-k)
2. Template file values (-t)
3. Default values from pattern

### Key-Value Format
- Space-separated pairs
- Key and value joined by colon
- Values with spaces must be quoted
- Example: `speaker:"Robert Smith" title:"My Journey"`

## Output Handling

### Output Destinations
- STDOUT (default)
- File specified by -o option

### Format Options
- txt (default): Plain text output
- json: JSON formatted output
- yaml: YAML formatted output

## Error Handling

### Input Errors
- Missing required pattern
- Invalid section JSON format
- Section/input file mismatch
- Missing input when required

### Template Errors
- Invalid template file format
- Invalid key-value pair format
- Missing required template values

## Usage Examples

```bash
# Basic file processing
tnh-fab process -p format_pattern input.txt > output.xml

# Process with template values
tnh-fab process -p format_pattern -k speaker:"Robert Smith" input.txt

# Process with sections file
tnh-fab process -p format_pattern -s sections.json input.txt

# Process STDIN with sections
cat input.txt | tnh-fab process -p format_pattern -s sections.json

# Pipeline from section command
tnh-fab section input.txt | tnh-fab process -p format_pattern input.txt
 
# Complete example with all options
tnh-fab process -p format_pattern \
  -s sections.json \
  -t template.yaml \
  -k speaker:"Robert Smith" \
  -f json \
  -o output.json \
  input.txt
```
