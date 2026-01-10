import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from tnh_scholar.audio_processing.diarization.audio import AudioHandler
from tnh_scholar.audio_processing.diarization.config import DiarizationConfig
from tnh_scholar.audio_processing.diarization.schemas import (
    DiarizationFailed,
    DiarizationPending,
    DiarizationResponse,
    DiarizationRunning,
    DiarizationSucceeded,
)
from tnh_scholar.audio_processing.diarization.strategies.time_gap import TimeGapChunker
from tnh_scholar.audio_processing.transcription import (
    TranscriptionServiceFactory,
    patch_whisper_options,
)
from tnh_scholar.utils.file_utils import ensure_directory_writable


class TranscriptionPipeline:
    def __init__(
        self,
        audio_file: Path,
        output_dir: Path,
        diarization_config: Optional[DiarizationConfig] = None,
        transcriber: str = "whisper",
        transcription_options: Optional[Dict[str, Any]] = None,
        diarization_kwargs: Optional[Dict[str, Any]] = None,
        save_diarization: bool = True,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the TranscriptionPipeline.

        Args:
            audio_file (Path): Path to the audio file to process.
            output_dir (Path): Directory to store output files.
            diarization_config (Optional[DiarizationConfig]): Diarization configuration.
            transcriber (str): Transcription service provider.
            transcription_options (Optional[Dict[str, Any]]): Options for transcription.
            diarization_kwargs (Optional[Dict[str, Any]]): Additional diarization arguments.
            save_diarization (bool): Whether to save raw diarization JSON results.
            logger (Optional[logging.Logger]): Logger for pipeline events.
        """
        self.logger = logger or logging.getLogger(__name__)
        self._validate_audio_file(audio_file)
        self._validate_output_dir(output_dir)

        self.audio_file = audio_file
        self.output_dir = output_dir
        self.diarization_config = diarization_config or DiarizationConfig()
        self.transcriber = transcriber
        if transcriber == "whisper":
            self.transcription_options = patch_whisper_options(
                transcription_options,
                file_extension=audio_file.suffix
            )
        else:
            self.transcription_options = transcription_options
        self.diarization_kwargs = diarization_kwargs or {}
        self.save_diarization = save_diarization

        if self.save_diarization:
            self.diarization_dir = self.output_dir / f"{self.audio_file.stem}_diarization"
            self.diarization_results_path = self.diarization_dir / "raw_diarization_results.json"
        else:
            self.diarization_dir = None
            self.diarization_results_path = None

        ensure_directory_writable(self.output_dir)
        if self.save_diarization:
            assert self.diarization_dir
            ensure_directory_writable(self.diarization_dir)

        self.audio_file_extension = audio_file.suffix

    def _validate_audio_file(self, audio_file: Path | str) -> None:
        """
        Validate the audio file input.

        Args:
            audio_file (Union[str, Path]): Path to the audio file.

        Raises:
            TypeError: If not a str or Path instance.
            FileNotFoundError: If file does not exist.
        """
        if isinstance(audio_file, str):
            audio_file = Path(audio_file)
        elif not isinstance(audio_file, Path):
            raise TypeError("audio_file must be a str or pathlib.Path instance")
        if not audio_file.exists() or not audio_file.is_file():
            raise FileNotFoundError(f"Audio file does not exist: {audio_file}")

    def _validate_output_dir(self, output_dir: Path | str) -> None:
        """
        Validate the output directory

        Args:
            output_dir (Path | str): Path to the output directory.

        Raises:
            TypeError: If not a Path or str instance.
        """
        if isinstance(output_dir, str):
            output_dir = Path(output_dir)
        elif not isinstance(output_dir, Path):
            raise TypeError("output_dir must be a str or pathlib.Path instance")


    def run(self) -> Optional[List[Dict[str, Any]]]:
        """
        Execute the full transcription pipeline with robust error handling.

        Returns:
            List[Dict[str, Any]]: List of transcript dicts with chunk metadata, or None on failure

        Raises:
            RuntimeError: If any pipeline step fails.
        """
        try:
            if self._should_skip_diarization():
                self.logger.info("Skipping diarization; transcribing full audio.")
                return self._transcribe_full_audio()
            self.logger.info("Starting diarization step.")
            segments = self._run_diarization()
            if not segments:
                self.logger.warning("No diarization segments found.")
                return []
            self.logger.info("Chunking segments.")
            chunk_list = self._chunk_segments(segments)
            if not chunk_list:
                self.logger.warning("No chunks produced from segments.")
                return []
            self.logger.info("Extracting audio chunks.")
            self._extract_audio_chunks(chunk_list)
            self.logger.info("Transcribing chunks.")
            return self._transcribe_chunks(chunk_list)
        except Exception as exc:
            self._handle_pipeline_error(exc)
            return None

    def _should_skip_diarization(self) -> bool:
        """
        AssemblyAI can handle long-form audio without pyannote chunking.
        """
        return self.transcriber == "assemblyai"

    def _transcribe_full_audio(self) -> List[Dict[str, Any]]:
        """
        Transcribe the full audio file without diarization/chunking.
        """
        ts_service = TranscriptionServiceFactory.create_service(provider=self.transcriber)
        transcript = ts_service.transcribe(self.audio_file, self.transcription_options)
        return [
            {
                "chunk": None,
                "transcript": transcript.text,
                "error": None,
            }
        ]

    def _run_diarization(self) -> List[Any]:
        """
        Orchestrate diarization and return domain-level segments.
        Uses structural pattern matching on the discriminated union.
        """
        # local import to avoid cycles
        from tnh_scholar.audio_processing.diarization import diarize, diarize_to_file

        diarization_response: DiarizationResponse
        if self.save_diarization:
            diarization_response = diarize_to_file(
                audio_file_path=self.audio_file,
                output_path=self.diarization_results_path,
                wait_until_complete=True, # for this module defaulting to unlimited processing time
                **(self.diarization_kwargs or {})
            )
        else:
            diarization_response = diarize(
                self.audio_file,
                wait_until_complete=True,
                **(self.diarization_kwargs or {})
            )
        if diarization_response is None:
            raise RuntimeError("Diarizer returned None response")

        # Discriminated-union matching
        match diarization_response:
            case DiarizationSucceeded(result=out):
                segments: List[Any] | None = getattr(out, "segments", None)
                if segments is None:
                    raise RuntimeError("DiarizationSucceeded missing 'segments'")
                self.logger.info(f"Diarization succeeded: {len(segments)} segments.")
                return segments

            case DiarizationFailed(error=err):
                raise RuntimeError(f"Diarization failed: {getattr(err, 'message', err)}")

            case DiarizationPending() | DiarizationRunning():
                raise RuntimeError("Diarization incomplete (pending/running).")

            case _:
                response_type = type(diarization_response).__name__
                job_id = getattr(diarization_response, "job_id", None)
                self.logger.error(
                    f"Unhandled diarization response variant: {response_type} (job_id={job_id})"
                )
                raise RuntimeError("Unhandled diarization response variant")

    def _chunk_segments(self, segments: List[Any]) -> List[Any]:
        """
        Chunk diarization segments with error handling.
        """
        try:
            chunker = TimeGapChunker(config=self.diarization_config)
            chunks: List[Any] = chunker.extract(segments)
            if not chunks:
                self.logger.warning("No chunks produced from segments.")
            return chunks
        except Exception as exc:
            self.logger.error(f"Chunking segments failed: {exc}")
            raise RuntimeError(f"Chunking segments failed: {exc}") from exc

    def _extract_audio_chunks(self, chunk_list: List[Any]) -> None:
        """
        Extract audio chunks with error handling.
        Remove failed chunks from the list and add error metadata for traceability.
        """
        audio_handler = AudioHandler()
        successful_chunks: List[Any] = []
        for chunk in chunk_list:
            try:
                audio_handler.build_audio_chunk(chunk, audio_file=self.audio_file)
                successful_chunks.append(chunk)
            except Exception as exc:
                self.logger.error(f"Audio chunk extraction failed for chunk {chunk}: {exc}")
                # Do not add chunk to successful_chunks, effectively removing it from further processing
        # Update chunk_list in place to only include successful chunks
        chunk_list[:] = successful_chunks

    def _transcribe_chunks(self, chunk_list: List[Any]) -> List[Dict[str, Any]]:
        """
        Transcribe audio chunks with error handling.
        """
        ts_service = TranscriptionServiceFactory.create_service(provider=self.transcriber)
        transcripts: List[Dict[str, Any]] = []
        for chunk in chunk_list:
            transcript_text = None
            error_detail = None
            try:
                audio = chunk.audio
                if not audio:
                    self.logger.warning(f"No audio data for chunk {chunk}. Skipping transcription.")
                    continue
                audio_obj = audio.data
                transcript = ts_service.transcribe(
                    audio_obj,
                    self.transcription_options,
                )
                transcript_text = transcript.text
                error_detail = None
            except Exception as exc:
                self.logger.error(f"Transcription failed for chunk {chunk}: {exc}")
                transcript_text = None
                error_detail = str(exc)
            transcripts.append({
                "chunk": chunk,
                "transcript": transcript_text,
                "error": error_detail
            })
        return transcripts

    def _handle_pipeline_error(self, exc: Exception) -> None:
        """
        Handle pipeline errors in a modular way.

        Args:
            exc (Exception): The exception to handle.

        Raises:
            RuntimeError: Always re-raises the error after logging.
        """
        self.logger.error(f"TranscriptionPipeline failed: {exc}")
        raise RuntimeError(f"TranscriptionPipeline failed: {exc}") from exc
