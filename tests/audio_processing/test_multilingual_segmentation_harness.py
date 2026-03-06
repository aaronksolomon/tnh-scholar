from __future__ import annotations

import wave
from pathlib import Path

from tnh_scholar.audio_processing.diarization.config import (
    DiarizationConfig,
    LanguageConfig,
    SpeakerConfig,
)
from tnh_scholar.audio_processing.diarization.models import DiarizedSegment
from tnh_scholar.audio_processing.multilingual_models import (
    MultilingualTranscriptionRequest,
)
from tnh_scholar.audio_processing.multilingual_service import (
    SpeakerBlockLanguageSegmentationService,
)
from tnh_scholar.utils import TimeMs


class FakeLanguageDetector:
    def __init__(self, responses: list[str | None]) -> None:
        self._responses = list(responses)
        self.calls: list[tuple[int, str]] = []

    def detect(self, audio, format_str: str) -> str | None:
        self.calls.append((len(audio), format_str))
        if self._responses:
            return self._responses.pop(0)
        return None


def _write_silent_wav(path: Path, duration_ms: int = 3000) -> None:
    frame_rate = 16000
    frame_count = int(frame_rate * (duration_ms / 1000))
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(frame_rate)
        wav_file.writeframes(b"\x00\x00" * frame_count)


def _segment(
    speaker: str,
    start_ms: int,
    end_ms: int,
) -> DiarizedSegment:
    return DiarizedSegment(
        speaker=speaker,
        start=TimeMs(start_ms),
        end=TimeMs(end_ms),
        audio_map_start=None,
        gap_before=None,
        spacing_time=None,
    )


def test_segmentation_groups_same_speaker_within_gap(tmp_path: Path) -> None:
    audio_file = tmp_path / "sample.wav"
    _write_silent_wav(audio_file)
    detector = FakeLanguageDetector(["vi"])
    service = SpeakerBlockLanguageSegmentationService(detector=detector)
    request = MultilingualTranscriptionRequest(
        audio_file=audio_file,
        diarization_segments=[
            _segment("SPEAKER_00", 0, 500),
            _segment("SPEAKER_00", 600, 1000),
        ],
        use_speaker_blocks=True,
    )

    blocks = service.build_blocks(request)

    assert len(blocks) == 1
    assert blocks[0].speaker_label == "SPEAKER_00"
    assert blocks[0].start_ms == 0
    assert blocks[0].end_ms == 1000
    assert blocks[0].detection.language_code == "vi"


def test_segmentation_splits_same_speaker_when_gap_exceeds_threshold(tmp_path: Path) -> None:
    audio_file = tmp_path / "sample.wav"
    _write_silent_wav(audio_file)
    config = DiarizationConfig(
        speaker=SpeakerConfig(same_speaker_gap_threshold=TimeMs(100)),
    )
    detector = FakeLanguageDetector(["en", "vi"])
    service = SpeakerBlockLanguageSegmentationService(
        diarization_config=config,
        detector=detector,
    )
    request = MultilingualTranscriptionRequest(
        audio_file=audio_file,
        diarization_segments=[
            _segment("SPEAKER_00", 0, 500),
            _segment("SPEAKER_00", 700, 1200),
        ],
        use_speaker_blocks=True,
    )

    blocks = service.build_blocks(request)

    assert len(blocks) == 2
    assert blocks[0].detection.language_code == "en"
    assert blocks[1].detection.language_code == "vi"


def test_segmentation_splits_when_speaker_changes(tmp_path: Path) -> None:
    audio_file = tmp_path / "sample.wav"
    _write_silent_wav(audio_file)
    detector = FakeLanguageDetector(["en", "zh"])
    service = SpeakerBlockLanguageSegmentationService(detector=detector)
    request = MultilingualTranscriptionRequest(
        audio_file=audio_file,
        diarization_segments=[
            _segment("SPEAKER_00", 0, 500),
            _segment("SPEAKER_01", 520, 900),
        ],
        use_speaker_blocks=True,
    )

    blocks = service.build_blocks(request)

    assert len(blocks) == 2
    assert blocks[0].speaker_label == "SPEAKER_00"
    assert blocks[1].speaker_label == "SPEAKER_01"


def test_segmentation_skips_detector_when_source_language_is_provided(tmp_path: Path) -> None:
    audio_file = tmp_path / "sample.wav"
    _write_silent_wav(audio_file)
    detector = FakeLanguageDetector(["vi"])
    service = SpeakerBlockLanguageSegmentationService(detector=detector)
    request = MultilingualTranscriptionRequest(
        audio_file=audio_file,
        source_language="en",
        diarization_segments=[_segment("SPEAKER_00", 0, 500)],
        use_speaker_blocks=True,
    )

    blocks = service.build_blocks(request)

    assert len(blocks) == 1
    assert blocks[0].detection.language_code == "en"
    assert blocks[0].detection.detector_source == "request"
    assert detector.calls == []


def test_segmentation_marks_unknown_language_as_uncertain(tmp_path: Path) -> None:
    audio_file = tmp_path / "sample.wav"
    _write_silent_wav(audio_file)
    detector = FakeLanguageDetector([None])
    service = SpeakerBlockLanguageSegmentationService(detector=detector)
    request = MultilingualTranscriptionRequest(
        audio_file=audio_file,
        diarization_segments=[_segment("SPEAKER_00", 0, 500)],
        use_speaker_blocks=True,
    )

    blocks = service.build_blocks(request)

    assert len(blocks) == 1
    assert blocks[0].detection.language_code is None
    assert blocks[0].detection.confidence == 0.0
    assert blocks[0].detection.is_reliable is False
    assert blocks[0].is_uncertain is True


def test_segmentation_uses_configured_probe_window_length(tmp_path: Path) -> None:
    audio_file = tmp_path / "sample.wav"
    _write_silent_wav(audio_file)
    config = DiarizationConfig(
        language=LanguageConfig(probe_time=400, export_format="wav"),
    )
    detector = FakeLanguageDetector(["en"])
    service = SpeakerBlockLanguageSegmentationService(
        diarization_config=config,
        detector=detector,
    )
    request = MultilingualTranscriptionRequest(
        audio_file=audio_file,
        diarization_segments=[_segment("SPEAKER_00", 0, 1200)],
        use_speaker_blocks=True,
    )

    blocks = service.build_blocks(request)

    assert len(blocks) == 1
    assert detector.calls == [(400, "wav")]
