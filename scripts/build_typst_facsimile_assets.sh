#!/usr/bin/env bash
set -euo pipefail

scan_path="docs/user-guide/assets/journal-pipeline/pgvn-17-18-page7-clean.jpg"
assets_dir="experiments/typst/assets"
title_out="$assets_dir/title-buddhist-cosmology-din-tight.png"
paper_out="$assets_dir/page7-paper-texture.png"
title_font="${TITLE_FONT:-/System/Library/Fonts/Supplemental/Impact.ttf}"

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
  -f lavfi -i color=c=white@0.0:s=980x360,format=rgba \
  -vf "drawtext=fontfile='${title_font}':text='BUDDHIST':fontcolor=0x111111@0.96:fontsize=168:x=46:y=14,drawtext=fontfile='${title_font}':text='COSMOLOGY':fontcolor=0x111111@0.96:fontsize=172:x=44:y=154" \
  -frames:v 1 -update 1 "$title_out" \
  >/tmp/build_typst_title.log 2>&1

echo "Building paper texture: $paper_out"
ffmpeg -y \
  -i "$scan_path" \
  -vf "crop=88:88:278:30,boxblur=14:2,eq=contrast=0.94:brightness=0.025:saturation=0.42,scale=840:1260:flags=lanczos" \
  -frames:v 1 -update 1 "$paper_out" \
  >/tmp/build_typst_paper.log 2>&1

echo "Wrote:"
echo "  $title_out"
echo "  $paper_out"
