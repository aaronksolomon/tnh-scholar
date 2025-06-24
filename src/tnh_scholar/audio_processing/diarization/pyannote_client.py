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
from pydantic_settings import BaseSettings
from tenacity import (
    RetryError,
    Retrying,
    retry,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential_jitter,
)

from tnh_scholar.logging_config import get_child_logger

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

    
# Pyannote AI API Configuration
class PyannoteConfig(BaseSettings):
    """Configuration constants for Pyannote API."""

    # API Endpoints
    base_url: str = "https://api.pyannote.ai/v1"

    @property
    def media_input_endpoint(self) -> str:
        return f"{self.base_url}/media/input"

    @property
    def diarize_endpoint(self) -> str:
        return f"{self.base_url}/diarize"

    @property
    def job_status_endpoint(self) -> str:
        return f"{self.base_url}/jobs"

    # Parameters
    polling_interval: int = 15  # Polling interval in seconds
    polling_timeout: int = 180  # Polling timeout in seconds
    initial_poll_time: int = 7 # First polling time in seconds (for short files)

    # Media
    media_prefix: str = "media://diarization-"
    media_content_type: str = "audio/mpeg"
    
    # Upload-specific settings
    upload_timeout: int = 300  # 5 minutes for large files
    upload_max_retries: int = 3
    
    # Network specific settings
    network_timeout: int = 3 # seconds
    class Config:
        env_file = ".env"
        case_sensitive = False
        env_prefix = "PYANNOTE_"

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
        self.polling_interval = self.config.polling_interval
        self.polling_timeout = self.config.polling_timeout
        self.initial_poll_time = self.config.initial_poll_time
        
        # Upload-specific timeouts (longer than general calls)
        self.upload_timeout = self.config.upload_timeout  # 5 minutes for large files
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
        if not file_path.exists() or not file_path.is_file():
            logger.error(f"Audio file not found or is not a file: {file_path}")
            return None

        file_size_mb = file_path.stat().st_size / (1024 * 1024)
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
        def __init__(self, client, job_id: str, timeout: float, logger):
            self.client = client
            self.job_id = job_id
            self.timeout = timeout
            self.logger = logger
            self.poll_count = 0
            self.start_time = time.time()

        def _poll(self):
            self.poll_count += 1
            status_response = self.client._check_status_with_retry(self.job_id)
            if not status_response:
                self.logger.error(f"Failed to get status for job {self.job_id} after retries")
                return None

            status = status_response.get(STATUS_FIELD)
            elapsed = time.time() - self.start_time

            if status == JobStatus.SUCCEEDED:
                self.logger.info(
                    f"Job {self.job_id} completed successfully after {elapsed:.1f}s ({self.poll_count} polls)"
                )
                return status_response

            if status == JobStatus.FAILED:
                error = status_response.get(ERROR_FIELD, "Unknown error")
                self.logger.error(f"Job {self.job_id} failed: {error}")
                return status_response

            # Job still running - calculate next poll interval
            self.logger.info(
                f"Job {self.job_id} status: {status} (elapsed: {elapsed:.1f}s) "
            )
            return "POLLING"
        
        # Not used
        # @staticmethod
        # def _polling_stop_condition(retry_state) -> bool:
        #     """Stop polling if elapsed time exceeds timeout."""
        #     self_instance = retry_state.args[0]
        #     return time.time() - self_instance.start_time > self_instance.timeout

        def run(self):
            try:
                retrying = Retrying(
                    retry=retry_if_result(lambda result: result == "POLLING"),
                    stop=stop_after_delay(self.timeout),
                    wait=wait_exponential_jitter(exp_base=2, initial=4, max=30),
                    reraise=True
                )
                result = retrying(self._poll)
                if isinstance(result, dict):
                    return result
                self.logger.info(f"Polling ended with result: {result}")
                return None
            except RetryError:
                elapsed = time.time() - self.start_time
                self.logger.info(f"Polling timed out for job {self.job_id} after {elapsed:.1f}s")
                return None
            except KeyboardInterrupt:
                self.logger.info(f"Polling for job {self.job_id} interrupted by user. Exiting.")
                return None
            except Exception as e:
                self.logger.error(f"Polling failed for job {self.job_id}: {e}")
                return None

    def poll_job_until_complete(
        self, 
        job_id: str,
        estimated_duration: Optional[float] = None
    ) -> Optional[Dict]:
        """
        Poll job until completion using JobPoller helper class.

        Args:
            job_id: The job ID to poll
            estimated_duration: Future hook for duration-based polling optimization

        Returns:
            Final job status or None if polling failed/timed out
        """
        logger.info(
            f"Polling job {job_id} until completion (timeout: {self.polling_timeout}s)"
        )

        if estimated_duration:
            logger.debug(f"Estimated duration: {estimated_duration}s (not yet used for polling optimization)")

        poller = self.JobPoller(
            client=self,
            job_id=job_id,
            timeout=self.polling_timeout,
            logger=logger,
        )
        return poller.run()

    # Currently not used. Here for reference
    # def _calculate_poll_interval(self, poll_count: int) -> float:
    #     """
    #     Calculate next polling interval with progressive backoff and jitter.
        
    #     Progressive intervals: initial_poll_time -> 2x -> 3x -> 4x -> max 30s
    #     With ±20% jitter to avoid API clustering.
    #     """
    #     base_interval = self.initial_poll_time

    #     # Progressive backoff: 1x, 2x, 3x, 4x, then cap at 30s
    #     if poll_count <= 1:
    #         interval = base_interval
    #     elif poll_count <= 4:
    #         interval = base_interval * poll_count
    #     else:
    #         interval = min(30, base_interval * 4)

    #     # Add ±20% jitter
    #     jitter = interval * 0.2 * (random.random() * 2 - 1)  # ±20%
    #     return max(1.0, interval + jitter)