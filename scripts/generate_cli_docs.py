#!/usr/bin/env python3
"""Generate CLI reference documentation from Click/Typer commands.

Note: This generates stub documentation pointing to --help output.
Full introspection of CLI modules is deferred to a future enhancement.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI_REFERENCE_DIR = ROOT / "docs/cli-reference"

# Map of CLI tool directories to their command names
CLI_COMMANDS = {
    "audio_transcribe": "audio-transcribe",
    "json_to_srt": "json-to-srt",
    "nfmt": "nfmt",
    "sent_split": "sent-split",
    "srt_translate": "srt-translate",
    "tnh_fab": "tnh-fab",
    "tnh_setup": "tnh-setup",
    "token_count": "token-count",
    "ytt_fetch": "ytt-fetch",
}


def main() -> None:
    """Generate CLI reference documentation for all registered commands."""
    print("Generating CLI reference documentation...")
    
    if not CLI_REFERENCE_DIR.exists():
        CLI_REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    
    for tool_dir, command_name in CLI_COMMANDS.items():
        print(f"Processing {command_name}...")
        doc_path = CLI_REFERENCE_DIR / f"{command_name}.md"
        
        stub = f"""---
title: "{command_name}"
description: "CLI reference for {command_name}"
owner: ""
author: ""
status: auto_generated
created: "{datetime.utcnow().date()}"
auto_generated: true
---

# {command_name}

For full command-line help, run:

```bash
poetry run {command_name} --help
```

## Location

`src/tnh_scholar/cli_tools/{tool_dir}/`
"""
        doc_path.write_text(stub)
        print(f"  ✓ {doc_path.relative_to(ROOT)}")
    
    print(f"\nGenerated {len(CLI_COMMANDS)} CLI reference docs in {CLI_REFERENCE_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
