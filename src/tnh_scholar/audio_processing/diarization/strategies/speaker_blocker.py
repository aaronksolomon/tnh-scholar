# speaker_block.py

from __future__ import annotations

from typing import List

from ..config import DiarizationConfig
from ..models import DiarizedSegment, SpeakerBlock


def group_speaker_blocks(
    segments: List[DiarizedSegment],
    config: DiarizationConfig = DiarizationConfig()
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
    buffer: List[DiarizedSegment] = [segments[0]]
    
    gap_threshold = config.speaker.same_speaker_gap_threshold

    for current in segments[1:]:
        previous = buffer[-1]
        same_speaker = current.speaker == previous.speaker
        gap = current.start - previous.end

        if same_speaker and gap <= gap_threshold:
            buffer.append(current)
        else:
            blocks.append(SpeakerBlock(speaker=buffer[0].speaker, segments=buffer))
            buffer = [current]

    if buffer:
        blocks.append(SpeakerBlock(speaker=buffer[0].speaker, segments=buffer))

    return blocks