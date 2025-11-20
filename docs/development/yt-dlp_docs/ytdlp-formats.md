---
title: "yt-dlp Format Selection Guide"
description: "## Basic Format Selection"
owner: ""
status: processing
created: "2025-02-01"
---
# yt-dlp Format Selection Guide

## Basic Format Selection

### Common Format Specifiers

```
best        # Best quality (video+audio usually)
worst       # Worst quality (video+audio usually)
bestvideo   # Best video only
bestaudio   # Best audio only
worstvideo  # Worst video only
worstaudio  # Worst audio only
```

### Format Combinations

```
bestvideo+bestaudio   # Best video and best audio merged
worstvideo+bestaudio  # Worst video with best audio
```

## Advanced Format Selection

### Quality Modifiers

You can specify maximum/minimum quality:

```
best[height<=720]          # Best quality video at 720p or lower
best[height>=720]          # Best quality video at 720p or higher
bestvideo[ext=mp4]         # Best mp4 video
worst[filesize<50M]        # Smallest file under 50MB
bestaudio[ext=m4a]         # Best m4a audio
```

### Format Filters

Filter by specific attributes:

```
# Video codecs
[vcodec=h264]             # H.264 video codec
[vcodec^=avc]             # Video codec that starts with AVC
[vcodec!=vp9]             # Exclude VP9 codec

# Audio codecs
[acodec=mp4a]             # MP4A audio codec
[acodec=none]             # No audio
[acodec!=opus]            # Exclude Opus codec

# Container formats
[ext=mp4]                 # MP4 container
[ext=webm]                # WebM container
[container=m4a]           # M4A container

# Resolution
[height=1080]             # Exactly 1080p
[width>=1920]             # At least 1920 pixels wide
[res=720p]                # 720p resolution

# File size
[filesize<100M]           # Less than 100 MB
[filesize>50M]            # More than 50 MB
```

### Complex Combinations

You can combine multiple criteria:

```
# Best mp4 video with height no more than 720p
bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]

# Best video that's either mp4 or webm
bestvideo[ext=mp4]/bestvideo[ext=webm]+bestaudio

# Best video under 50MB or else best video under 100MB
bestvideo[filesize<50M]/bestvideo[filesize<100M]
```

## Format Sort Options

You can specify how formats should be sorted:

```python
"format_sort": [
    "res",            # Resolution
    "fps",            # Frame rate
    "codec:h264",     # Prefer h264 codec
    "size",           # File size
    "br",             # Bit rate
    "asr",            # Audio sample rate
    "proto:https"     # Prefer HTTPS protocol
]
```

## Practical Examples

### Common Use Cases

1. **High Quality Video Download**
```
format="bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
```
This tries to:
- Get best MP4 video and M4A audio
- If not available, get best MP4
- If not available, get best format

2. **Efficient Mobile Quality**
```
format="bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]"
```
This gets:
- 720p or lower MP4 video with M4A audio
- Fallback to combined format if separate streams aren't available

3. **Audio-Only Download**
```
format="bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio"
```
This tries to:
- Get best M4A audio
- Fallback to MP3
- Fallback to any audio

4. **Size-Constrained Download**
```
format="best[filesize<50M]/best[filesize<100M][height<=480]"
```
This tries to:
- Get best format under 50MB
- Fallback to 480p or lower if needed to stay under 100MB

## Format Selection Algorithm

yt-dlp uses this process to select formats:

1. Filter formats based on criteria
2. Sort remaining formats by quality
3. Select best matching format
4. Apply any post-processing

## Best Practices

1. **Always provide fallbacks**
   ```
   format="bestvideo+bestaudio/best"  # Good
   format="bestvideo+bestaudio"       # May fail if separated streams unavailable
   ```

2. **Be specific about containers**
   ```
   format="bestvideo[ext=mp4]+bestaudio[ext=m4a]"  # Good
   format="bestvideo+bestaudio"                     # May get incompatible formats
   ```

3. **Consider bandwidth and storage**
   ```
   format="best[height<=720]"  # Reasonable quality cap
   format="best"              # May get unnecessarily large files
   ```

4. **Use appropriate quality metrics**
   ```
   format="bestvideo[vcodec^=avc][height>=720]"  # Good
   format="best[height>=720]"                     # May get inefficient codecs
   ```

## Debugging Format Selection

To see available formats:
```python
with YoutubeDL() as ydl:
    info = ydl.extract_info(url, download=False)
    ydl.list_formats(info)
```

This will show all available formats with their IDs, codecs, and other properties to help you refine your format selection.