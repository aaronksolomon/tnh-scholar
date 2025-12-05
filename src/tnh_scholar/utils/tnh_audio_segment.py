
"""
TNHAudioSegment: A typed, minimal wrapper for pydub.AudioSegment.

This class provides a type-safe interface for working with audio segments using pydub, enabling
easier composition, slicing, and manipulation of audio data. It exposes common operations such as
concatenation, slicing, and length retrieval, while hiding the underlying pydub implementation.

Key features:
    - Type-annotated methods for static analysis and IDE support
    - Static constructors for silent and empty segments
    - Operator overloads for concatenation and slicing
    - Access to the underlying pydub.AudioSegment via the `raw` property

Extend this class with additional methods as needed for your audio processing workflows.
"""

from io import BytesIO
from pathlib import Path
from typing import Any, BinaryIO

from pydub import AudioSegment as _AudioSegment


class TNHAudioSegment:
    def __init__(self, segment: _AudioSegment):
        self._segment = segment

    @staticmethod
    def from_file(
        file: str | Path | BytesIO,
        format: str | None = None,
        **kwargs: Any,
    ) -> "TNHAudioSegment":
        """
        Wrapper: Load an audio file into a TNHAudioSegment.

        Args:
            file: Path to the audio file.
            format: Optional audio format (e.g., 'mp3', 'wav'). If None, pydub will attempt to infer it.
            **kwargs: Additional keyword arguments passed to pydub.AudioSegment.from_file.

        Returns:
            TNHAudioSegment instance containing the loaded audio.
        """
        return TNHAudioSegment(_AudioSegment.from_file(file, format=format, **kwargs))
    
    def export(self, out_f: str | BinaryIO, format: str, **kwargs: Any) -> None:
        """
        Wrapper: Export the audio segment to a file-like object or file path.

        Args:
            out_f: File path or file-like object to write the audio data to.
            format: Audio format (e.g., 'mp3', 'wav').
            **kwargs: Additional keyword arguments passed to pydub.AudioSegment.export.
        """
        self._segment.export(out_f, format=format, **kwargs)
        
    @staticmethod
    def silent(duration: int) -> "TNHAudioSegment":
        return TNHAudioSegment(_AudioSegment.silent(duration=duration))

    @staticmethod
    def empty() -> "TNHAudioSegment":
        return TNHAudioSegment(_AudioSegment.empty())

    def __getitem__(self, key: int | slice) -> "TNHAudioSegment":
        return TNHAudioSegment(self._segment[key]) # type: ignore

    def __add__(self, other: "TNHAudioSegment") -> "TNHAudioSegment":
        return TNHAudioSegment(self._segment + other._segment)

    def __iadd__(self, other: "TNHAudioSegment") -> "TNHAudioSegment":
        self._segment = self._segment + other._segment
        return self

    def __len__(self) -> int:
        return len(self._segment)

    # Add more methods as needed, e.g., export, from_file, etc.

    @property
    def raw(self) -> _AudioSegment:
        """Access the underlying pydub.AudioSegment if needed."""
        return self._segment
