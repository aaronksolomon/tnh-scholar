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

The recommended pipeline uses tnh-gen for every stage, including the split:

```bash
# Step 1: Number raw lines (preprocessing — no model call)
awk '{print NR":"$0}' source.txt > source_numbered.txt

# Step 2: Section — tnh-gen identifies page/article breaks and produces metadata
tnh-gen run --prompt section_by_break \
  --input-file source_numbered.txt \
  --var source_language=Vietnamese \
  --var section_count=4 \
  --var metadata='{"title":"...","author":"..."}' \
  --output-file sections.json

# Step 3: Clean each section (focused per-page context)
for i in 1 2 3 4; do
  tnh-gen run --prompt default_clean_numbered \
    --input-file section_${i}_raw.txt \
    --var source_language=Vietnamese \
    --output-file section_${i}_clean.txt
done

# Step 4: Translate each section with full document context
for i in 1 2 3 4; do
  tnh-gen run --prompt default_line_translate \
    --input-file section_${i}_clean.txt \
    --vars sections.json \
    --var source_language=Vietnamese \
    --var target_language=English \
    --var style=scholarly \
    --output-file section_${i}_translated.txt
done

# Step 5: Combine
cat section_{1,2,3,4}_translated.txt > final_translated.txt
```

Processing section-by-section (rather than one large batch) keeps each model call focused on a single page's worth of content and contains errors locally. The `sections.json` produced in step 2 carries section titles, key concepts, and a document summary that give the translator full context for every section.

```bash
# Never: overwrite your only input copy
tnh-gen run --prompt default_clean --input-file source.txt --output-file source.txt
```

For the full walkthrough with a real OCR source, extraction helper script, and golden output structure, see the [Thầy Edited Journal Text Case Study](/user-guide/journal-pipeline-case-study.md).

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
