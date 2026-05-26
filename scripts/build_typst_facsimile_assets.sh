#!/usr/bin/env bash
set -euo pipefail

scan_path="docs/user-guide/assets/journal-pipeline/pgvn-17-18-page7-clean.jpg"
assets_dir="experiments/typst/assets"
title_out="$assets_dir/title-buddhist-cosmology-din-tight.png"
paper_out="$assets_dir/page7-paper-texture.png"
title_font="${TITLE_FONT:-/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf}"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "Error: ffmpeg is not installed or not on PATH." >&2
  exit 1
fi

if [[ ! -f "$scan_path" ]]; then
  echo "Error: clean page scan not found: $scan_path" >&2
  exit 1
fi

if [[ ! -f "$title_font" ]]; then
  echo "Error: title font not found: $title_font" >&2
  exit 1
fi

mkdir -p "$assets_dir"

echo "Building title asset: $title_out"
ffmpeg -y \
  -f lavfi -i color=c=white@0.0:s=860x360,format=rgba \
  -vf "drawtext=fontfile='${title_font}':text='Buddhist':fontcolor=0x111111@0.96:fontsize=185:x=56:y=18,drawtext=fontfile='${title_font}':text='Cosmology':fontcolor=0x111111@0.96:fontsize=190:x=52:y=150" \
  -frames:v 1 -update 1 "$title_out" \
  >/tmp/build_typst_title.log 2>&1

echo "Building paper texture: $paper_out"
ffmpeg -y \
  -i "$scan_path" \
  -vf "crop=100:100:220:10,scale=840:1260:flags=lanczos" \
  -frames:v 1 -update 1 "$paper_out" \
  >/tmp/build_typst_paper.log 2>&1

echo "Wrote:"
echo "  $title_out"
echo "  $paper_out"
