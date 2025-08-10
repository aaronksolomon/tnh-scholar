# tnh_scholar.audio_processing.diarization.protocols.py
"""
Interfaces shared by diarization strategy classes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional, Protocol

from tnh_scholar.utils.tnh_audio_segment import TNHAudioSegment as AudioSegment

from .models import DiarizationChunk, DiarizedSegment


class SegmentAdapter(Protocol):
    def to_segments(
        self, 
        data: Any
        ) -> List[DiarizedSegment]: ...
        
        
class ChunkingStrategy(Protocol):
    """
    Protocol every chunking strategy must satisfy.
    """

    def extract(self, segments: List[DiarizedSegment]) -> List[DiarizationChunk]: ...
        

class AudioFetcher(Protocol):
    """Abstract audio provider for probing a segment."""

    def extract_audio(self, start_ms: int, end_ms: int) -> Path: ...

    
class LanguageDetector(Protocol):
    """Abstract language detector (e.g., fastText, Whisper-lang)."""

    def detect(self, audio: AudioSegment, format_str: str) -> Optional[str]: ...