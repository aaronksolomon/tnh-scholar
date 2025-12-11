#!/usr/bin/env python3
"""Update version string in src/tnh_scholar/__init__.py to match pyproject.toml."""

import re
import sys
from pathlib import Path
from typing import Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # fallback for older Python


def get_pyproject_version() -> str:
    """Read version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("❌ Error: pyproject.toml not found", file=sys.stderr)
        sys.exit(1)

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        version = data["tool"]["poetry"]["version"]
        return version
    except (KeyError, tomllib.TOMLDecodeError) as e:
        print(f"❌ Error reading version from pyproject.toml: {e}", file=sys.stderr)
        sys.exit(1)


def get_init_version() -> Optional[str]:
    """Read version from __init__.py."""
    init_path = Path("src/tnh_scholar/__init__.py")
    if not init_path.exists():
        print("❌ Error: src/tnh_scholar/__init__.py not found", file=sys.stderr)
        sys.exit(1)

    content = init_path.read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
    if match:
        return match.group(1)
    return None


def update_init_version(new_version: str) -> bool:
    """Update version in __init__.py."""
    init_path = Path("src/tnh_scholar/__init__.py")
    content = init_path.read_text(encoding="utf-8")

    # Replace __version__ = "x.y.z" with new version
    new_content = re.sub(
        r'^(__version__\s*=\s*["\'])([^"\']+)(["\'])',
        rf"\g<1>{new_version}\g<3>",
        content,
        flags=re.MULTILINE,
    )

    if new_content == content:
        print(
            "❌ Error: __version__ variable not found in src/tnh_scholar/__init__.py",
            file=sys.stderr,
        )
        return False

    init_path.write_text(new_content, encoding="utf-8")
    return True


def main() -> None:
    """Sync version from pyproject.toml to __init__.py."""
    pyproject_version = get_pyproject_version()
    init_version = get_init_version()

    print("📦 Current versions:")
    print(f"   pyproject.toml: {pyproject_version}")
    print(f"   __init__.py:    {init_version or 'NOT FOUND'}")

    if init_version is None:
        print(
            "❌ Error: __version__ variable not found in src/tnh_scholar/__init__.py",
            file=sys.stderr,
        )
        sys.exit(1)

    if init_version == pyproject_version:
        print(f"✅ Versions already in sync ({pyproject_version})")
        return

    print(f"📝 Updating __init__.py to {pyproject_version}...")
    if update_init_version(pyproject_version):
        print(f"✅ Updated __init__.py to version {pyproject_version}")
    else:
        print("❌ Failed to update __init__.py", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
