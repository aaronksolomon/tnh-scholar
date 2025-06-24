# speaker_block.py

from __future__ import annotations

from typing import List

from pydantic_settings import BaseSettings

from tnh_scholar.utils import TimeMs

from .models import DiarizationSegment, SpeakerBlock


class SpeakerBlockConfig(BaseSettings):
    """Configuration settings for speaker block generation."""
    gap_threshold: TimeMs = TimeMs(500)

    class Config:
        env_prefix = "SPEAKER_BLOCK_"
        arbitrary_types_allowed = True


def group_speaker_blocks(
    segments: List[DiarizationSegment],
    config: SpeakerBlockConfig = SpeakerBlockConfig()
) -> List[SpeakerBlock]:
    """Group contiguous or near-contiguous segments by speaker identity.

    Segments are grouped into `SpeakerBlock`s when the speaker remains the same
    and the gap between consecutive segments is less than the configured threshold.

    Parameters:
        segments: A list of diarization segments (must be sorted by start time).
        config: Configuration containing the allowed gap between segments.

    Returns:
        A list of SpeakerBlock objects representing grouped speaker runs.
    """
    if not segments:
        return []

    blocks: List[SpeakerBlock] = []
    buffer: List[DiarizationSegment] = [segments[0]]

    for current in segments[1:]:
        previous = buffer[-1]
        same_speaker = current.speaker == previous.speaker
        gap = TimeMs(current.start) - TimeMs(previous.end)

        if same_speaker and gap.to_ms() <= config.gap_threshold.to_ms():
            buffer.append(current)
        else:
            blocks.append(SpeakerBlock(speaker=buffer[0].speaker, segments=buffer))
            buffer = [current]

    if buffer:
        blocks.append(SpeakerBlock(speaker=buffer[0].speaker, segments=buffer))

    return blocks