# tnh_scholar.audio_processing.diarization.strategies.language_probe.py
"""
Lightweight language-detection helpers pluggable into chunkers.
"""

from __future__ import annotations

from typing import Optional

from tnh_scholar.audio_processing.transcription import patch_whisper_options
from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils import TimeMs
from tnh_scholar.utils import TNHAudioSegment as AudioSegment

from ..audio.handler import AudioHandler
from ..config import DiarizationConfig
from ..models import AugDiarizedSegment
from ..protocols import LanguageDetector

logger = get_child_logger(__name__)


class WhisperLanguageDetector:
    """Language detector using Whisper service."""
    
    def __init__(self, model: str = "whisper-1", audio_handler: Optional[AudioHandler] = None):
        self.model = model
        self.audio_handler = audio_handler or AudioHandler()

    def detect(self, audio: AudioSegment, format_str: str) -> Optional[str]:
        from tnh_scholar.audio_processing.transcription.whisper_service import WhisperTranscriptionService
        whisper = WhisperTranscriptionService(model=self.model, language=None, response_format="verbose_json")
        try:
            audio_bytes = self.audio_handler.export_audio_bytes(audio, format_str=format_str)
            options = patch_whisper_options(options = None, file_extension=format_str)
            result = whisper.transcribe(audio_bytes, options=options)
            logger.debug(f"full transcription result: {result}")
            return self._extract_language_from_result(result)
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return None
        
    def _extract_language_from_result(self, result) -> Optional[str]:
        """Extract language code from transcription result."""
        return getattr(result, 'language', None)
            

class LanguageProbe:
    def __init__(self, config: DiarizationConfig, detector: LanguageDetector):
        self.probe_time = config.language.probe_time
        self.export_format = config.language.export_format
        self.detector = detector
        
    def segment_language(
        self,
        aug_segment: AugDiarizedSegment,
    ) -> str:
        """
        Get segment ISO-639 language code from an Augmented Diarize Segment which contains audio.

        The probe window is always relative to the segment audio (0=start, duration=end).
        """
        probe_start, probe_end = self._calculate_probe_window(aug_segment)

        if aug_segment.audio is None:
            raise ValueError(f"Segment Audio has not been set: {aug_segment}")

        # All slicing is relative to the segment audio (0 to duration)
        audio_segment = aug_segment.audio[probe_start:probe_end]
        language = self.detector.detect(audio_segment, self.export_format)

        if language is not None:
            return language
        logger.warning(f"No language detected in language probe for segment {aug_segment}.")
        return "unknown"
    
    def _calculate_probe_window(
        self,
        aug_segment: AugDiarizedSegment,
    ) -> tuple[TimeMs, TimeMs]:
        """
        Calculate start/end times for language probe sampling, 
        always relative to the segment audio (0 to duration).
        """
        duration = aug_segment.duration
        if duration <= self.probe_time:
            return TimeMs(0), duration
        return self._extract_center_window(duration)

    def _extract_center_window(
        self,
        duration: TimeMs,
    ) -> tuple[TimeMs, TimeMs]:
        """
        Extract probe window from center of segment audio (relative time).
        """
        center_time = duration // 2
        half_probe = self.probe_time // 2

        probe_start = TimeMs(max(0, center_time - half_probe))
        probe_end = TimeMs(min(duration, center_time + half_probe))

        return probe_start, probe_end


# original audio fetcher implementation using file based IO, for reference

# class SimpleAudioFetcher:
#     """Extract audio segments for language probing."""
    
#     def __init__(self, source_audio: Path, temp_dir: Optional[Path] = None):
#         self.source_audio = source_audio
#         self.temp_dir = temp_dir or Path.cwd() / "temp_audio"
#         self.temp_dir.mkdir(exist_ok=True)
    
#     def extract_audio(self, start_ms: int, end_ms: int) -> Path:
#         """Extract audio segment to temporary file."""
#         import subprocess
        
#         output_path = self.temp_dir / f"probe_{start_ms}_{end_ms}.wav"
#         cmd = [
#             "ffmpeg", "-i", str(self.source_audio),
#             "-ss", str(start_ms/1000), "-t", str((end_ms-start_ms)/1000),
#             "-y", str(output_path)
#         ]
#         subprocess.run(cmd, capture_output=True, check=True)
#         return output_path