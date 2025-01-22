# Getting Started

This guide will help you get started with TNH Scholar's main features.


## Setup

In order to use OpenAI based tools you must have an OpenAI API key set in the environment variable: OPENAI_API_KEY.

- `setup-tnh`: This setup tool TNH Scholar sets up the default director for the project: HOME/.config/tnh_scholar. 
It also offers to download patterns from the default pattern repository on github.

## Basic Usage

TNH Scholar provides several command-line tools:

- `audio-transcribe`: Process and transcribe audio files
- `tnh-fab`: Text processing and formatting tool
- `ytt-fetch`: YouTube transcript fetching utility
- `nfmt`: A tool to formate newlines in a text file

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