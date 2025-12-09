#!/bin/bash
# Git Branch Staleness Detection Script
#
# Detects if a local branch reference is stale compared to its remote tracking branch.
# This is critical for preventing data loss when using branch names in git reset or other
# destructive operations after remote PR merges.
#
# Usage: ./git-check-staleness.sh [--remote <remote>] [--branch <remote-branch>] [<local-branch>]
#        ./git-check-staleness.sh           (checks current branch against its upstream)
#
# Exit codes:
#   0 - Branch is up-to-date or has no remote tracking branch
#   1 - Branch is stale (local behind remote)
#   2 - Invalid usage

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_error() {
    echo -e "${RED}✗ $1${NC}" >&2
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠  $1${NC}"
}

# Parse flags/args
override_remote=""
override_remote_branch=""
branch=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --remote|-r)
            override_remote="$2"
            shift 2
            ;;
        --branch|-b)
            override_remote_branch="$2"
            shift 2
            ;;
        *)
            if [ -z "$branch" ]; then
                branch="$1"
                shift
            else
                print_error "Usage: $0 [--remote <remote>] [--branch <remote-branch>] [<local-branch>]"
                exit 2
            fi
            ;;
    esac
done

# Get branch name (from argument or current branch)
if [ -z "$branch" ]; then
    branch=$(git symbolic-ref --short HEAD 2>/dev/null || echo "HEAD")
fi

# Validate branch exists
if ! git rev-parse --verify "$branch" >/dev/null 2>&1; then
    print_error "Branch '$branch' does not exist"
    exit 2
fi

# Resolve upstream tracking ref
upstream_ref=$(git rev-parse --abbrev-ref --symbolic-full-name "${branch}@{upstream}" 2>/dev/null || echo "")
if [ -n "$upstream_ref" ]; then
    upstream_remote=${upstream_ref%%/*}
    upstream_branch=${upstream_ref#*/}
else
    upstream_remote=""
    upstream_branch=""
fi

remote="${override_remote:-$upstream_remote}"
remote_branch="${override_remote_branch:-${upstream_branch:-$branch}}"

if [ -z "$remote" ]; then
    print_success "Branch '$branch' has no remote tracking branch"
    exit 0
fi

remote_ref="$remote/$remote_branch"

# Fetch latest remote state (quietly)
echo "Fetching remote state from $remote_ref..."
if ! git fetch "$remote" "$remote_branch" 2>/dev/null; then
    # Branch might not exist on remote yet (new local branch or custom remote missing)
    print_success "Branch '$branch' has no remote tracking branch on '$remote' (or fetch failed)"
    exit 0
fi

# Get local and remote SHAs
local_sha=$(git rev-parse "$branch" 2>/dev/null)
remote_sha=$(git rev-parse "$remote_ref" 2>/dev/null || echo "")

# If no remote branch, exit success
if [ -z "$remote_sha" ]; then
    print_success "Branch '$branch' has no remote tracking branch on '$remote'"
    exit 0
fi

# Compare SHAs
if [ "$local_sha" = "$remote_sha" ]; then
    print_success "Branch '$branch' is up-to-date"
    echo "  SHA: $local_sha"
    exit 0
fi

# Branch is stale
print_error "Branch '$branch' is STALE!"
echo ""
echo "  Local:  $local_sha"
echo "  Remote: $remote_sha"
echo ""

# Show what commits are ahead/behind
ahead=$(git rev-list --count "$branch".."$remote_ref" 2>/dev/null || echo "0")
behind=$(git rev-list --count "$remote_ref".."$branch" 2>/dev/null || echo "0")

if [ "$ahead" -gt 0 ]; then
    print_warning "Local is $ahead commit(s) BEHIND remote"
fi

if [ "$behind" -gt 0 ]; then
    print_warning "Local is $behind commit(s) AHEAD of remote"
fi

echo ""
echo "To update local branch:"
echo "  git checkout $branch && git pull"
echo ""
echo "Or to force local to match remote:"
echo "  git fetch $remote && git reset --hard $remote_ref"

exit 1
