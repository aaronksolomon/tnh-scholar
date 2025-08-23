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


import os
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Union

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field
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

# Load environment variables
load_dotenv()

# Logger placeholder - will be replaced by your logger setup
logger = get_child_logger(__name__)

class APIKeyError(Exception):
    """Raised when API key is missing or invalid."""
    pass


# Response Fields 
JOB_ID_FIELD = "jobId"
STATUS_FIELD = "status"
ERROR_FIELD = "error"
OUTPUT_FIELD = "output"
DIARIZATION_FIELD = "diarization"


class JobStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PENDING = "pending"
    RUNNING = "running"


class DiarizationParams(BaseModel):
    """Parameters for diarization job configuration."""
    num_speakers: Optional[Union[int, str]] = Field(
        None, 
        description="Number of speakers (int) or 'auto' for automatic detection"
    )
    confidence: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0, 
        description="Confidence threshold for speaker segments"
    )
    webhook: Optional[str] = None

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert to API payload format."""
        payload = {}

        if self.num_speakers is not None:
            payload["numSpeakers"] = self.num_speakers
        
        if self.confidence is not None:
            payload["confidence"] = self.confidence

        if self.webhook:
            payload["webhook"] = self.webhook

        return payload


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
    
    def _create_media_id(self) -> str:
        """Generate a unique media ID."""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
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
                    headers={"Content-Type": self.config.media_content_type}
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
        retry=retry_if_exception_type((
            requests.RequestException, 
            requests.Timeout,
            requests.ConnectionError
        ))
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
            upload_url = self._get_upload_url_with_retry(media_id)
            if not upload_url:
                return None

            # Upload file (this is slow, use extended timeout)
            if self._upload_file_with_retry(file_path, upload_url):
                logger.info(f"Upload completed successfully: {media_id}")
                return media_id
            else:
                logger.error(f"Upload failed for {file_path.name}")
                return None

        except Exception as e:
            # Log but don't retry - let tenacity handle retries
            logger.error(f"Upload attempt failed: {e}")
            raise  # Re-raise for tenacity to handle
        
    def _get_upload_url_with_retry(self, media_id: str) -> Optional[str]:
        """Get upload URL - separate from file upload for cleaner retry logic."""
        try:
            return self._data_upload_url(media_id)
        except requests.RequestException as e:
            logger.error(f"Failed to get upload URL: {e}")
            raise  # Let tenacity retry this
        except ValueError as e:
            logger.error(f"Invalid API response: {e}")
            return None  # Don't retry on API response issues

    def _data_upload_url(self, media_id):
        response = requests.post(
            self.config.media_input_endpoint,
            headers=self.headers,
            json={"url": media_id},
            timeout=self.config.network_timeout  # Use normal timeout
        )

        response.raise_for_status()
        upload_info = response.json()

        upload_url = upload_info.get("url")
        if not upload_url:
            raise ValueError("No upload URL in API response")

        logger.debug(f"Got upload URL for media ID: {media_id}")
        return upload_url

    def _upload_file_with_retry(self, file_path: Path, upload_url: str) -> bool:
        """Upload file with extended timeout and progress tracking."""
        try:
            return self._file_open_and_upload(file_path, upload_url)
        except requests.Timeout as e:
            logger.warning(f"Upload timeout for {file_path.name} (will retry): {e}")
            raise  # Let tenacity retry
        except requests.RequestException as e:
            logger.error(f"Upload request failed for {file_path.name}: {e}")
            raise  # Let tenacity retry
        except Exception as e:
            logger.error(f"Unexpected upload error: {e}")
            return False  # Don't retry on unexpected errors

    def _file_open_and_upload(self, file_path, upload_url):
        file_size = file_path.stat().st_size
        logger.info(f"Uploading {file_path.name} ({file_size / 1024 / 1024:.1f}MB)...")

        with open(file_path, "rb") as file_data:
            upload_response = requests.put(
                upload_url,
                data=file_data,
                headers={"Content-Type": self.config.media_content_type},
                timeout=self.upload_timeout  # Extended timeout for uploads
            )

        upload_response.raise_for_status()
        logger.info(f"File upload completed: {file_path.name}")
        return True
    
    def start_diarization(
        self, 
        media_id: str, 
        params: Optional[DiarizationParams] = None
    ) -> Optional[str]:
        """
        Start diarization job with pyannote.ai API.
        
        Uses Diarization parameters if specified
        
        Args:
            DiarizationParams: Optional parameters for diarization
            media_id: The media ID from upload_audio
            
        Returns:
            Optional[str]: The job ID if started successfully, None otherwise
        """
        try:
            return self._send_payload_for_diarization(media_id, params)
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None
        except ValueError as e:
            logger.error(f"Invalid API response: {e}")
            return None

    def _send_payload_for_diarization(self, media_id, params):
        payload = {"url": media_id}

        if params:
            payload |= params.to_api_dict()
            logger.info(f"Starting diarization with params: {params}")
        
        logger.debug(f"Full payload: {payload}")

        response = requests.post(
            self.config.diarize_endpoint,
            headers=self.headers,
            json=payload
        )

        response.raise_for_status()
        job_info = response.json()

        # Validate response structure
        if not (job_id := job_info.get(JOB_ID_FIELD)):
            raise ValueError("API response missing job ID")

        logger.info(f"Diarization job {job_id} started successfully")
        return job_id
        

    def check_job_status(self, job_id: str) -> Optional[Dict]:
        """
        Check the status of a diarization job.
        
        Args:
            job_id: The job ID to check
            
        Returns:
            Optional[Dict]: The job status response or None if request failed
        """
        return self._check_status_with_retry(job_id)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(exp_base=2, initial=1, max=10),
        retry=retry_if_exception_type((
            requests.RequestException, 
            requests.Timeout,
            requests.ConnectionError
        ))
    )
    
    def _check_status_with_retry(self, job_id: str) -> Optional[Dict]:
        """
        Check job status with network error retry logic.
        
        Retries network failures without killing the polling loop.
        Fails fast on API errors (auth, malformed response, etc.).
        """
        try:
            endpoint = f"{self.config.job_status_endpoint}/{job_id}"
            response = requests.get(endpoint, headers=self.headers)
            
            response.raise_for_status()
            result = response.json()
            
            # Validate response structure
            if STATUS_FIELD not in result:
                logger.error(f"Invalid status response for job {job_id}: {result}")
                return None
                
            return result
            
        except requests.RequestException as e:
            logger.warning(f"Status check network error for job {job_id}: {e}")
            raise  # Let tenacity retry
        except Exception as e:
            logger.error(f"Unexpected status check error for job {job_id}: {e}")
            return None  # Don't retry on unexpected errors
    
    class JobPoller:
        """
        Generic job polling helper for long-running async jobs.

        Args:
            status_fn: Callable that returns job status dict.
            job_id: The job ID to poll.
            timeout: Max seconds to wait (None = forever).
            initial_wait: Initial wait for exponential backoff.
            logger: Logger instance (optional, defaults to client's logger).
        """
        def __init__(
            self,
            status_fn,
            job_id: str,
            polling_config: PollingConfig,
        ):
            self.status_fn = status_fn
            self.job_id = job_id
            self.polling_config = polling_config
            self.poll_count = 0
            self.start_time = time.time()


        def _poll(self):
            self.poll_count += 1
            status_response = self.status_fn(self.job_id)
            if not status_response:
                logger.error(f"Failed to get status for job {self.job_id} after retries")
                return None

            status = status_response.get(STATUS_FIELD)
            elapsed = time.time() - self.start_time

            if status == JobStatus.SUCCEEDED:
                logger.info(
                        f"Job {self.job_id} completed successfully after "
                        "{elapsed:.1f}s ({self.poll_count} polls)"
                    )
                return status_response

            if status == JobStatus.FAILED:
                error = status_response.get(ERROR_FIELD, "Unknown error")
                logger.error(f"Job {self.job_id} failed: {error}")
                return status_response

            # Job still running - calculate next poll interval
            logger.info(
                f"Job {self.job_id} status: {status} (elapsed: {elapsed:.1f}s) "
            )
            return "POLLING"
        
        def run(self):
            try:
                return self._setup_and_run_poll()
            except RetryError:
                elapsed = time.time() - self.start_time
                logger.info(f"Polling timed out for job {self.job_id} after {elapsed:.1f}s")
                return None
            except KeyboardInterrupt:
                logger.info(f"Polling for job {self.job_id} interrupted by user. Exiting.")
                return None
            except Exception as e:
                logger.error(f"Polling failed for job {self.job_id}: {e}")
                return None
            
        def _setup_and_run_poll(self):
            cfg = self.polling_config
            # Determine stop policy (None => wait indefinitely)
            stop_policy = stop_never if cfg.polling_timeout is None else (
                    stop_after_delay(cfg.polling_timeout)
                )
            retrying = Retrying(
                retry=retry_if_result(lambda result: result == "POLLING"),
                stop=stop_policy,
                wait=wait_exponential_jitter(
                    exp_base=cfg.exp_base,
                    initial=cfg.initial_poll_time,
                    max=cfg.max_interval
                ),
                reraise=True
            )
            result = retrying(self._poll)
            if isinstance(result, dict):
                return result
            logger.info(f"Polling ended with result: {result}")
            return None

    def poll_job_until_complete(
        self, 
        job_id: str,
        estimated_duration: Optional[float] = None,
        timeout: Optional[float] = None,
        wait_until_complete: Optional[bool] = False,
    ) -> Optional[Dict]:
        """
        Main entrypoint for PyannoteClient
        Poll job until completion using JobPoller helper class.

        Args:
            job_id: The job ID to poll
            estimated_duration: Future hook for duration-based polling optimization
            timeout: Optional override for the polling timeout in seconds. 
                     If not provided, uses self.polling_timeout.
            wait_until_complete: Optional override of polling timeout. Wait indefinitely.

        Returns:
            Final job status or None if polling failed/timed out
        """
        if timeout and wait_until_complete:
            raise ConfigurationError("Timeout cannot be set with wait_until_complete")
            
        if wait_until_complete:
            timeout = None
        else:
            timeout = timeout or self.polling_config.polling_timeout
                        
        timeout_str = "∞" if timeout is None else f"{timeout}s"
        logger.info(
            f"Polling job {job_id} until completion (timeout: {timeout_str})"
        )

        if estimated_duration:
            logger.debug(f"Estimated duration: {estimated_duration}s (not yet used for polling optimization)")

        poller = self.JobPoller(
            status_fn=self._check_status_with_retry,
            job_id=job_id,
            polling_config=self.polling_config
        )
        return poller.run()