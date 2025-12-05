---
title: "token-count"
description: "The `token-count` command calculates the OpenAI API token count for text input. This is useful for ensuring that a text is within maximum token limits for the API model and also for estimating API costs."
owner: ""
author: ""
status: processing
created: "2025-02-01"
---
# token-count

The `token-count` command calculates the OpenAI API token count for text input. This is useful for ensuring that a text is within maximum token limits for the API model and also for estimating API costs.

## Usage

```bash
token-count [INPUT_FILE]
```

If no input file is specified, reads from standard input (stdin).

## Examples

### Count Tokens in File

```bash
token-count input.txt
```

### Count Tokens from Stdin

```bash
echo "Sample text" | token-count
cat input.txt | token-count
```

### Pipeline Usage

```bash
# Count tokens after processing
cat input.txt | tnh-fab punctuate | token-count

# Count tokens at multiple stages
cat input.txt | tee >(token-count >&2) | \
  tnh-fab punctuate | tee >(token-count >&2) | \
  tnh-fab process -p format_xml | token-count
```

## Output

Returns a single integer representing the number of tokens in the input text, calculated using the OpenAI tokenizer.

## Notes

- Uses the same tokenizer as GPT-4
- Counts are exact matches to OpenAI API usage
- Useful for:
  - Cost estimation
  - Context window planning
  - Processing pipeline optimization
  - Model input validation

## See Also

- OpenAI tokenizer documentation
- TNH Scholar API documentation for token counting
- tnh-fab documentation for text processing