# TNH-FAB Command Line Tool Specification

## Overview

`tnh-fab` is a command-line text processing tool providing standalone but pipeable operations for Buddhist text processing. It is part of the `tnh-scholar` suite of tools, focusing on simplicity, flexibility, and consistent behavior.

## Core Functionality

- Text punctuation and formatting
- Section creation and management
- Translation (line-by-line and block)
- Pattern-based text processing
- XML/structured output generation

## Command Structure

```bash
tnh-fab <command> [options] [input_file]
```

### Global Options

```plaintext
Input/Output:
  [input_file]                Input file (optional, uses STDIN if not provided)
  -o, --output FILE          Output file (default: STDOUT)
  -d, --output-dir DIR       Output directory (default: current)
  -f, --format FORMAT        Output format: txt/json/yaml/xml (default varies by command)

Configuration:
  -l, --language LANG        Source language code (auto-detect if not specified)
  -t, --template FILE        Template values file (YAML format)
  -k, --key-values PAIRS     Space-separated key:value pairs (e.g., speaker:"Name")
  -p, --pattern NAME         Pattern name (command-specific default if not specified)
  -c, --review-count NUM       Number of review passes (default: 3)

Logging:
  -v, --verbose             Enable detailed logging
  --debug                   Enable debug output
  --quiet                   Suppress all non-error output

Other:
  -h, --help               Show command-specific help
  --version                Show version information
```

### Commands

#### punctuate

Add punctuation and structure to text.

```plaintext
Additional Options:
  -y, --style STYLE            Punctuation style (default: configuration file)
```

#### section

Create and manage text sections.

```plaintext
Additional Options:
  -n, --num-sections NUM   Target number of sections (default: auto)
  --target-section-size NUM   Target section size in tokens (default: configuration file)
```

#### translate

Perform line-by-line or block translation.

```plaintext
Additional Options:
  -r, --target LANG        Target language code (default: en)
  -y, --style STYLE            Translation style (default: configuration file)
  --context-lines NUM      Number of context lines (default: 3)
  --segment-size NUM       Lines per translation segment (default: auto)
```

#### process

Execute pattern-based text processing. Can work on sections of data or on the whole input stream.

```plaintext
Additional Options:
  -s, --sections FILE      JSON file containing section data
  -g, --paragraph         Use line-separated paragraphs as sections
  --xml                   Wrap output in XML style document tags
```

## Input/Output Handling

### Input Sources
- File specified as argument
- STDIN (piped input)
- Section data (JSON format)
- Template files (YAML format)

### Input Processing
1. Text content priority:
   - Named input file
   - STDIN if no file specified
   - Error if neither available

2. Section data priority:
   - JSON file specified with -s
   - STDIN when paired with input file
   - Auto-generated sections if no pattern specified

3. Template values priority:
   - Command line key-values (-k)
   - Template file values (-t)
   - Default values from pattern
   - Environment variables (TNH_FAB_*)

### Output Handling
1. Output destination priority:
   - File specified by -o
   - STDOUT if no file specified

2. Format determination:
   - Format specified by -f
   - Default format by command:
     - punctuate: txt
     - section: json
     - translate: txt
     - process: txt


## Pattern Management

### Pattern Resolution
1. Pattern name sources (in order):
   - Command line (-p)
   - Command defaults:
     - punctuate: default_punctuate
     - section: default_section
     - translate: default_translate
     - process: NO DEFAULT (must be specified)

2. Pattern search paths:
   - Path specified in configuration
   - ~/.config/tnh_scholar/patterns/

### Template Value Processing

1. Key-Value Format:
   ```
   key:value key2:"value with spaces"
   ```
   - Keys must be valid identifiers
   - Values with spaces must be quoted
   - Invalid formats raise error

2. Template File Format (YAML):
   ```yaml
   key1: value1
   key2: value2
   ```

3. Environment Variables:
   - Format: TNH_FAB_{KEY}
   - Lowest priority in template resolution

## Pipeline Behavior

### Data Flow
- All commands accept STDIN
- All commands can output to STDOUT
- Section data can flow through pipeline
- Binary data not supported

### Pipeline Examples
```bash
# Punctuate and section
cat input.txt | tnh-fab punctuate | tnh-fab section > sections.json

# Section and process
tnh-fab section input.txt | tnh-fab process -p format_xml > output.xml

# Complete pipeline
cat input.txt | \
  tnh-fab punctuate -l vi | \
  tnh-fab section -n 5 | \
  tnh-fab process -p format_xml -k speaker:"Thay" > output.xml
```

1. **Single File Input**
   ```bash
   tnh-fab process -p format_xml input.txt
   ```
   - Processes input.txt directly. No sectioning is performed.

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


## Configuration

### Configuration Files

1. User: ~/.config/tnh_scholar/tnh-fab/config.yaml
2. Project: ./.tnh-fab.yaml
3. Priority: Project > User

### Configuration Format
```yaml
defaults:
  language: auto
  output_format: txt
  
punctuate:
  pattern: default_punctuate
  style: APA
  review_count: 3
  
section:
  pattern: default_section
  review_count: 3
  
translate:
  pattern: default_translate
  target_language: en
  style: "American Dharma Teaching"
  context_lines: 3
  review_count: 3
  
process:
  wrap_document: true
  
patterns:
  path: ~/.config/tnh_scholar/patterns
  
logging:
  level: INFO
  file: ~/.tnh-fab.log
```

## Error Handling

### Error Categories
1. Input Errors
   - Missing required input
   - Invalid file formats
   - Encoding issues
   - Section/input mismatch

2. Pattern Errors
   - Missing required pattern
   - Pattern not found
   - Invalid pattern format

3. Template Errors
   - Invalid template format
   - Missing required values
   - Invalid key-value syntax

4. Processing Errors
   - AI service errors
   - Timeout errors
   - Validation failures

### Error Reporting
- Standard error format
- Error codes for scripting
- Detailed logging with -v
- Stack traces with --debug

## Exit Codes
```
0  Success
1  General error
2  Input error
3  Pattern error
4  Template error
5  Processing error
64-73  Command-specific errors
```

## Development Notes

### Key Decision Points
1. Pattern Management:
   - Consider pattern versioning
   - Pattern validation requirements
   - Pattern update mechanism

2. Pipeline Handling:
   - Memory management for large files
   - Progress indication in pipelines
   - Error propagation in pipelines

3. Configuration:
   - Environment variable handling
   - Configuration validation
   - Configuration migration

4. Testing Requirements:
   - Unit test coverage requirements
   - Integration test scenarios
   - Performance benchmarks

### Future Considerations
1. Additional Commands:
   - Format validation
   - Pattern management
   - Batch processing

2. Extensions:
   - Plugin system
   - Custom pattern repositories
   - API integration

3. Integration:
   - CI/CD requirements
   - Packaging requirements
   - Documentation generation