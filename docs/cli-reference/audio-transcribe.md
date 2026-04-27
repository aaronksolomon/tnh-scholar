---
title: "audio-transcribe"
description: "Command-line tool for downloading audio (YouTube or local) and transcribing to text."
owner: ""
author: ""
status: current
created: "2025-01-21"
---
# audio-transcribe

Command-line tool for downloading audio from YouTube or local files and transcribing to text using OpenAI Whisper or AssemblyAI.

## Usage

```bash
audio-transcribe [OPTIONS]
```

Exactly one audio source must be provided: `--yt_url`, `--yt_url_csv`, or `--file`.

## Options

### Audio Source (one required)

```
-y, --yt_url TEXT           Single YouTube URL to download and transcribe
-v, --yt_url_csv PATH       CSV file with YouTube URLs in first column
-f, --file PATH             Path to a local audio or video file
```

### Output

```
-o, --output PATH           Output transcript file path
                            (default: ./audio_transcriptions/transcript.txt)
-k, --keep_artifacts        Keep intermediate files in output directory
```

### Transcription Service

```
-s, --service [whisper|assemblyai]    Transcription service (default: whisper)
-m, --model TEXT                      Model name (default: whisper-1)
-l, --language TEXT                   Language code, e.g., 'en', 'vi' (default: en)
-r, --response_format TEXT            Whisper response format (default: text)
--prompt TEXT                         Prompt or keywords to guide transcription
```

### Audio Processing

```
--chunk_duration INT        Target chunk duration in seconds (default: 120)
--min_chunk INT             Minimum chunk duration in seconds (default: 10)
--start_time TEXT           Start time offset for input media (HH:MM:SS)
--end_time TEXT             End time offset for input media (HH:MM:SS)
```

### Mode Flags

```
-n, --no_transcribe         Download audio only, skip transcription
```

## Examples

### Transcribe from YouTube

```bash
audio-transcribe --yt_url "https://youtube.com/watch?v=example"
```

### Transcribe with Vietnamese Language

```bash
audio-transcribe --yt_url "https://youtube.com/watch?v=example" \
  --language vi \
  --output ./transcripts/dharma_talk.txt
```

### Download Only (No Transcription)

```bash
audio-transcribe --yt_url "https://youtube.com/watch?v=example" \
  --no_transcribe \
  --keep_artifacts
```

### Process Local Audio File

```bash
audio-transcribe --file recording.mp3 --output transcript.txt
```

### Extract Portion of Audio

```bash
audio-transcribe --yt_url "https://youtube.com/watch?v=example" \
  --start_time 00:05:00 \
  --end_time 00:15:00
```

### Batch Process from CSV

```bash
audio-transcribe --yt_url_csv urls.csv --output batch_transcript.txt
```

## Output Behavior

- Transcripts are written to the output file as plain text
- Each chunk is separated by blank lines
- Transcript chunks are also printed to stdout during processing
- Video files (`.mp4`, `.avi`, `.mov`, `.mkv`, `.wmv`) are auto-converted to audio

## Requirements

- **OpenAI API key**: Required for Whisper transcription (`OPENAI_API_KEY`)
- **yt-dlp**: Required for YouTube downloads (installed automatically with tnh-scholar)

## See Also

- [CLI Reference: Overview](/cli-reference/overview.md)
- [ytt-fetch](/cli-reference/ytt-fetch.md) - For fetching existing YouTube transcripts
