---
title: "Command Line Tools Overview"
description: "TNH Scholar provides a suite of command-line tools designed to work together for text processing. Each tool focuses on specific tasks while maintaining consistent interfaces and behavior. This overview introduces the available tools and their primary functions."
owner: ""
author: ""
status: processing
created: "2025-02-01"
---
# Command Line Tools Overview

TNH Scholar provides a suite of command-line tools designed to work together for text processing. Each tool focuses on specific tasks while maintaining consistent interfaces and behavior. This overview introduces the available tools and their primary functions. 

## Available tools

- **[audio-transcribe](audio-transcribe.md)** – Transcribe audio files with diarization
- **[nfmt](nfmt.md)** – Normalize and format text files
- **[tnh-fab](tnh-fab.md)** – Pattern-driven text processing and translation
- **[tnh-setup](tnh-setup.md)** – Environment setup helper
- **[token-count](token-count.md)** – Token estimation utility
- **[ytt-fetch](ytt-fetch.md)** – YouTube transcript fetcher

## TNH-FAB

The primary text processing tool, TNH-FAB ('fab' short for 'fabric'), provides core functionality for text manipulation and analysis. This versatile tool includes several subcommands:

The **punctuate** command handles text punctuation and basic formatting. It can work with multiple languages and adapts to various writing styles.

The **section** command analyzes text structure and identifies logical divisions. It helps organize content into meaningful segments for further processing. This is crucial for working with larger text where model context limits may be reached or where processing will be ineffective due to content size.

The **translate** command performs line-by-line translation while maintaining document structure. It provides context-aware translation particularly suited for wisdom and mindfulness content.

The **process** command applies custom pattern-based processing to text. It offers flexible text transformation capabilities through the pattern system.

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
