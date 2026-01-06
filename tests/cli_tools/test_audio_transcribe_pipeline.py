from pathlib import Path

import pytest

from tnh_scholar.cli_tools.audio_transcribe.transcription_pipeline import (
    TranscriptionPipeline,
)


def test_pipeline_skips_diarization_for_assemblyai(tmp_path: Path) -> None:
    audio_path = tmp_path / "sample.mp3"
    audio_path.write_bytes(b"fake-audio")

    pipeline = TranscriptionPipeline(
        audio_file=audio_path,
        output_dir=tmp_path,
        transcriber="assemblyai",
    )

    pipeline._run_diarization = lambda: pytest.fail("diarization should be skipped")
    pipeline._transcribe_full_audio = lambda: ["ok"]

    assert pipeline.run() == ["ok"]
