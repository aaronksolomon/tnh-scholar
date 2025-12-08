#!/bin/bash
# Version Sync Pre-commit Hook
#
# Ensures pyproject.toml and TODO.md versions are in sync
# Prevents accidental version mismatches during commits

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get version from pyproject.toml via poetry
PYPROJECT_VERSION=$(poetry version -s 2>/dev/null)

if [ -z "$PYPROJECT_VERSION" ]; then
    echo -e "${RED}❌ Error: Could not read version from pyproject.toml${NC}"
    echo "   Ensure poetry is installed and pyproject.toml is valid"
    exit 1
fi

# Get version from TODO.md
if [ ! -f TODO.md ]; then
    echo -e "${YELLOW}⚠️  Warning: TODO.md not found${NC}"
    echo "   Version sync check skipped"
    exit 0
fi

TODO_VERSION=$(grep -oP '> \*\*Version\*\*: \K[0-9.]+' TODO.md 2>/dev/null || echo "")

if [ -z "$TODO_VERSION" ]; then
    echo -e "${YELLOW}⚠️  Warning: Could not find version in TODO.md${NC}"
    echo "   Expected format: > **Version**: X.Y.Z (Alpha)"
    echo "   Version sync check skipped"
    exit 0
fi

# Compare versions
if [ "$PYPROJECT_VERSION" != "$TODO_VERSION" ]; then
    echo -e "${RED}❌ Version Mismatch!${NC}"
    echo ""
    echo "   pyproject.toml: $PYPROJECT_VERSION"
    echo "   TODO.md:        $TODO_VERSION"
    echo ""
    echo "To fix, run one of:"
    echo "   make release-patch   # Bump patch version (0.x.Y -> 0.x.Y+1)"
    echo "   make release-minor   # Bump minor version (0.X.y -> 0.X+1.0)"
    echo "   make release-major   # Bump major version (X.y.z -> X+1.0.0)"
    echo ""
    echo "Or manually sync the versions."
    exit 1
fi

echo -e "${GREEN}✓ Version sync OK${NC} (v$PYPROJECT_VERSION)"
exit 0
