---
title: "ytt-fetch"
description: "(Y)ou(T)ube (T)ranscript-(Fetch)ing utility."
owner: ""
author: ""
status: current
created: "2025-01-21"
---
# ytt-fetch

(Y)ou(T)ube (T)ranscript-(Fetch)ing utility.

## Usage

```bash
ytt-fetch [OPTIONS] URL
```

## Options

```plaintext
-l, --lang TEXT     Language code for transcript (default: en)
-o, --output PATH   Save transcript text to file
```

## Examples

### Download English Transcript

```bash
ytt-fetch "https://youtube.com/watch?v=example" -l en -o transcript.txt
```

### Print Transcript to Console

```bash
ytt-fetch "https://youtube.com/watch?v=example"
```

## yt-dlp Runtime Notes

yt-dlp may emit warnings about missing JS runtime support or impersonation. These are not login prompts.
They refer to runtime helpers (deno/node/bun) and `curl_cffi` that improve stability against YouTube changes.
ytt-fetch validates these prerequisites and exits with guidance when missing.
