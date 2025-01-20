I'll create a supplementary ADR that builds on our format decision to include this consideration about transcript sources:


# ADR: YouTube Transcript Source Handling in yt-fetch CLI

## Status
Proposed (supplements ADR: YouTube Transcript Format Selection)

## Context
When requesting transcripts from YouTube videos:
- Videos may have manually uploaded subtitles
- Videos may have auto-generated captions
- Some videos may have both
- Quality and accuracy can vary significantly between sources

Currently yt-dlp options:
```python
opts = {
    "writesubtitles": True,      # Get manual subtitles
    "writeautomaticsub": True,   # Get auto-generated captions
    "subtitleslangs": ["en"]     # Language selection
}


## Decision
1. Initially accept both sources (manual and auto-generated) with preference given to manual subtitles when available (yt-dlp's default behavior)

2. Flag this as a known limitation/consideration:
   - Source of transcript (manual vs auto) may affect quality
   - No current mechanism to force selection of specific source
   - Transcript source not clearly indicated in output

## Future Considerations
Future versions should consider:
- Adding transcript source metadata
- Option to specify preferred source
- Quality indicators in output
- Logging which source was used

## Consequences

### Positive
- Simple initial implementation
- Works with all video types
- Maximum transcript availability

### Negative
- Uncertain transcript source
- No quality indicators
- May get auto-generated when manual exists
- May get manual when auto-generated preferred

## Notes
This limitation is acceptable for prototyping but should be revisited when:
- Transcript quality becomes critical
- Source attribution needed
- Specific use cases require specific transcript types

Would you like me to explore any specific aspect of this further, or shall we move on to implementation?