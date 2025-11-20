---
title: "yt-dlp Comprehensive Guide"
description: "## Overview"
owner: ""
status: processing
created: "2025-02-01"
---
# yt-dlp Comprehensive Guide

## Overview

yt-dlp is a feature-rich downloader for videos and audio from YouTube and other platforms. At its core is the `YoutubeDL` class which coordinates the entire download process through these main components:

1. **InfoExtractors**: Extract video metadata and available formats
2. **FileDownloader**: Handle the actual file downloading
3. **PostProcessors**: Process downloaded files (e.g., converting formats)
4. **Progress Hooks**: Monitor and report download progress

## Basic Usage Pattern

```python
from yt_dlp import YoutubeDL

# Configure options
ydl_opts = {
    "format": "bestaudio/best",
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
    }],
}

# Create YoutubeDL instance
with YoutubeDL(ydl_opts) as ydl:
    # Download video(s)
    ydl.download(["https://www.youtube.com/watch?v=..."])
```

## Core Components

### 1. Information Extraction

InfoExtractors handle determining what content is available:

- Extract metadata (title, duration, formats, etc.)
- Identify available formats
- Handle platform-specific details
- Support multiple URL patterns

### 2. Download Management

The FileDownloader handles:

- Format selection
- Actual file downloading
- Progress tracking
- Resume capability
- Rate limiting
- Error handling

### 3. Post-Processing

After download, files can be processed to:

- Convert formats
- Extract audio
- Embed metadata
- Merge formats
- Handle subtitles

## Configuration Options

### Authentication

```python
{
    "username": "user",           # Account username
    "password": "pass",           # Account password
    "videopassword": "vpass",     # Video-specific password
    "ap_mso": "provider",         # Adobe Pass provider
    "ap_username": "user",        # Adobe Pass username
    "ap_password": "pass",        # Adobe Pass password
    "usenetrc": True,             # Use .netrc for auth
    "netrc_location": "~/.netrc"  # Custom netrc location
}
```

### Format Selection

```python
{
    "format": "bestvideo+bestaudio",  # Format specification
    "format_sort": ["res", "ext"],    # Sort criteria for formats
    "merge_output_format": "mp4",     # Output format for merged files
    "allow_multiple_video_streams": True,  # Allow multiple video streams
    "allow_multiple_audio_streams": True,  # Allow multiple audio streams
    "prefer_free_formats": True,      # Prefer free container formats
}
```

### Output Control

```python
{
    "paths": {
        "home": "~/Downloads",    # Base download directory
        "temp": "/tmp"           # Temporary files directory
    },
    "outtmpl": {
        "default": "%(title)s.%(ext)s",  # Output template
        "chapter": "%(title)s-%(section_number)s.%(ext)s"
    },
    "restrictfilenames": True,    # Use filesystem-safe names
    "windowsfilenames": True,     # Force Windows-compatible names
    "trim_file_name": 220        # Max filename length
}
```

### Download Behavior

```python
{
    "concurrent_fragment_downloads": 3,  # Parallel downloads
    "throttledratelimit": 50000,        # Speed limit (bytes/sec)
    "retries": 10,                      # Retry attempts
    "fragment_retries": 10,             # Fragment retry attempts
    "skip_download": False,             # Skip actual download
    "keepvideo": True,                  # Keep video after processing
    "overwrites": True                  # Overwrite existing files
}
```

### Network Settings

```python
{
    "socket_timeout": 30,               # Connection timeout
    "source_address": "0.0.0.0",        # Source IP address
    "proxy": "socks5://127.0.0.1:1080", # Proxy URL
    "socket_timeout": 30,               # Timeout in seconds
    "geo_verification_proxy": "",       # Geo-bypass proxy
    "geo_bypass": True,                 # Enable geo-bypass
    "geo_bypass_country": "US"          # Country code for geo-bypass
}
```

### Progress Monitoring

Progress hooks receive detailed download status:

```python
def progress_hook(d):
    if d['status'] == 'downloading':
        # Access download information:
        # d['filename']         - Output filename
        # d['downloaded_bytes'] - Bytes downloaded
        # d['total_bytes']     - Total file size
        # d['speed']           - Download speed
        # d['eta']             - Estimated time
        pass
    elif d['status'] == 'finished':
        # Download completed
        pass
    elif d['status'] == 'error':
        # Download failed
        pass

ydl_opts = {
    "progress_hooks": [progress_hook]
}
```

### Subtitles and Thumbnails

```python
{
    "writesubtitles": True,           # Download subtitles
    "writeautomaticsub": True,        # Download auto-generated subs
    "subtitleslangs": ["en", "es"],   # Subtitle languages
    "subtitlesformat": "srt",         # Subtitle format
    "writethumbnail": True,           # Download thumbnail
    "write_all_thumbnails": True      # Download all thumbnails
}
```

## Advanced Features

### 1. Custom Format Selection

Format selection can use complex criteria:

```python
def format_selector(ctx):
    """Select the best video and audio formats."""
    formats = ctx.get('formats')[::-1]

    # Select best video format available
    best_video = next(f for f in formats 
                     if f['vcodec'] != 'none' and f['acodec'] == 'none')
    
    # Select best audio format available
    best_audio = next(f for f in formats
                     if f['acodec'] != 'none' and f['vcodec'] == 'none')

    return [best_video, best_audio]

ydl_opts = {
    "format": format_selector
}
```

### 2. Download Range Selection

```python
def download_range_callback(info_dict, ydl):
    """Select specific portions of video to download."""
    return [
        {
            "start_time": 30,
            "end_time": 90,
            "title": "First section"
        },
        {
            "start_time": 150,
            "end_time": 210,
            "title": "Second section"
        }
    ]

ydl_opts = {
    "download_ranges": download_range_callback
}
```

### 3. Custom Post-Processing

```python
from yt_dlp.postprocessor import PostProcessor

class CustomPP(PostProcessor):
    def run(self, info):
        # Process the downloaded file
        return [], info

ydl.add_post_processor(CustomPP())
```

## Error Handling

The system provides several layers of error handling:

1. **Download Retries**: Automatic retry on temporary failures
2. **Graceful Degradation**: Falls back to lower quality if preferred format fails
3. **Error Reporting**: Detailed error information through hooks
4. **Recovery Options**: Can resume interrupted downloads

```python
{
    "ignoreerrors": True,              # Continue on download errors
    "no_warnings": True,               # Suppress warnings
    "retries": 5,                      # Number of retries
    "file_access_retries": 3,          # File operation retries
    "fragment_retries": 3              # Segment download retries
}
```

## Best Practices

1. **Always use context manager** (`with` statement) to ensure proper cleanup
2. **Implement progress hooks** for download monitoring
3. **Set appropriate timeouts** for your network conditions
4. **Use format selection** instead of hardcoded format IDs
5. **Implement error handling** appropriate for your use case
6. **Consider rate limiting** for bulk downloads
7. **Use postprocessors** for format conversion instead of separate tools
8. **Properly handle authentication** using secure methods
9. **Monitor disk space** when downloading large files/playlists
10. **Use appropriate output templates** for organized downloads

## Common Pitfalls

1. Not handling network timeouts
2. Incorrect format selection leading to unnecessary downloads
3. Not implementing proper error handling
4. Ignoring geo-restriction handling
5. Poor output template design leading to filename conflicts
6. Not considering platform differences (Windows vs Unix)
7. Inefficient use of post-processing
8. Not properly handling authentication
9. Missing required dependencies for certain features
10. Not cleaning up temporary files

## Performance Optimization

1. **Concurrent Downloads**:
   - Use `concurrent_fragment_downloads` for parallel downloading
   - Balance concurrency with system resources

2. **Network Optimization**:
   - Set appropriate buffer sizes
   - Use proper timeouts
   - Implement rate limiting as needed

3. **Disk I/O**:
   - Use appropriate temporary directories
   - Monitor disk space
   - Clean up temporary files

4. **Resource Management**:
   - Properly close file handles
   - Use context managers
   - Implement cleanup hooks

## Debugging

Enable detailed logging for troubleshooting:

```python
{
    "verbose": True,               # Enable verbose output
    "debug_printtraffic": True,    # Print network traffic
    "logger": custom_logger       # Use custom logger
}
```

## Security Considerations

1. **Authentication**:
   - Secure storage of credentials
   - Use of netrc for credential management
   - Proper handling of session data

2. **Network Security**:
   - SSL/TLS verification
   - Proxy configuration
   - Geo-restriction handling

3. **File System Safety**:
   - Safe filename handling
   - Permission management
   - Temporary file cleanup

## Integration Tips

1. **As Library**:
   - Use as Python module
   - Implement custom hooks
   - Extend functionality

2. **In Applications**:
   - Handle events asynchronously
   - Proper resource management
   - Error handling and recovery

3. **With Other Tools**:
   - FFmpeg integration
   - External downloaders
   - Custom post-processors