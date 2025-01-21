# audio-transcribe

Command-line tool for audio transcription tasks.

## Usage

```bash
audio-transcribe [OPTIONS] [INPUT_FILE]
```

## Options

```
-s, --split              Split audio into chunks
-t, --transcribe         Transcribe the audio chunks
-y, --yt_url TEXT        Single YouTube URL to process
-v, --yt_url_csv PATH    CSV file containing multiple YouTube URLs
...
```

## Examples

### Download and Transcribe from YouTube
```bash
audio-transcribe --yt_url "https://youtube.com/watch?v=example" --split --transcribe
```

### Process Local Audio File
```bash
audio-transcribe -f my_audio.mp3 --split --transcribe
```