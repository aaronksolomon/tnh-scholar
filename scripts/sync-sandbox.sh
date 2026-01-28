#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/sync-sandbox.sh --sandbox <path> --source-repo <path> [--branch <branch>]

Resets a sandbox worktree to the specified branch and reinstalls dependencies
if pyproject.toml or poetry.lock changed.
EOF
}

SANDBOX_PATH=""
BRANCH=""
SOURCE_REPO=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sandbox)
      SANDBOX_PATH="$2"
      shift 2
      ;;
    --branch)
      BRANCH="$2"
      shift 2
      ;;
    --source-repo)
      SOURCE_REPO="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$SANDBOX_PATH" || -z "$SOURCE_REPO" ]]; then
  echo "Missing required arguments." >&2
  usage
  exit 1
fi

if [[ ! -d "$SANDBOX_PATH" ]]; then
  echo "Sandbox path not found: $SANDBOX_PATH" >&2
  exit 1
fi

if ! git -C "$SANDBOX_PATH" rev-parse --git-dir >/dev/null 2>&1; then
  echo "Sandbox path is not a git worktree: $SANDBOX_PATH" >&2
  exit 1
fi

if ! git -C "$SOURCE_REPO" rev-parse --git-dir >/dev/null 2>&1; then
  echo "Source repo is not a git checkout: $SOURCE_REPO" >&2
  exit 1
fi

if [[ -z "$BRANCH" ]]; then
  BRANCH="$(git -C "$SOURCE_REPO" rev-parse --abbrev-ref HEAD)"
  if [[ "$BRANCH" == "HEAD" ]]; then
    echo "Source repo is in detached HEAD; pass --branch explicitly." >&2
    exit 1
  fi
fi

if ! git -C "$SANDBOX_PATH" rev-parse --verify "$BRANCH" >/dev/null 2>&1; then
  echo "Branch not found in sandbox: $BRANCH" >&2
  exit 1
fi

git -C "$SANDBOX_PATH" reset --hard "$BRANCH"
git -C "$SANDBOX_PATH" clean -fd

tmp_patch="$(mktemp -t tnh-sandbox.XXXXXX.patch)"
git -C "$SOURCE_REPO" add -N .
git -C "$SOURCE_REPO" diff --binary > "$tmp_patch"
if [[ ! -s "$tmp_patch" ]]; then
  echo "No changes to sync; sandbox is up to date."
  rm -f "$tmp_patch"
  exit 0
fi
git -C "$SANDBOX_PATH" apply "$tmp_patch"
rm -f "$tmp_patch"

echo "Sandbox patch sync complete: $SANDBOX_PATH <- $SOURCE_REPO"
