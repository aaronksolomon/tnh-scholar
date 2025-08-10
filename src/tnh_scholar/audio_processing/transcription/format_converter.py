"""
tnh_scholar.audio_processing.transcription.format_converter
-----------------------------------------------------------

Thin facade that turns *raw* transcription-service output dictionaries into the
formats requested by callers (plain-text, SRT - VTT coming later).

Core heavy lifting now lives in:

* `TimedText` / `TimedTextUnit` - canonical internal representation
* `SegmentBuilder`            - word-level -> sentence/segment chunking
* `SRTProcessor`              - rendering to `.srt`

Only one public method remains: :py:meth:`FormatConverter.convert`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from tnh_scholar.logging_config import get_child_logger

from ..timed_object import Granularity, TimedText, TimedTextUnit
from .srt_processor import (
    SRTProcessor,
)
from .text_segment_builder import TextSegmentBuilder
from .transcription_service import (
    TranscriptionResult,
)

logger = get_child_logger(__name__)

class FormatConverterConfig(BaseModel):
    """
    User-tunable knobs for :class:`FormatConverter`.

    Only a handful remain now that the heavy logic moved to `SegmentBuilder`.
    """

    max_entry_duration_ms: int = 6_000
    include_segment_index: bool = True
    include_speaker: bool = True
    characters_per_entry: int = 42
    max_gap_duration_ms: int = 2_000
    
class FormatConverter:
    """
    Convert a raw transcription result to *text*, *SRT*, or (placeholder) *VTT*.

    The *raw* result must follow the loose schema
    - ``{"utterances": [...]}`` -> already speaker-segmented
    - ``{"words":       [...]}`` -> word-level; we chunk via :class:`SegmentBuilder`
    - ``{"text": "...", "audio_duration_ms": 12345}`` -> single blob fallback
    """

    def __init__(self, config: Optional[FormatConverterConfig] = None):
        self.config = config or FormatConverterConfig()
        self._segment_builder = TextSegmentBuilder(
            max_duration_ms=self.config.max_entry_duration_ms,
            target_characters=self.config.characters_per_entry,
            avoid_orphans=True,
            ignore_speaker=not self.config.include_speaker,  
            max_gap_duration_ms=self.config.max_gap_duration_ms
        )

    def convert(
        self,
        result: TranscriptionResult,
        format_type: str = "srt",
        format_options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Convert *result* to the given *format_type*.

        Parameters
        ----------
        result : dict
            Raw transcription output.
        format_type : {"srt", "text", "vtt"}
        format_options : dict | None
            Currently only ``{"include_speaker": bool}`` recognized for *srt*.
        """
        format_type = format_type.lower()
        format_options = format_options or {}

        timed_text = self._build_timed_text(result)

        if format_type == "text":
            return self._to_plain_text(timed_text)

        if format_type == "srt":
            include_speaker = format_options.get("include_speaker", True)
            processor = SRTProcessor()
            return processor.generate(timed_text, include_speaker=include_speaker)

        if format_type == "vtt":
            raise NotImplementedError("VTT conversion not implemented yet.")

        raise ValueError(f"Unsupported format_type: {format_type}")

    def _to_plain_text(self, timed_text: TimedText) -> str:
        """Flatten ``TimedText`` into a newline-separated block of text."""
        return "\n".join(unit.text for unit in timed_text.segments if unit.text)

    def _build_timed_text(self, result: TranscriptionResult) -> TimedText:
        """
        Normalize *result* into :class:`TimedText`, handling three cases:

        1. *utterance*-level input (already segmented)
        2. *word*-level input  - chunk via :class:`SegmentBuilder`
        3. plain *text* fallback
        """
        
        if timed_text := result.utterance_timing:
            units: List[TimedTextUnit] = []
            for i, unit in enumerate(timed_text.iter_segments(), start=1):
                data = unit.model_copy()

                units.append(
                    TimedTextUnit(
                        granularity=Granularity.SEGMENT,
                        text=data.text,
                        start_ms=data.start_ms,
                        end_ms=data.end_ms,
                        speaker=data.speaker,
                        index=i,
                        confidence=data.confidence,
                    )
                )

            return TimedText(segments=units, granularity=Granularity.SEGMENT)

        if words := result.word_timing:
            # *SegmentBuilder* returns a list[TimedTextUnit]
            return self._segment_builder.create_segments(words)

        if text := result.text:
            duration_ms = result.audio_duration_ms

            units = [
                TimedTextUnit(
                    granularity=Granularity.SEGMENT,
                    text=text,
                    start_ms=0,
                    end_ms=duration_ms or 0,
                    speaker=None,
                    index=None,
                    confidence=None,
                )
            ]
            return TimedText(segments=units, granularity=Granularity.SEGMENT)

        # If we arrived here – nothing to work with.
        raise ValueError(
            "Cannot build TimedText: result contains no utterances, words, or text."
        )