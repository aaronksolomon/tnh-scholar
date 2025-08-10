
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from tnh_scholar.audio_processing.diarization import diarize
from tnh_scholar.audio_processing.diarization.audio import AudioHandler
from tnh_scholar.audio_processing.diarization.config import DiarizationConfig
from tnh_scholar.audio_processing.diarization.pyannote_adapter import PyannoteAdapter
from tnh_scholar.audio_processing.diarization.strategies.time_gap import TimeGapChunker
from tnh_scholar.audio_processing.transcription import (
    TranscriptionServiceFactory,
    patch_whisper_options,
)
from tnh_scholar.utils.file_utils import ensure_directory_exists


class TranscriptionPipeline:
    def __init__(
        self,
        audio_file: Path,
        output_dir: Path,
        diarization_config: Optional[DiarizationConfig] = None,
        transcriber: str = "whisper",
        transcription_options: Optional[Dict[str, Any]] = None,
        diarization_kwargs: Optional[Dict[str, Any]] = None,
    ):
        self.audio_file = audio_file
        self.output_dir = output_dir
        self.diarization_config = diarization_config or DiarizationConfig()
        self.transcriber = transcriber
        self.transcription_options = patch_whisper_options(
            transcription_options, 
            file_extension=audio_file.suffix
            ) 
        self.diarization_kwargs = diarization_kwargs or {}
        self.diarization_dir = self.output_dir / f"{self.audio_file.stem}_diarization"
        self.diarization_results_path = self.diarization_dir / "raw_diarization_results.json"
        ensure_directory_exists(self.output_dir)
        ensure_directory_exists(self.diarization_dir)
        
        self.audio_file_extension = audio_file.suffix

    def run(self) -> List[str]:
        segments = self._run_and_load_diarization()
        chunk_list = self._chunk_segments(segments)
        self._extract_audio_chunks(chunk_list)
        return self._transcribe_chunks(chunk_list)

    def _run_and_load_diarization(self):
        if not self.diarization_results_path.exists():
            diarize(
                self.audio_file,
                output_path=self.diarization_results_path,
                **self.diarization_kwargs
            )
        return self._load_diarization_result()

    def _load_diarization_result(self):
        with open(self.diarization_results_path, "r") as f:
            raw_diarization = json.load(f)
        adapter = PyannoteAdapter(config=self.diarization_config)
        return adapter.to_segments(raw_diarization["output"])

    def _chunk_segments(self, segments):
        chunker = TimeGapChunker(config=self.diarization_config)
        return chunker.extract(segments)

    def _extract_audio_chunks(self, chunk_list):
        audio_handler = AudioHandler()
        for chunk in chunk_list:
            audio_handler.build_audio_chunk(chunk, audio_file=self.audio_file)

    def _transcribe_chunks(self, chunk_list):
        ts_service = TranscriptionServiceFactory.create_service(provider=self.transcriber)
        transcripts = []
        for chunk in chunk_list:
            audio = chunk.audio
            if not audio:
                raise ValueError("No audio data for chunk")
            audio_obj = audio.data
            transcript = ts_service.transcribe(
                audio_obj, 
                self.transcription_options, 
                )
            transcripts.append(transcript.text)
        return transcripts