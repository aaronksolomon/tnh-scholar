---
title: "yt-dlp Ops Check"
description: "Local cron workflow for monthly yt-dlp integration checks."
owner: ""
author: ""
status: current
created: "2026-02-01"
updated: "2026-02-01"
---
# yt-dlp Ops Check

Run a local, monthly integration check for yt-dlp to catch upstream breakage without GitHub Actions noise.

## Script

Use:

```bash
python scripts/yt_dlp_ops_check.py
```

This runs a live ops check and appends logs to `logs/yt_dlp_ops_check.log`.

Optional overrides:

- `TNH_YT_URLS_PATH=/path/to/validation_urls.txt` to use a custom URL list.
- `TNH_YT_URL_LIMIT=2` to limit the number of URLs for a quick run.

## Cron example

```bash
# Weekly on Mondays at 9:00 AM
0 9 * * 1 /usr/bin/env bash -lc "cd /path/to/tnh-scholar && python scripts/yt_dlp_ops_check.py"
```

## URL list

Edit the live test URLs at:

`tests/fixtures/yt_dlp/validation_urls.txt`

## Runtime setup

Use the helper script or Makefile target:

```bash
python scripts/setup_ytdlp_runtime.py --yes
make ytdlp-runtime
```
