---
title: "ADR-YF00: Early yt-fetch Transcript Decisions (Historical)"
description: "Consolidates the original transcript ADR notes for yt-fetch before they were split into discrete records."
owner: ""
author: ""
status: historical
created: "2025-01-17"
---
# ADR-YF00: Early yt-fetch Transcript Decisions (Historical)

Preserves the original consolidated transcript decisions that led to ADR-YF01 and ADR-YF02.

- **Status**: Historical
- **Date**: 2024-01-15

## ADR-1: YouTube Transcript Format Selection 

## Context
The yt-fetch CLI tool needs to download YouTube transcripts/captions. YouTube offers multiple formats:
- VTT (Web Video Text Tracks)
- TTML (Timed Text Markup Language) 
- srv1/2/3 (YouTube internal formats)
- json3 (YouTube JSON format)

While yt-dlp offers format conversion capabilities, these are:
- Poorly documented
- Inconsistent in behavior
- May change across versions

## Decision
Standardize on VTT format output because:
1. It is a web standard format, likely to remain stable
2. Human readable and well-documented
3. Has wide library support if needed
4. Already the default format from yt-dlp
5. Available for both manual and auto-generated captions

Implementation approach:
- Use minimal yt-dlp options (writesubtitles, writeautomaticsub, subtitleslangs)
- Accept VTT as default output without trying format conversion
- Let downstream tools handle any needed format conversion

```python
# Example minimal implementation
opts = {
   "writesubtitles": True,
   "writeautomaticsub": True,
   "subtitleslangs": ["en"],
   "skip_download": True
}
```

## 2024-01-15
### ADR-2: YouTube Transcript Source Handling 

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
```

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

## 2024-01-16
### ADR-3 Update: YouTube Transcript Format Selection (Revision 2)

## Context
After testing various formats with real YouTube videos:
- VTT shows duplicate line issues
- TTML format provides cleaner output
- TTML includes timing and styling information in structured XML

## Decision Update
Changing preferred format from VTT to TTML based on:
- Better transcript quality (fewer duplicates)
- Clean, structured XML format
- Includes all necessary timing data
- Easy to parse with standard XML tools

## Learning Process Note
Initial decision was based on theoretical advantages of VTT.
Actual testing revealed TTML as superior choice.

### ADR-4: TTML Text Extraction Implementation

## Status
Accepted

## Context
Need to extract raw text content from YouTube TTML transcript files:
- TTML files contain timing and styling metadata in XML format
- Only need raw text content for downstream processing
- Must handle potentially malformed XML from YouTube
- Prefer minimal dependencies and simple implementation

## Decision
Implement using Python's standard library xml.etree.ElementTree because:
1. No additional dependencies required (already part of Python standard library)
2. Simple, focused API sufficient for basic XML parsing
3. Built-in namespace handling
4. Lightweight and well-documented

Implementation approach:
- Strip XML namespaces to simplify parsing
- Use ElementTree's findall() with XPath to locate text content
- Extract and join raw text with newlines
- Keep implementation minimal (under 20 lines)

## Consequences

### Positive
- Zero new dependencies
- Simple, maintainable code
- Handles basic TTML structure effectively
- Easy to test and debug

### Negative
- Limited validation of XML structure
- May need additional error handling for malformed XML
- No preservation of timing information (acceptable for current needs)
- Could break if YouTube significantly changes TTML format

## Notes
While more robust XML parsing libraries exist (lxml, BeautifulSoup4), the standard library solution provides sufficient functionality for current requirements while maintaining simplicity. Error handling can be enhanced if needed based on production experience.

## Future Considerations
- Add error handling for malformed XML if needed
- Monitor YouTube TTML format changes
- Consider preserving timing data if needed for future features
