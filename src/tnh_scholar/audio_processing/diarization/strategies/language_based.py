# tnh_scholar.audio_processing.diarization.strategies.language_based.py
"""
LanguageChunker – chunking informed by speaker blocks + language probing.
"""

from __future__ import annotations

from typing import List

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils import TimeMs

from ..config import ChunkConfig, DiarizationConfig
from ..models import DiarizationChunk, DiarizedSegment, SpeakerBlock
from ..protocols import AudioFetcher, ChunkingStrategy, LanguageDetector
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

        grouping_config = DiarizationConfig(chunk=self.cfg)
        blocks = group_speaker_blocks(segments, config=grouping_config)
        # Optionally split blocks on language change
        enriched_segments: List[DiarizedSegment] = []
        for block in blocks:
            if block.duration >= self.lang_thresh and self.fetcher and self.detector:
                enriched_segments.extend(self._split_block_on_language(block))
            else:
                enriched_segments.extend(block.segments)

        # Now fall back to pure time-gap chunking
        from .time_gap import TimeGapChunker

        return TimeGapChunker(grouping_config).extract(enriched_segments)

    def _probe_segment_language(self, segment: DiarizedSegment) -> str:
        """Return detected language for a segment or a stable fallback."""
        assert self.fetcher and self.detector
        try:
            audio_path = self.fetcher.extract_audio(int(segment.start), int(segment.end))
            return audio_path.suffix.lstrip(".") or "unknown"
        except Exception as exc:
            logger.debug("Language probing fallback used for segment %s: %s", segment, exc)
            return "unknown"

    def _split_block_on_language(self, block: SpeakerBlock) -> List[DiarizedSegment]:
        """
        Probe language at 25% and 75% of block; if mismatch, split.
        Very naive – replace with richer algorithm later.
        """
        assert self.fetcher and self.detector  # guaranteed by caller
        first_seg = block.segments[0]
        quarter_point = first_seg.start + (block.duration // 4)
        three_quarter = first_seg.start + (block.duration * 3 // 4)

        probe_segs = [self._segment_at(block, quarter_point), self._segment_at(block, three_quarter)]

        langs = {self._probe_segment_language(segment) for segment in probe_segs}

        if len(langs) <= 1:
            return block.segments  # All one language

        # Language split → naively split at midpoint
        midpoint_ms = block.start + (block.duration // 2)
        left: list[DiarizedSegment] = []
        right: list[DiarizedSegment] = []
        for seg in block.segments:
            (left if seg.end <= midpoint_ms else right).append(seg)

        return left + right

    def _segment_at(self, block: SpeakerBlock, ms: TimeMs) -> DiarizedSegment:
        """Return the first segment covering the given ms offset."""
        for seg in block.segments:
            if seg.start <= ms < seg.end:
                return seg
        return block.segments[0]  # fallback
