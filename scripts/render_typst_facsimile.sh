#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/render_typst_facsimile.sh [typ_file]

Render a Typst facsimile source to both PDF and PNG.

Defaults:
  typ_file = experiments/typst/vu-tru-page7-facsimile.typ

Outputs:
  <typ_file basename>.pdf
  <typ_file basename>.png
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if ! command -v typst >/dev/null 2>&1; then
  echo "Error: typst is not installed or not on PATH." >&2
  exit 1
fi

if ! command -v pdftoppm >/dev/null 2>&1; then
  echo "Error: pdftoppm is not installed or not on PATH." >&2
  exit 1
fi

if [[ -x "./scripts/build_typst_facsimile_assets.sh" ]]; then
  echo "Refreshing facsimile assets"
  ./scripts/build_typst_facsimile_assets.sh
fi

typ_file="${1:-experiments/typst/vu-tru-page7-facsimile.typ}"

if [[ ! -f "$typ_file" ]]; then
  echo "Error: Typst source not found: $typ_file" >&2
  exit 1
fi

base_path="${typ_file%.typ}"
pdf_path="${base_path}.pdf"
repo_root="$(pwd)"

echo "Compiling Typst source: $typ_file"
typst compile --root "$repo_root" "$typ_file" "$pdf_path"

echo "Rendering first PDF page to PNG: $pdf_path"
pdftoppm -png -r 300 -f 1 -singlefile "$pdf_path" "$base_path"

echo "Wrote:"
echo "  $pdf_path"
echo "  ${base_path}.png"
