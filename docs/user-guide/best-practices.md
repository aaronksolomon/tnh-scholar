---
title: "Best Practices"
description: "This guide outlines recommended practices for using TNH Scholar effectively."
owner: ""
author: ""
status: current
created: "2025-02-01"
---
# Best Practices

This guide outlines recommended practices for using TNH Scholar effectively.

## General Guidelines

### Text Processing

#### 1. Input Preparation

- Ensure text files use consistent line endings
- Remove any special formatting or control characters
- Use UTF-8 encoding for all text files
- Consider running `nfmt` on input files to standardize formatting

#### 2. Language Handling

- Specify language codes explicitly when known
- Use ISO 639-1 two-letter codes (e.g., 'en', 'vi')
- Allow auto-detection only for simple cases

#### 3. File Management

- Keep original files backed up
- Use descriptive file names
- Maintain consistent directory structure
- Store intermediate results when running long pipelines

## Command-Line Tools

### TNH-Gen

#### 1. Prompt Selection

- Use default prompts for initial testing
- Create custom prompts for specific needs
- Test prompts with small samples first
- Document prompt modifications

#### 2. Pipeline Design

- Break complex processing into steps
- Use intermediate files for long pipelines
- Validate output at each stage
- Consider using `tee` for debugging

Example of good pipeline practice:

```bash
# Good: Save intermediate results
tnh-gen run --prompt punctuate --input-file input.txt --output-file punctuated.txt
tnh-gen run --prompt section --input-file punctuated.txt --output-file sections.json
tnh-gen run --prompt format_xml --input-file punctuated.txt --vars sections.json --output-file final.xml

# Not recommended: Overwrite the only copy without checkpoints
tnh-gen run --prompt format_xml --input-file input.txt --output-file input.txt
```

#### 3. Error Handling

- Check command exit codes
- Save error output for debugging
- Use verbose mode for troubleshooting
- Keep log files organized

### Audio-Transcribe

#### 1. Audio Processing

- Use appropriate chunk sizes for content
- Consider silence detection for natural breaks
- Monitor transcription quality
- Save intermediate audio chunks

#### 2. YouTube Downloads

- Verify video availability before batch processing
- Use CSV files for bulk operations
- Include timestamps when needed
- Save downloaded audio files

## Pattern Development

### 1. Pattern Design

- Keep patterns focused and single-purpose
- Include clear documentation
- Test with various input types
- Patterns are automatically version controlled using git.
  - Use git tools to inspect and manage versions.

### 2. Template Variables

- Use descriptive variable names
- Provide default values when appropriate
- Document required variables
- Test variable combinations

Example pattern structure:

```markdown
---
description: Example pattern for formatting
version: 1.0
author: TNH Scholar
---
Process this text according to these parameters:

Language: {{ language }}
Style: {{ style_convention }}
Review Count: {{ review_count }}

Additional instructions...
```

## Performance Optimization

### 1. Resource Management

- Monitor token usage
- Use appropriate batch sizes
- Consider chunking for large files
- Cache intermediate results

### 2. API Usage

- Implement rate limiting
- Handle API errors gracefully
- Monitor usage and costs
- Use appropriate models for tasks

## Testing and Validation

### 1. Input Validation

- Test with various file sizes
- Include different languages
- Check character encodings
- Verify line endings

### 2. Output Validation

- Verify file formats
- Check content integrity
- Validate XML structure
- Compare with expected results

### 3. Process Validation

- Monitor system resources
- Track processing time
- Log error conditions
- Document edge cases

## Security Considerations

### 1. API Keys

- Use environment variables
- Never commit keys to version control
- Rotate keys regularly
- Monitor API usage

### 2. File Handling

- Validate input files
- Use secure file permissions
- Clean up temporary files
- Handle sensitive content appropriately

## Documentation

### 1. Code Comments

- Document complex logic
- Explain pattern usage
- Note assumptions
- Include examples

### 2. Process Documentation

- Document workflows
- Create usage examples
- Update for changes
- Include troubleshooting guides
