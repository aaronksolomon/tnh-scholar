# tnh_scholar.audio_processing.diarization.protocols.py
"""
Interfaces shared by diarization strategy classes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional, Protocol, runtime_checkable

from tnh_scholar.utils.tnh_audio_segment import TNHAudioSegment as AudioSegment

from .models import DiarizationChunk, DiarizedSegment
from .schemas import DiarizationParams, DiarizationResponse


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
    
@runtime_checkable
class DiarizationService(Protocol):
    """Protocol for any diarization service."""

    def start(self, audio_path: Path, params: Optional[DiarizationParams] = None) -> str:
        """Start a diarization job and return an opaque job_id.""" 
        ...
        

    def get_response(self, job_id: str, *, wait_until_complete: bool = False) -> DiarizationResponse: 
        """Return the current state or final result as a DiarizationResponse.

            When `wait_until_complete` is True, the service blocks until a terminal
            state (succeeded/failed/timeout) and returns that envelope.
            """
        ...

    def generate(
        self,
        audio_path: Path,
        params: Optional[DiarizationParams] = None,
        *,
        wait_until_complete: bool = True,
    ) -> DiarizationResponse: 
        ...
        """One-shot convenience: start + (optionally) wait + fetch + map.

        Implementations may optimize this path; default behavior can be
        start() followed by get_response().
        """
        
class ResultWriter(Protocol):
    """Port for persisting diarization results."""

    def write(self, path: Path, response: DiarizationResponse) -> Path:
        ...