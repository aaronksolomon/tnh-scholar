#TODO move this file (also all related diarization modules) 
# into the audio_processing folder

import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import requests
from dotenv import load_dotenv

from tnh_scholar.logging_config import get_child_logger

# Load environment variables
load_dotenv()

# Logger placeholder - will be replaced by your logger setup
logger = get_child_logger(__name__)

# Pyannote AI API Configuration
class PyannoteConfig:
    """Configuration constants for Pyannote API."""
    
    # API Endpoints
    BASE_URL = "https://api.pyannote.ai/v1"
    MEDIA_INPUT_ENDPOINT = f"{BASE_URL}/media/input"
    DIARIZE_ENDPOINT = f"{BASE_URL}/diarize"
    JOB_STATUS_ENDPOINT = f"{BASE_URL}/jobs"
    
    # Response Fields
    JOB_ID_FIELD = "jobId"
    STATUS_FIELD = "status"
    ERROR_FIELD = "error"
    OUTPUT_FIELD = "output"
    DIARIZATION_FIELD = "diarization"
    
    # Values
    SUCCESS_STATUS = "succeeded"
    FAILED_STATUS = "failed"
    PENDING_STATUS = "pending"
    RUNNING_STATUS = "running"
    
    # Parameters
    POLLING_INTERVAL = 15  # seconds
    POLLING_TIMEOUT = 180  # seconds (2 minutes)
    
    # Media
    MEDIA_PREFIX = "media://diarization-"
    MEDIA_CONTENT_TYPE = "audio/mpeg"


class APIKeyError(Exception):
    """Raised when API key is missing or invalid."""
    pass


class PyannoteClient:
    """Client for interacting with the pyannote.ai speaker diarization API."""
    
    def __init__(self, api_key: Optional[str] = None):
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
            
        self.polling_interval = PyannoteConfig.POLLING_INTERVAL
        self.polling_timeout = PyannoteConfig.POLLING_TIMEOUT
        
        self.headers = {"Authorization": f"Bearer {self.api_key}"}
    
    def _create_media_id(self) -> str:
        """Generate a unique media ID."""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{PyannoteConfig.MEDIA_PREFIX}{timestamp}"
    
    def _get_upload_url(self, media_id: str) -> Optional[str]:
        """
        Get URL for uploading media to pyannote.ai.
        
        Args:
            media_id: The media ID to use
            
        Returns:
            Optional[str]: Upload URL or None if request failed
        """
        try:
            response = requests.post(
                PyannoteConfig.MEDIA_INPUT_ENDPOINT,
                headers=self.headers,
                json={"url": media_id}
            )
            
            response.raise_for_status()
            upload_info = response.json()
            logger.info(f"Temporary media ID created: {media_id}")
            return upload_info.get("url")
            
        except requests.RequestException as e:
            logger.error(f"Failed to get upload URL: {e}")
            return None
    
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
                    headers={"Content-Type": PyannoteConfig.MEDIA_CONTENT_TYPE}
                )
            
            upload_response.raise_for_status()
            logger.info("File uploaded successfully")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to upload file: {e}")
            return False
    
    def upload_audio(self, file_path: Path) -> Optional[str]:
        """
        Upload audio file to pyannote temporary storage.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Optional[str]: The media ID if upload succeeded, None otherwise
        """
        if not file_path.exists():
            logger.error(f"Audio file not found: {file_path}")
            return None

        # Create media ID
        media_id = self._create_media_id()

        if upload_url := self._get_upload_url(media_id):
            return media_id if self._upload_file(file_path, upload_url) else None
        else:
            return None
    
    def start_diarization(self, media_id: str) -> Optional[str]:
        """
        Start diarization job with pyannote.ai API.
        
        Args:
            media_id: The media ID from upload_audio
            
        Returns:
            Optional[str]: The job ID if started successfully, None otherwise
        """
        try:
            logger.info(f"Starting diarization job for {media_id}")
            
            response = requests.post(
                PyannoteConfig.DIARIZE_ENDPOINT,
                headers=self.headers,
                json={"url": media_id}
            )
            
            response.raise_for_status()
            job_info = response.json()
            job_id = job_info.get(PyannoteConfig.JOB_ID_FIELD)
            
            if not job_id:
                logger.error("No job ID in response")
                return None
                
            logger.info(f"Diarization job started with ID: {job_id}")
            logger.info(
                "Initial status: "
                f"{job_info.get(PyannoteConfig.STATUS_FIELD, 'unknown')}")
            
            return job_id
            
        except requests.RequestException as e:
            logger.error(f"Failed to start diarization job: {e}")
            return None
    
    def check_job_status(self, job_id: str) -> Optional[Dict]:
        """
        Check the status of a diarization job.
        
        Args:
            job_id: The job ID to check
            
        Returns:
            Optional[Dict]: The job status response or None if request failed
        """
        try:
            endpoint = f"{PyannoteConfig.JOB_STATUS_ENDPOINT}/{job_id}"
            response = requests.get(endpoint, headers=self.headers)
            
            response.raise_for_status()
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Failed to check job status: {e}")
            return None
    
    def poll_job_until_complete(
        self, 
        job_id: str, 
    ) -> Optional[Dict]:
        """
        Poll a job until it completes or fails.
        
        Args:
            job_id: The job ID to poll
            interval: Seconds between polling attempts
            timeout: Maximum seconds to wait
            
        Returns:
            Optional[Dict]: Final job status or None if polling failed/timed out
        """
        logger.info(
            f"Polling job {job_id} until completion (timeout: {self.polling_timeout}s)"
            )
        
        start_time = time.time()
        elapsed = 0
        
        while elapsed < self.polling_timeout:
            status_response = self.check_job_status(job_id)
            
            if not status_response:
                logger.error("Failed to get job status")
                return None
                
            status = status_response.get(PyannoteConfig.STATUS_FIELD)
            
            if status == PyannoteConfig.SUCCESS_STATUS:
                logger.info(f"Job {job_id} completed successfully")
                return status_response
                
            if status == PyannoteConfig.FAILED_STATUS:
                error = status_response.get(PyannoteConfig.ERROR_FIELD, "Unknown error")
                logger.error(f"Job {job_id} failed: {error}")
                return status_response
                
            # Job is still running, wait and try again
            logger.info(
                f"Job {job_id} status: {status}, "
                f"polling again in {self.polling_interval}s")
            time.sleep(self.polling_interval)
            
            elapsed = time.time() - start_time
        
        logger.error(f"Polling timed out after {self.polling_timeout}s")
        return None