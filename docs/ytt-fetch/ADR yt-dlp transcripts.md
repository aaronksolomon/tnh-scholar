# ADR: YouTube Transcript Format Selection for yt-fetch CLI

## Status
Proposed

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