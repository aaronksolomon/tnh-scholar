"""
pyannote_client.py

Client interface for interacting with the pyannote.ai speaker diarization API.

This module provides a robust, object-oriented client for uploading audio files,
starting diarization jobs, polling for job completion, and retrieving results
from the pyannote.ai API. It includes retry logic, configurable timeouts, and
support for advanced diarization parameters.

Typical usage:
    client = PyannoteClient(api_key="your_api_key")
    media_id = client.upload_audio(Path("audio.mp3"))
    job_id = client.start_diarization(media_id)
    result = client.poll_job_until_complete(job_id)
"""

from __future__ import annotations

import os
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv
from tenacity import (
    RetryError,
    Retrying,
    retry,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    stop_after_delay,
    stop_never,
    wait_exponential_jitter,
)

from tnh_scholar.exceptions import ConfigurationError
from tnh_scholar.logging_config import get_child_logger

from .config import PollingConfig, PyannoteConfig
from .schemas import DiarizationParams, JobStatus, JobStatusResponse, PollOutcome

# Load environment variables
load_dotenv()

logger = get_child_logger(__name__)


class APIKeyError(Exception):
    """Raised when API key is missing or invalid."""


# Response field keys used by the remote API
JOB_ID_FIELD = "jobId"


class _PollSignal(Enum):
    CONTINUE = "continue"              # internal: keep polling
    STATUS_RETRY_EXHAUSTED = "status_retry_exhausted"  # internal: status_fn retried and failed


class PyannoteClient:
    """Client for interacting with the pyannote.ai speaker diarization API."""

    def __init__(self, api_key: Optional[str] = None, config: Optional[PyannoteConfig] = None):
        """
        Initialize with API key.

        Args:
            api_key: Pyannote.ai API key (defaults to environment variable)
        """
        self.api_key = api_key or os.getenv("PYANNOTEAI_API_TOKEN")
        if not self.api_key:
            raise APIKeyError(
                "API key is required. Set PYANNOTEAI_API_TOKEN environment "
                "variable or pass as parameter"
            )

        self.config = config or PyannoteConfig()
        self.polling_config = self.config.polling_config

        # Upload-specific timeouts (longer than general calls)
        self.upload_timeout = self.config.upload_timeout
        self.upload_max_retries = self.config.upload_max_retries
        self.network_timeout = self.config.network_timeout

        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    # -----------------------
    # Upload helpers
    # -----------------------
    def _create_media_id(self) -> str:
        """Generate a unique media ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return f"{self.config.media_prefix}{timestamp}"

    def _upload_file(self, file_path: Path, upload_url: str) -> bool:
        """
        Upload file to the provided URL.

        Args:
            file_path: Path to the file to upload
            upload_url: URL to upload to

        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            logger.info(f"Uploading file to Pyannote.ai: {file_path}")
            with open(file_path, "rb") as file_data:
                upload_response = requests.put(
                    upload_url,
                    data=file_data,
                    headers={"Content-Type": self.config.media_content_type},
                    timeout=self.upload_timeout,
                )

            upload_response.raise_for_status()
            logger.info("File uploaded successfully")
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to upload file: {e}")
            return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(exp_base=2, initial=3, max=30),
        retry=retry_if_exception_type(
            (requests.RequestException, requests.Timeout, requests.ConnectionError)
            ),
    )
    def upload_audio(self, file_path: Path) -> Optional[str]:
        """
        Upload audio file with retry logic for network robustness.

        Retries on network errors with exponential backoff.
        Fails fast on permanent errors (auth, file not found, etc.).
        """
        try:
            if not file_path.exists() or not file_path.is_file():
                logger.error(f"Audio file not found or is not a file: {file_path}")
                return None
        except OSError as e:
            logger.error(f"Error accessing audio file '{file_path}': {e}")
            return None

        try:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
        except OSError as e:
            logger.error(f"Error reading file size for '{file_path}': {e}")
            return None

        logger.info(f"Starting upload of {file_path.name} ({file_size_mb:.1f}MB)")

        try:
            # Create media ID
            media_id = self._create_media_id()
            logger.debug(f"Created media ID: {media_id}")

            # Get upload URL (this is fast, use normal timeout)
            upload_url = self._data_upload_url(media_id)
            if not upload_url:
                return None

            # Upload file (this is slow, use extended timeout)
            if self._upload_file(file_path, upload_url):
                logger.info(f"Upload completed successfully: {media_id}")
                return media_id
            else:
                logger.error(f"Upload failed for {file_path.name}")
                return None

        except Exception as e:
            # Log but don't retry - let tenacity handle retries
            logger.error(f"Upload attempt failed: {e}")
            raise  # Re-raise for tenacity to handle

    def _data_upload_url(self, media_id: str) -> Optional[str]:
        response = requests.post(
            self.config.media_input_endpoint,
            headers=self.headers,
            json={"url": media_id},
            timeout=self.network_timeout,
        )
        upload_url = self._extract_response_info(
            response, "url", "No upload URL in API response"
        )
        logger.debug(f"Got upload URL for media ID: {media_id}")
        return upload_url
    
    def _extract_response_info(self, response, response_type, error_msg):
        response.raise_for_status()
        info = response.json()
        if result := info.get(response_type):
            return result
        else:
            raise ValueError(error_msg)
    
    # -----------------------
    # Start job
    # -----------------------
    def start_diarization(self, media_id: str, params: Optional[DiarizationParams] = None) -> Optional[str]:
        """
        Start diarization job with pyannote.ai API.

        Args:
            media_id: The media ID from upload_audio
            params: Optional parameters for diarization

        Returns:
            Optional[str]: The job ID if started successfully, None otherwise
        """
        try:
            return self._send_payload(media_id, params)
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except ValueError as e:
            logger.error(f"Invalid API response: {e}")
            return None

    def _send_payload(self, media_id, params):
        payload: Dict[str, Any] = {"url": media_id}
        if params:
            payload |= params.to_api_dict()
            logger.info(f"Starting diarization with params: {params}")
        logger.debug(f"Full payload: {payload}")

        response = requests.post(self.config.diarize_endpoint, headers=self.headers, json=payload)
        job_id = self._extract_response_info(
            response, JOB_ID_FIELD, "API response missing job ID"
        )
        logger.info(f"Diarization job {job_id} started successfully")
        return job_id

    # -----------------------
    # Status / Polling
    # -----------------------
    def check_job_status(self, job_id: str) -> Optional[JobStatusResponse]:
        """
        Check the status of a diarization job.

        Returns a typed transport model (JobStatusResponse) or None on failure.
        """
        return self._check_status_with_retry(job_id)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(exp_base=2, initial=1, max=10),
        retry=retry_if_exception_type(
            (requests.RequestException, requests.Timeout, requests.ConnectionError)
            ),
    )
    def _check_status_with_retry(self, job_id: str) -> Optional[JobStatusResponse]:
        """
        Check job status with network error retry logic.

        Retries network failures without killing the polling loop.
        Fails fast on API errors (auth, malformed response, etc.).
        
        Used as the status function in the JobPoller helper class.
        """
        try:
            endpoint = f"{self.config.job_status_endpoint}/{job_id}"
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            result = response.json()

            try:
                jsr = JobStatusResponse.model_validate(result)
            except Exception as ve:
                logger.error(f"Invalid status response for job {job_id}: {result} ({ve})")
                return None

            return jsr

        except requests.RequestException as e:
            logger.warning(f"Status check network error for job {job_id}: {e}")
            raise  # Let tenacity retry
        except Exception as e:
            logger.error(f"Unexpected status check error for job {job_id}: {e}")
            return None  # Don't retry on unexpected errors

    class JobPoller:
        """
        Generic job polling helper for long-running async jobs.
        """

        def __init__(self, status_fn, job_id: str, polling_config: PollingConfig):
            self.status_fn = status_fn
            self.job_id = job_id
            self.polling_config = polling_config
            self.poll_count = 0
            self.start_time = time.time()
            self.last_status: Optional[JobStatusResponse] = None
            self._last_error_reason: Optional[str] = None

        def _poll(self) -> JobStatusResponse | _PollSignal | None:
            self.poll_count += 1
            try:
                status_response = self.status_fn(self.job_id)
            except RetryError as e:
                self._last_error_reason = f"status check retry exhausted: {e}"
                logger.error(f"Status check retries exhausted for job {self.job_id}: {e}")
                return _PollSignal.STATUS_RETRY_EXHAUSTED

            if status_response is None:
                logger.error(f"Failed to get status for job {self.job_id} after retries")
                self._last_error_reason = "status response None"
                return None

            # track last known status for timeout / errors
            self.last_status = status_response

            status = status_response.status
            elapsed = time.time() - self.start_time

            if status == JobStatus.SUCCEEDED:
                logger.info(
                    f"Job {self.job_id} completed successfully after {elapsed:.1f}s ({self.poll_count} polls)"
                )
                return status_response

            if status == JobStatus.FAILED:
                logger.error(f"Job {self.job_id} failed: {status_response.server_error_msg}")
                return status_response

            # Job still running - calculate next poll interval
            logger.info(f"Job {self.job_id} status: {status} (elapsed: {elapsed:.1f}s)")
            return _PollSignal.CONTINUE

        # --- Internal builders to attach polling context and craft JSRs ---
        def _attach_context(
            self, 
            base: Optional[JobStatusResponse], 
            *, 
            outcome: PollOutcome, 
            elapsed: float, 
            msg: Optional[str] = None
            ) -> JobStatusResponse:
            """Return a JSR carrying outcome + poll context. If `base` exists, preserve its
            status/payload/server_error_msg unless `msg` overrides it. Otherwise, synthesize a minimal JSR."""
            if base is None:
                return JobStatusResponse(
                    job_id=self.job_id,
                    outcome=outcome,
                    status=None,
                    server_error_msg=msg,
                    payload=None,
                    polls=self.poll_count,
                    elapsed_s=elapsed,
                )
            return JobStatusResponse(
                job_id=self.job_id,
                outcome=outcome,
                status=base.status,
                server_error_msg=msg if msg is not None else base.server_error_msg,
                payload=base.payload,
                polls=self.poll_count,
                elapsed_s=elapsed,
            )

        def _on_terminal(self, jsr: JobStatusResponse, *, elapsed: float) -> JobStatusResponse:
            """Attach poll context to a terminal server response (SUCCEEDED/FAILED)."""
            return JobStatusResponse(
                job_id=self.job_id,
                outcome=PollOutcome.SUCCEEDED if jsr.status == JobStatus.SUCCEEDED else PollOutcome.FAILED,
                status=jsr.status,
                server_error_msg=jsr.server_error_msg,
                payload=jsr.payload,
                polls=self.poll_count,
                elapsed_s=elapsed,
            )

        def _on_status_retry_exhausted(self, *, elapsed: float) -> JobStatusResponse:
            return self._attach_context(
                self.last_status, 
                outcome=PollOutcome.NETWORK_ERROR, 
                elapsed=elapsed, 
                msg=self._last_error_reason
                )

        def _on_invalid_payload(self, *, elapsed: float) -> JobStatusResponse:
            return self._attach_context(
                self.last_status, 
                outcome=PollOutcome.ERROR, 
                elapsed=elapsed, 
                msg="invalid status payload"
                )

        def _on_timeout(self, err: RetryError, *, elapsed: float) -> JobStatusResponse:
            return self._attach_context(
                self.last_status, 
                outcome=PollOutcome.TIMEOUT, 
                elapsed=elapsed, 
                msg=str(err)
                )

        def _on_interrupt(self, *, elapsed: float) -> JobStatusResponse:
            return self._attach_context(
                self.last_status, 
                outcome=PollOutcome.INTERRUPTED, 
                elapsed=elapsed, 
                msg="KeyboardInterrupt"
                )

        def _on_exception(self, err: Exception, *, elapsed: float) -> JobStatusResponse:
            return self._attach_context(
                self.last_status, 
                outcome=PollOutcome.ERROR, 
                elapsed=elapsed, 
                msg=str(err)
                )

        def run(self) -> JobStatusResponse:
            try:
                result = self._setup_and_run_poll()
                elapsed = time.time() - self.start_time

                if isinstance(result, JobStatusResponse):
                    # Terminal SUCCEEDED/FAILED (or unexpected non-terminal delivered): attach context
                    return self._on_terminal(result, elapsed=elapsed)

                if result is _PollSignal.STATUS_RETRY_EXHAUSTED:
                    return self._on_status_retry_exhausted(elapsed=elapsed)

                # None indicates invalid status payload or unexpected branch
                return self._on_invalid_payload(elapsed=elapsed)

            except RetryError as e:
                # Outer polling timeout
                elapsed = time.time() - self.start_time
                logger.info(f"Polling timed out for job {self.job_id} after {elapsed:.1f}s")
                return self._on_timeout(e, elapsed=elapsed)
            except KeyboardInterrupt:
                elapsed = time.time() - self.start_time
                logger.info(f"Polling for job {self.job_id} interrupted by user. Exiting.")
                return self._on_interrupt(elapsed=elapsed)
            except Exception as e:
                elapsed = time.time() - self.start_time
                logger.error(f"Polling failed for job {self.job_id}: {e}")
                return self._on_exception(e, elapsed=elapsed)

        def _setup_and_run_poll(self) -> Optional[JobStatusResponse | _PollSignal]:
            cfg = self.polling_config
            stop_policy = stop_never if cfg.polling_timeout is None else stop_after_delay(cfg.polling_timeout)
            retrying = Retrying(
                retry=retry_if_result(lambda result: result is _PollSignal.CONTINUE),
                stop=stop_policy,
                wait=wait_exponential_jitter(
                    exp_base=cfg.exp_base,
                    initial=cfg.initial_poll_time,
                    max=cfg.max_interval,
                ),
                reraise=True,
            )
            result = retrying(self._poll)
            if isinstance(result, JobStatusResponse):
                return result
            # could be STATUS_RETRY_EXHAUSTED sentinel or None
            logger.info(f"Polling ended with result: {result}")
            return result

    def poll_job_until_complete(
        self,
        job_id: str,
        estimated_duration: Optional[float] = None,
        timeout: Optional[float] = None,
        wait_until_complete: Optional[bool] = False,
    ) -> JobStatusResponse:
        """
        Poll until the job reaches a terminal state or a client-side stop condition, and
        return a unified JobStatusResponse (JSR) that includes both the server payload
        and polling context via `outcome`, `polls`, and `elapsed_s`.

        Args:
            job_id: Remote job identifier to poll.
            estimated_duration: Optional hint; currently unused (reserved for adaptive backoff).
            timeout: Optional hard timeout in seconds for this poll call. If provided, it overrides
                     the client's default polling timeout. Ignored if `wait_until_complete` is True.
            wait_until_complete: If True, ignore timeout and poll indefinitely (subject to process lifetime).

        Returns:
            JobStatusResponse: unified transport + polling-context result.
        """
        if timeout is not None and wait_until_complete:
            raise ConfigurationError("Timeout cannot be set with wait_until_complete")

        # Derive an effective timeout for this call, without mutating client defaults
        effective_timeout = None if wait_until_complete else (
            timeout if timeout is not None else self.polling_config.polling_timeout
            )

        cfg = PollingConfig(
            polling_timeout=effective_timeout,
            initial_poll_time=self.polling_config.initial_poll_time,
            exp_base=self.polling_config.exp_base,
            max_interval=self.polling_config.max_interval,
        )

        poller = self.JobPoller(
            status_fn=self._check_status_with_retry,
            job_id=job_id,
            polling_config=cfg,
        )
        return poller.run()
    
    