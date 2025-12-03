---
title: "ADR-YF02: YouTube Transcript Format Selection"
description: "Locks yt-fetch to a single transcript format (initially VTT) for predictable downstream processing."
owner: ""
author: ""
status: processing
created: "2025-01-21"
---
# ADR-YF02: YouTube Transcript Format Selection

Selects a canonical transcript format for yt-fetch to keep downstream processing deterministic during early releases.

- **Status**: Proposed
- **Date**: 2025-01-15

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
