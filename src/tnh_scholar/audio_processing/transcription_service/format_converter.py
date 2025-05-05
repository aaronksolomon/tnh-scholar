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

from tnh_scholar.audio_processing.transcription_service import (
    Granularity,
    SegmentBuilder,
    TimedText,
    TimedTextUnit,
)
from tnh_scholar.audio_processing.transcription_service.srt_processor import (
    SRTProcessor,
)
from tnh_scholar.logging_config import get_child_logger

logger = get_child_logger(__name__)


# --------------------------------------------------------------------------- #
# Utility helpers
# --------------------------------------------------------------------------- #
def convert_sec_to_ms(
    data: Dict[str, Any], source_field: str, target_field: str, label: str
) -> None:
    """
    In-place helper - convert a timing value expressed in **seconds** into
    milliseconds, storing it under ``target_field``.  Raises if value missing.

    Parameters
    ----------
    data, source_field, target_field : see implementation
    label : str
        Label used in error messages (“Word”, “Segment”, ...).
    """
    if source_field in data and target_field not in data:
        if data[source_field] is None:
            raise ValueError(f"{label} missing {source_field} timing: {data}")
        data[target_field] = int(data[source_field] * 1000)


# --------------------------------------------------------------------------- #
# Configuration dataclass
# --------------------------------------------------------------------------- #
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
    



# --------------------------------------------------------------------------- #
# Main facade
# --------------------------------------------------------------------------- #
class FormatConverter:
    """
    Convert a raw transcription result to *text*, *SRT*, or (placeholder) *VTT*.

    The *raw* result must follow the loose schema used by Whisper / OpenAI:
    - ``{"utterances": [...]}`` → already speaker-segmented
    - ``{"words":       [...]}`` → word-level; we chunk via :class:`SegmentBuilder`
    - ``{"text": "...", "audio_duration_ms": 12345}`` → single blob fallback
    """

    def __init__(self, config: Optional[FormatConverterConfig] = None):
        self.config = config or FormatConverterConfig()
        self._segment_builder = SegmentBuilder(
            max_duration=self.config.max_entry_duration_ms,
            target_characters=self.config.characters_per_entry,
            avoid_orphans=True,
            ignore_speaker=not self.config.include_speaker,  
            max_gap_duration=self.config.max_gap_duration_ms
        )

    # ...................................................... public API ...... #
    def convert(
        self,
        result: Dict[str, Any],
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

    # .................................................. internal helpers ... #
    def _to_plain_text(self, timed_text: TimedText) -> str:
        """Flatten ``TimedText`` into a newline-separated block of text."""
        return "\n".join(unit.text for unit in timed_text.segments if unit.text)

    def _build_timed_text(self, result: Dict[str, Any]) -> TimedText:
        """
        Normalize *result* into :class:`TimedText`, handling three cases:

        1. *utterance*-level input (already segmented)
        2. *word*-level input  - chunk via :class:`SegmentBuilder`
        3. plain *text* fallback
        """
        # -- 1. U T T E R A N C E S ---------------------------------------- #
        if utterances := result.get("utterances"):
            units: List[TimedTextUnit] = []
            for u in utterances:
                data = u.copy()
                convert_sec_to_ms(data, "start", "start_ms", "Utterance")
                convert_sec_to_ms(data, "end", "end_ms", "Utterance")

                units.append(
                    TimedTextUnit(
                        granularity=Granularity.SEGMENT,
                        text=data.get("text", ""),
                        start_ms=data["start_ms"],
                        end_ms=data["end_ms"],
                        speaker=data.get("speaker"),
                        index=None,
                        confidence=data.get("confidence"),
                    )
                )

            return TimedText(segments=units)

        # -- 2. W O R D S -------------------------------------------------- #
        if words := result.get("words"):
            # normalize timings to ms first
            for w in words:
                convert_sec_to_ms(w, "start", "start_ms", "Word")
                convert_sec_to_ms(w, "end", "end_ms", "Word")

            # *SegmentBuilder* returns a list[TimedTextUnit]
            return self._segment_builder.create_segments(words)


        # -- 3. P L A I N   T E X T --------------------------------------- #
        if text := result.get("text"):
            duration_ms = result.get(
                "audio_duration_ms", 0
            )
            units = [
                TimedTextUnit(
                    granularity=Granularity.SEGMENT,
                    text=text,
                    start_ms=0,
                    end_ms=duration_ms,
                    speaker=None,
                    index=None,
                    confidence=None,
                )
            ]
            return TimedText(segments=units)

        # If we arrived here – nothing to work with.
        raise ValueError(
            "Cannot build TimedText: result contains no utterances, words, or text."
        )