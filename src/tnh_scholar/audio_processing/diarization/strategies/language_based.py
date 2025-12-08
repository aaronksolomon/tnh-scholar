# tnh_scholar.audio_processing.diarization.strategies.language_based.py
"""
LanguageChunker – chunking informed by speaker blocks + language probing.
"""

from __future__ import annotations

from typing import List

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils import TimeMs

from ..config import ChunkConfig
from ..models import DiarizationChunk, DiarizedSegment
from ..protocols import ChunkingStrategy
from .language_probe import AudioFetcher, LanguageDetector, probe_segment_language
from .speaker_blocker import group_speaker_blocks

logger = get_child_logger(__name__)


class LanguageChunker(ChunkingStrategy):
    """
    Strategy:

    1. Group contiguous segments into SpeakerBlock objects.
    2. For each block longer than ``language_probe_threshold`` probe language
       at configurable offsets; if mismatch, split on language change.
    3. Build chunks respecting ``target_time`` similar to TimeGapChunker.
    """

    def __init__(
        self,
        cfg: ChunkConfig = ChunkConfig(),
        fetcher: AudioFetcher | None = None,
        detector: LanguageDetector | None = None,
        language_probe_threshold: TimeMs = TimeMs(90_000),
    ):
        self.cfg = cfg
        self.fetcher = fetcher
        self.detector = detector
        self.lang_thresh = language_probe_threshold

    def extract(self, segments: List[DiarizedSegment]) -> List[DiarizationChunk]:
        if not segments:
            return []

        blocks = group_speaker_blocks(
            segments, config=self.cfg.speaker_block
        )  # attribute from DiarizationConfig
        # Optionally split blocks on language change
        enriched_segments: List[DiarizedSegment] = []
        for block in blocks:
            if block.duration >= self.lang_thresh and self.fetcher and self.detector:
                enriched_segments.extend(self._split_block_on_language(block))
            else:
                enriched_segments.extend(block.segments)

        # Now fall back to pure time-gap chunking
        from .time_gap import TimeGapChunker

        return TimeGapChunker(self.cfg).extract(enriched_segments)


    def _split_block_on_language(self, block):
        """
        Probe language at 25% and 75% of block; if mismatch, split.
        Very naive – replace with richer algorithm later.
        """
        assert self.fetcher and self.detector  # guaranteed by caller
        first_seg = block.segments[0]
        last_seg = block.segments[-1]
        quarter_point = first_seg.start + (block.duration // 4)
        three_quarter = first_seg.start + (block.duration * 3 // 4)

        probe_segs = [self._segment_at(block, quarter_point),
                      self._segment_at(block, three_quarter)]

        langs = {probe_segment_language(s, self.fetcher, self.detector) for s in probe_segs}

        if len(langs) <= 1:
            return block.segments  # All one language

        # Language split → naively split at midpoint
        midpoint_ms = block.start + (block.duration // 2)
        left, right = [], []
        for seg in block.segments:
            (left if seg.end <= midpoint_ms else right).append(seg)

        return left + right

    def _segment_at(self, block, ms):
        """Return the first segment covering the given ms offset."""
        for seg in block.segments:
            if seg.start <= ms < seg.end:
                return seg
        return block.segments[0]  # fallback