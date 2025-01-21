# Getting Started

This guide will help you get started with TNH Scholar's main features.

## Basic Usage

TNH Scholar provides several command-line tools:

- `audio-transcribe`: Process and transcribe audio files
- `tnh-fab`: Text processing and formatting tool
- `ytt-fetch`: YouTube transcript fetching utility

## Quick Start Examples

### Transcribing Audio
```bash
audio-transcribe --yt_url "https://youtube.com/watch?v=example" --split --transcribe
```

### Processing Text
```bash
tnh-fab punctuate input.txt > punctuated.txt
```

### Fetching Transcripts
```bash
ytt-fetch "https://youtube.com/watch?v=example" -l en -o transcript.txt
```

## Next Steps

- See the CLI documentation for detailed usage of each tool
- Check the API documentation for programmatic usage
- Review example notebooks for common workflows