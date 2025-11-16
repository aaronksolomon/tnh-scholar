from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from dotenv import load_dotenv

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils.file_utils import ensure_directory_exists, write_str_to_file

from .protocols import DiarizationService, ResultWriter
from .pyannote_adapter import PyannoteAdapter
from .pyannote_client import PyannoteClient
from .schemas import (
    DiarizationParams,
    DiarizationResponse,
    DiarizationSucceeded,
    JobHandle,
    JobStatusResponse,
)

# Load environment variables
load_dotenv()

logger = get_child_logger(__name__)

PYANNOTE_FILE_STR = "_pyannote_diarization"


class FileResultWriter:
    """Default file-system writer to JSON."""

    def write(self, path: Path, response: DiarizationResponse) -> Path:
        ensure_directory_exists(path.parent)
        write_str_to_file(path, response.model_dump_json(indent=2), overwrite=True)
        logger.debug(f"DiarizationResponse saved to {path}")
        return path


class PyannoteService(DiarizationService):
    """Concrete implementation of DiarizationService for pyannote.ai.

    Bridges transport (PyannoteClient) and mapping (PyannoteAdapter) while
    exposing a clean domain-facing API.
    """

    def __init__(self, client: Optional[PyannoteClient] = None, adapter: Optional[PyannoteAdapter] = None):
        self.client = client or PyannoteClient()
        self.adapter = adapter or PyannoteAdapter()

    # --- DiarizationService protocol ---
    def start(self, audio_path: Path, params: Optional[DiarizationParams] = None) -> str:
        media_id = self.client.upload_audio(audio_path)
        if not media_id:
            return ""
        job_id = self.client.start_diarization(media_id, params=params)
        return job_id or ""

    def get_response(self, job_id: str, *, wait_until_complete: bool = False) -> DiarizationResponse:
        jsr: Optional[JobStatusResponse]
        
        jsr = self.client.poll_job_until_complete(job_id, wait_until_complete)
        
        return self.adapter.to_response(jsr)

    def generate(
        self, 
        audio_path: Path, 
        params: Optional[DiarizationParams] = None, 
        *, 
        wait_until_complete: bool = True
        ) -> DiarizationResponse:
        if job_id := self.start(audio_path, params=params):
            return self.get_response(job_id, wait_until_complete=wait_until_complete)
        return self.adapter.failed_start()



# ===== Orchestrator ===========================================================

class DiarizationProcessor:
    """Orchestrator over a DiarizationService.

    This layer delegates to the service for generation and handles persistence.
    """

    def __init__(
        self,
        audio_file_path: Path,
        output_path: Optional[Path] = None,
        *,
        service: Optional[DiarizationService] = None,
        params: Optional[DiarizationParams] = None,
        api_key: Optional[str] = None,
        writer: Optional[ResultWriter] = None,
    ) -> None:
        self.audio_file_path: Path = audio_file_path.resolve()
        if not self.audio_file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        # Default output path
        self.output_path: Path = (
            output_path.resolve()
            if output_path is not None
            else self.audio_file_path.parent / f"{self.audio_file_path.stem}{PYANNOTE_FILE_STR}.json"
        )

        # Service & config
        # If a concrete service is not provided, default to PyannoteService.
        # Only pass api_key to PyannoteClient if it is not None.
        default_client = PyannoteClient(api_key) if api_key is not None else PyannoteClient()
        self.service: DiarizationService = service or PyannoteService(default_client)
        self.params: Optional[DiarizationParams] = params
        self.writer: ResultWriter = writer or FileResultWriter()

        # Cached state
        self._last_response: Optional[DiarizationResponse] = None
        self._last_job_id: Optional[str] = None

    # ---- Two-phase job control (nice for UIs) --------------------------------

    def start(self) -> JobHandle:
        """Start a job and cache its job_id."""
        job_id = self.service.start(self.audio_file_path, params=self.params)
        if not job_id:
            raise RuntimeError("Diarization service returned empty job_id")
        self._last_job_id = job_id
        return JobHandle(job_id=job_id)

    def get_response(
        self, job: Optional[Union[JobHandle, str]] = None, *, wait_until_complete: bool = False
        ) -> DiarizationResponse:
        """Fetch current/final response for a job, caching the last response."""
        target_id: Optional[str]
        if isinstance(job, JobHandle):
            target_id = job.job_id
        else:
            target_id = job or self._last_job_id
        if target_id is None:
            raise ValueError(
                "No job_id provided and no previous job has been started. Call start() or pass a job_id."
            )
        resp = self.service.get_response(target_id, wait_until_complete=wait_until_complete)
        self._last_response = resp
        return resp

    # ---- One-shot path --------------------------------------------------------

    def generate(self, *, wait_until_complete: bool = True) -> DiarizationResponse:
        """One-shot convenience: delegate to the service and cache the response."""
        resp = self.service.generate(
            self.audio_file_path, 
            params=self.params, 
            wait_until_complete=wait_until_complete
            )
        self._last_response = resp
        # If the service exposes a job_id in the envelope, cache it for UIs
        # Do not fail on metadata issues; response is primary.
        try:
            job_id = getattr(resp, "job_id", None)
            if isinstance(job_id, str):
                self._last_job_id = job_id
        except (AttributeError, TypeError) as e:
            logger.warning(f"Could not extract job_id from response: {e}")
        return resp

    # ---- Persistence ----------------------------------------------------------

    def export(self, response: Optional[DiarizationResponse] = None) -> Path:
        """Write the provided or last response to `self.output_path`."""
        result = response or self._last_response
        if result is None:
            raise ValueError(
                "No DiarizationResponse available; call generate()/get_response() first or pass response="
                )
        return self.writer.write(self.output_path, result)


# ===== Convenience functions ==================================================

def diarize(
    audio_file_path: Path,
    output_path: Optional[Path] = None,
    *,
    params: Optional[DiarizationParams] = None,
    service: Optional[DiarizationService] = None,
    api_key: Optional[str] = None,
    wait_until_complete: bool = True,
) -> DiarizationResponse:
    """One-shot convenience to generate a result and (optionally) write it.

    This returns the `DiarizationResponse`. Writing is left to callers or
    `diarize_to_file` below.
    """
    processor = DiarizationProcessor(
        audio_file_path,
        output_path=output_path,
        service=service,
        params=params,
        api_key=api_key,
    )
    return processor.generate(wait_until_complete=wait_until_complete)


def diarize_to_file(
    audio_file_path: Path,
    output_path: Optional[Path] = None,
    *,
    params: Optional[DiarizationParams] = None,
    service: Optional[DiarizationService] = None,
    api_key: Optional[str] = None,
    wait_until_complete: bool = True,
) -> DiarizationResponse:
    """Convenience helper: generate then export to JSON if successful; returns response"""
    processor = DiarizationProcessor(
        audio_file_path,
        output_path=output_path,
        service=service,
        params=params,
        api_key=api_key,
    )
    response = processor.generate(wait_until_complete=wait_until_complete)
    if isinstance(response, DiarizationSucceeded):
        processor.export()
    return response