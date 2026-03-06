from __future__ import annotations

from pathlib import Path
from typing import Any

from tnh_scholar.audio_processing.diarization.audio.handler import AudioHandler
from tnh_scholar.utils import TNHAudioSegment as AudioSegment


def resolve_audio_format(audio_file: Path) -> str:
    """Resolve the export format from the source audio suffix."""
    suffix = audio_file.suffix.lstrip(".").lower()
    return suffix or "wav"


def slice_audio_bytes(
    base_audio: AudioSegment,
    start_ms: int,
    end_ms: int,
    audio_file: Path,
) -> Any:
    """Export a byte stream for a bounded audio slice."""
    block_audio = base_audio[start_ms:end_ms]
    return AudioHandler().export_audio_bytes(
        block_audio,
        format_str=resolve_audio_format(audio_file),
    )
