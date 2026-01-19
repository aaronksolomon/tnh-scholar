---
title: "Command Line Tools Overview"
description: "TNH Scholar provides a suite of command-line tools designed to work together for text processing. Each tool focuses on specific tasks while maintaining consistent interfaces and behavior. This overview introduces the available tools and their primary functions."
owner: ""
author: ""
status: current
created: "2025-02-01"
---
# Command Line Tools Overview

TNH Scholar provides a suite of command-line tools designed to work together for text processing. Each tool focuses on specific tasks while maintaining consistent interfaces and behavior. This overview introduces the available tools and their primary functions. 

## Available tools

### Core CLI Tools

- **[tnh-gen](/cli-reference/tnh-gen.md)** – Unified GenAI-powered text processing CLI (NEW)
- **[audio-transcribe](/cli-reference/audio-transcribe.md)** – Transcribe audio files with diarization
- **[nfmt](/cli-reference/nfmt.md)** – Normalize and format text files
- **[tnh-setup](/cli-reference/tnh-setup.md)** – Environment setup helper
- **[token-count](/cli-reference/token-count.md)** – Token estimation utility
- **[ytt-fetch](/cli-reference/ytt-fetch.md)** – YouTube transcript fetcher

### Archived Tools

  - **Status**: Deprecated in v0.2.2, archived 2025-12-28
  - **Replacement**: [tnh-gen](/cli-reference/tnh-gen.md)
  - **Migration Guide**: See [TNH-Gen Architecture](/architecture/tnh-gen/index.md)

## TNH-Gen (Current)

The `tnh-gen` CLI is TNH Scholar's unified command-line interface for GenAI-powered text processing operations, with a modern object-service compliant architecture.

**Key Features**:

- **Prompt Discovery**: Browse and search available prompts with `tnh-gen list`
- **Text Processing**: Execute AI-powered transformations (translation, sectioning, summarization)
- **Human-Friendly**: Optimized for direct CLI usage with readable output
- **API Mode**: `--api` flag for machine-readable JSON output (VS Code, scripts)
- **Configuration Management**: Hierarchical config with clear precedence rules
- **Provenance Tracking**: All outputs include generation metadata and fingerprints

**Quick Example**:

```bash
# List available prompts
tnh-gen list

# Translate a text file
tnh-gen run --prompt translate \
  --input-file teaching.md \
  --var source_lang=vi \
  --var target_lang=en \
  --output-file teaching.en.md
```

For complete documentation, see [tnh-gen CLI Reference](/cli-reference/tnh-gen.md).

## Audio-Transcribe

The audio transcription tool handles conversion of audio content to text format. It provides several key capabilities:

Audio downloading supports direct processing from YouTube URLs. The tool can handle both single videos and batch processing from CSV files.

Audio splitting automatically divides long audio files into manageable chunks. It supports both silence-based and AI-assisted splitting methods.

Transcription processes audio into text while maintaining timing information. The tool supports multiple languages and can include translations.

## YTT-Fetch

The YouTube Transcript Fetch utility specializes in retrieving video transcripts. It offers streamlined functionality:

Direct transcript downloading from YouTube videos eliminates the need for full video processing. This approach saves time and resources when only text is needed.

Language selection allows retrieval of transcripts in specific languages when available. The tool automatically handles language code conversion.

Output formatting provides options for saving or displaying retrieved transcripts. The tool integrates smoothly with other processing commands.

## Token-Count

The token counting utility helps manage AI processing limits and costs. It provides essential information:

Token calculation matches OpenAI's counting method exactly. This accuracy helps predict API usage and costs.

Pipeline integration allows token counting at any processing stage. This capability helps optimize processing workflows.

Standard input support enables flexible usage in command chains. The tool works seamlessly with other text processing commands.

## TNH-Setup

The setup tool handles initial configuration and maintenance of the TNH Scholar environment. It manages several aspects:

Directory creation establishes the required folder structure for patterns and logs. The tool ensures proper permissions and organization.

Pattern management handles downloading and installation of default patterns. It maintains the pattern repository structure.

Environment verification checks for necessary API keys and configurations. The tool provides guidance for missing requirements.

## NFMT

The newline formatting utility standardizes text file formatting. It provides focused functionality:

Line ending standardization ensures consistent text formatting. This standardization is particularly important for pattern processing.

Spacing control allows customization of line spacing between paragraphs. The tool helps prepare text for various processing needs.

Pipeline compatibility enables integration with other processing tools. This integration supports complex text processing workflows.

## Workflow Integration

The TNH Scholar command-line tools are designed to work together effectively:

Pipeline Support: All tools support both file input/output and standard streams, enabling complex processing pipelines.

Consistent Interfaces: Tools maintain consistent option patterns and behavior, making them easy to learn and use together.

Error Handling: Tools are intended to provide consistent error reporting and status information, helping with workflow debugging.
(In the prototyping phase not all error handling is implemented.)

Resource Management: Tools coordinate resource usage and maintain efficient processing patterns.

## Common Features

Several features are common across all TNH Scholar command-line tools:

Standard Input/Output: All tools support both file-based and stream-based processing, enabling flexible usage.

Verbose Modes: Tools provide detailed logging options for troubleshooting and monitoring.

Documentation: Each tool includes help information and usage examples.

Configuration: Tools respect both global and command-specific configuration options.

## Getting Started

To begin using the command-line tools:

1. Install TNH Scholar using pip
2. Run tnh-setup to configure your environment
3. Review individual tool documentation for specific usage details
4. Start with simple commands and gradually build more complex pipelines

For detailed information about each tool, refer to their specific documentation sections.
