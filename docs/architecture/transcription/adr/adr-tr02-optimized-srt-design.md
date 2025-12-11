---
title: "ADR-TR02: Optimized SRT Generation Design"
description: "Uses provider-native SRT generation to simplify the transcription pipeline."
owner: ""
author: ""
status: current
created: "2025-05-01"
---
# ADR-TR02: Optimized SRT Generation Design

Leverages provider-native subtitle generation so SRT output no longer requires a bespoke converter.

- **Status**: Proposed
- **Date**: 2025-05-01

## Context

After researching the capabilities of both OpenAI Whisper and AssemblyAI transcription services, we discovered that they both offer direct SRT generation capabilities. Our current design included a separate `TranscriptionFormatConverter` utility for format conversion, but we can streamline the implementation by utilizing these native capabilities.

## Decision Drivers

1. Direct support for SRT generation in both API services
2. Performance considerations when generating subtitles
3. Consistency of outputs across providers
4. Maintenance complexity
5. API efficiency and cost optimization

## Proposed Decision

We will optimize the SRT generation by:

1. Using provider-specific direct SRT output capabilities when available
2. Overriding the `transcribe_to_format()` method in each provider implementation to take advantage of native format generation
3. Maintaining the fallback to the general `TranscriptionFormatConverter` for scenarios where direct generation isn't available
4. Simplifying the implementation to reduce unnecessary code paths

## Design Details

### Service Interface Updates

The `TranscriptionService` base class will remain mostly unchanged, with the existing methods:

```python
def transcribe(self, audio_file, options) -> Dict[str, Any]
def get_result(self, job_id) -> Dict[str, Any]
def export_format(self, result, format_type, options) -> str
def transcribe_to_format(self, audio_file, format_type, transcription_options, format_options) -> str
```

### Provider-Specific Optimizations

#### OpenAI Whisper

For Whisper, we'll use the API's native `response_format` parameter:

```python
def transcribe_to_format(self, audio_file, format_type="srt", transcription_options=None, format_options=None):
    if format_type in ["srt", "vtt"]:
        options = transcription_options or {}
        options["response_format"] = format_type
        result = self.transcribe(audio_file, options)
        if "subtitle_content" in result:
            return result["subtitle_content"]
        # Fallback to raw result if available
        if isinstance(result["raw_result"], str):
            return result["raw_result"]
    # Fallback to general converter
    return super().transcribe_to_format(...)
```

#### AssemblyAI

For AssemblyAI, we'll use the dedicated subtitles endpoint:

```python
def transcribe_to_format(self, audio_file, format_type="srt", transcription_options=None, format_options=None):
    if format_type in self.SUBTITLE_FORMATS:
        audio_url = self.upload_file(audio_file)
        transcript_id = self.start_transcription(audio_url, transcription_options)
        self.poll_for_completion(transcript_id)
        return self.get_subtitles(transcript_id, format_type, format_options)
    # Fallback to general converter
    return super().transcribe_to_format(...)
```

### Format Converter Simplification

The `TranscriptionFormatConverter` will still be available as a fallback, but we'll deprioritize its implementation since most SRT generation will use the native capabilities. We'll focus on the most essential format conversion features:

1. Basic text-only output
2. Simple SRT generation for cases where native support is unavailable
3. Minimal formatting options

## Consequences

### Advantages

1. **Performance**: Direct API generation of SRT files will be more efficient
2. **Quality**: Native SRT generation will produce higher quality subtitles with proper timing
3. **Maintenance**: Less code to maintain in the format converter
4. **Cost**: Potentially lower API costs by avoiding redundant processing
5. **Accuracy**: Provider-specific optimizations will better handle edge cases

### Disadvantages

1. **Provider Coupling**: Tighter coupling to provider-specific API capabilities
2. **Testing Complexity**: Need to test both direct generation and fallback paths
3. **Configuration Management**: More provider-specific options to document and manage

## Implementation Plan

1. Update the Whisper service implementation to use the `response_format` parameter
2. Enhance the AssemblyAI implementation to use the subtitles endpoint
3. Simplify the `TranscriptionFormatConverter` to focus on fallback scenarios
4. Update the integration tests to verify both direct and fallback paths
5. Update documentation to reflect the optimized approach

## References

1. OpenAI Whisper API [response_format parameter](https://platform.openai.com/docs/api-reference/audio)
2. AssemblyAI [Subtitles endpoint](https://www.assemblyai.com/docs/api-reference/subtitles)
3. Original SRT Generation ADR
