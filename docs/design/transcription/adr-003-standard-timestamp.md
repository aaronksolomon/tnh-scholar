# ADR 003: Standardizing Timestamps to Milliseconds in Transcription Service

## Status

Proposed

## Context

Our transcription service currently uses a mix of timestamp formats across different providers:

- AssemblyAI returns timestamps in milliseconds, which we then convert to seconds
- OpenAI Whisper returns timestamps in seconds

This inconsistency creates several issues:

1. We need conversion logic in the AssemblyAI adapter
2. We use floating-point numbers to represent seconds, potentially leading to precision issues
3. The inconsistent API contract creates potential confusion for consumers of the service
4. The mixed format approach is more error-prone and less maintainable

## Decision Drivers

1. **Precision Requirements**: Accurate timestamps are critical for subtitle synchronization, speaker diarization, and audio analysis
2. **Data Type Consistency**: Integer representation is more reliable than floating-point for precise timing
3. **Provider API Formats**: Different providers use different time unit standards
4. **Downstream Compatibility**: Impact on existing consumers of the transcription service
5. **Performance Considerations**: Integer operations are typically faster than floating-point operations

## Proposed Decision

We will standardize all timestamps in the transcription service to use **milliseconds** as the base unit, represented as integers, for the following reasons:

1. Milliseconds provide sufficient precision for all anticipated use cases
2. Integer representation avoids floating-point precision errors
3. AssemblyAI already uses milliseconds, reducing conversion needs
4. Millisecond precision is the common standard in media processing applications

## Design Impacts

### Interface Changes

The `TranscriptionService` interface will be updated to specify that all timestamps should be in milliseconds:

```python
def transcribe(self, audio_file, options) -> Dict[str, Any]:
    """
    ...
    Returns:
        Dictionary containing transcription results with standardized keys:
            - ...
            - words: List of words with timing information (timestamps in milliseconds)
            - utterances: List of utterances by speaker (timestamps in milliseconds)
            - audio_duration: Duration of audio in milliseconds
            - ...
    """
```

### Service Implementation Changes

1. **AssemblyAITranscriptionService**:
   - Remove timestamp conversions from milliseconds to seconds
   - Update documentation to reflect millisecond timestamps
   - Keep raw API response format unchanged (already uses milliseconds)

2. **WhisperTranscriptionService**:
   - Convert timestamps from seconds to milliseconds
   - Update documentation to reflect millisecond timestamps
   - For API responses in seconds, multiply values by 1000 and convert to integers

3. **Format Converter**:
   - Update handling of timestamps in format conversion logic
   - Ensure SRT and VTT generation use correct millisecond timing

### Standardized Timestamp Format

All timestamp-related fields will follow this standard:

- Use integer values representing milliseconds
- Use consistent field names across all services (`start_ms`, `end_ms`, `duration_ms`)
- Always include timestamp units in field names for clarity

## Consequences

### Positive

1. **Consistent Data Type**: Integer timestamps avoid floating-point precision issues
2. **Reduced Conversion Logic**: Less conversion code in the AssemblyAI adapter
3. **Higher Precision**: Millisecond precision is suitable for all anticipated use cases
4. **Clearer API Contract**: Standardized format creates consistency for consumers
5. **Future Compatibility**: Easier integration with additional transcription services
6. **Alignment with Industry Standards**: Media processing typically uses milliseconds

### Negative

1. **Breaking Changes**: Existing code that consumes timestamps in seconds will need updates
2. **Increased Values**: Millisecond values are 1000x larger than second values
3. **Initial Complexity**: Additional adapter code needed during transition

### Neutral

1. **Storage Impact**: Integer milliseconds may use slightly more memory than floating-point seconds, but the difference is negligible
2. **Computational Impact**: Integer operations are typically faster than floating-point, potentially offsetting the larger values

## Implementation Plan

We will follow a phased approach to minimize disruption:

### Phase 1: Interface Documentation (2 days)

1. Update the interface documentation to specify millisecond timestamps
2. Add deprecation notices for second-based timestamps
3. Document the migration path for consumers

### Phase 2: Service Implementation (1 week)

1. Update the `AssemblyAITranscriptionService` to remove conversions to seconds
2. Update the `WhisperTranscriptionService` to output milliseconds
3. Update the format converter timestamp handling
4. Add comprehensive tests for timestamp handling

### Phase 3: Compatibility Layer (1 week)

1. Add helper methods for clients to convert between timestamp formats
2. Create adapter functions to maintain backward compatibility where needed
3. Provide utility functions for common timestamp operations

### Phase 4: Full Migration (2 weeks)

1. Update all internal consumers to use millisecond timestamps
2. Remove compatibility helpers for second-based timestamps
3. Finalize documentation and test coverage

## Alternatives Considered

### 1. Standardize on Seconds

**Pros:**
- More human-readable values
- Smaller numeric values
- Already implemented in Whisper service

**Cons:**
- Requires conversion from AssemblyAI's native milliseconds
- Floating-point precision issues
- Less common in media processing systems

### 2. Nanosecond Precision

**Pros:**
- Higher precision than milliseconds
- Future-proof for high-precision applications

**Cons:**
- Unnecessary precision for current use cases
- Very large integer values
- Not supported by our current providers natively

### 3. Maintain Mixed Format

**Pros:**
- No immediate changes needed
- Each provider uses its native format

**Cons:**
- Inconsistent API contract
- More complex error handling
- Higher cognitive load for developers

## References

1. [IEEE 754 floating-point precision issues](https://en.wikipedia.org/wiki/IEEE_754)
2. [AssemblyAI API documentation](https://docs.assemblyai.com/)
3. [OpenAI Whisper API documentation](https://platform.openai.com/docs/guides/speech-to-text)
4. [SRT subtitle format specification](https://en.wikipedia.org/wiki/SubRip)
5. [VTT subtitle format specification](https://developer.mozilla.org/en-US/docs/Web/API/WebVTT_API)