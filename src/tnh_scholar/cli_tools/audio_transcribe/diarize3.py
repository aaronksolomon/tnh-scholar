import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydub import AudioSegment

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils.file_utils import write_str_to_file

# Load environment variables
load_dotenv()

# Logger placeholder - will be replaced by your logger setup
logger = get_child_logger(__name__)

# Configuration
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
    DEFAULT_POLLING_INTERVAL = 15  # seconds
    DEFAULT_POLLING_TIMEOUT = 180  # seconds (2 minutes)
    
    # Media
    MEDIA_PREFIX = "media://diarization-"
    MEDIA_CONTENT_TYPE = "audio/mpeg"


class ProcessingConfig:
    """Configuration for audio processing."""
    
    # Progress reporting
    PROGRESS_INTERVAL = 10  # report every N segments
    
    # Segment file naming
    DEFAULT_FILENAME_TEMPLATE = "{speaker}_{start_ms}_{end_ms}.mp3"
    

class APIKeyError(Exception):
    """Raised when API key is missing or invalid."""
    pass


class AudioSegmentInfo(BaseModel):
    """Pydantic model for speaker segment information."""
    
    speaker: str = Field(..., description="Speaker identifier")
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    duration: float = Field(..., description="Duration in seconds")
    filename: str = Field(..., description="Path to the audio file")
    
    def export(self, format: str = "json", pretty: bool = True) -> str:
        """
        Export segment information to the specified format.
        
        Args:
            format: Output format ("json" for now)
            pretty: Whether to use pretty-printing (indentation)
            
        Returns:
            Formatted string representation of the segment info
        """
        if format.lower() == "json":
            return self.model_dump_json(indent=2 if pretty else None)
        else:
            raise ValueError(f"Unsupported export format: {format}")
            
    def save_to_file(
        self, 
        file_path: Path, 
        format: str = "json", 
        pretty: bool = True
        ) -> None:
        """
        Save segment information to a file.
        
        Args:
            file_path: Path where to save the information
            format: Output format ("json" for now)
            pretty: Whether to use pretty-printing (indentation)
        """
        content = self.export(format, pretty)
        write_str_to_file(file_path, content)
        logger.debug(f"Segment info saved to {file_path}")
           
    @property
    def start_ms(self) -> int:
        """Get start time in milliseconds."""
        return int(self.start * 1000)
    
    @property
    def end_ms(self) -> int:
        """Get end time in milliseconds."""
        return int(self.end * 1000)


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
        interval: int = PyannoteConfig.DEFAULT_POLLING_INTERVAL, 
        timeout: int = PyannoteConfig.DEFAULT_POLLING_TIMEOUT
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
        logger.info(f"Polling job {job_id} until completion (timeout: {timeout}s)")
        
        start_time = time.time()
        elapsed = 0
        
        while elapsed < timeout:
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
            logger.info(f"Job {job_id} status: {status}, polling again in {interval}s")
            time.sleep(interval)
            
            elapsed = time.time() - start_time
        
        logger.error(f"Polling timed out after {timeout}s")
        return None


class DiarizationProcessor:
    """Process audio files for speaker diarization using pyannote.ai."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize diarization processor.
        
        Args:
            api_key: Pyannote.ai API key (defaults to environment variable)
        """
        self.pyannote = PyannoteClient(api_key)
    
    def _extract_diarization_segments(self, results: Dict) -> Optional[List[Dict]]:
        """
        Extract diarization segments from API response.
        
        Args:
            results: The diarization results from the API
            
        Returns:
            Optional[List[Dict]]: Extracted segments or None if not found/invalid
        """
        # Check job status
        if results.get(PyannoteConfig.STATUS_FIELD) != PyannoteConfig.SUCCESS_STATUS:
            error = results.get(PyannoteConfig.ERROR_FIELD, "No error details provided")
            logger.error(
                f"Job failed with status: {results.get(PyannoteConfig.STATUS_FIELD)}"
                )
            logger.error(f"Error details: {error}")
            return None
        
        # Get diarization segments
        output = results.get(PyannoteConfig.OUTPUT_FIELD, {})
        segments = output.get(PyannoteConfig.DIARIZATION_FIELD, [])
        
        if not segments:
            logger.error("No diarization segments found in results")
            return None
        
        logger.info(f"Found {len(segments)} diarization segments")
        return segments
    
    def _create_segment_info(
        self, 
        segment: Dict, 
        output_dir: Path,
        filename_template: Optional[str] = None
    ) -> AudioSegmentInfo:
        """
        Create metadata for a single audio segment.
        
        Args:
            segment: Raw segment data from API
            output_dir: Directory for output files
            filename_template: Optional template for filename format
            
        Returns:
            AudioSegmentInfo: Structured segment metadata
        """
        start_seconds = segment["start"]
        end_seconds = segment["end"]
        speaker = segment["speaker"]
        duration = end_seconds - start_seconds
        
        # Calculate values for filename
        start_ms = int(start_seconds * 1000)
        end_ms = int(end_seconds * 1000)
        
        # Create segment filename using template
        template = filename_template or ProcessingConfig.DEFAULT_FILENAME_TEMPLATE
        filename_str = template.format(
            speaker=speaker, 
            start_ms=start_ms, 
            end_ms=end_ms,
            start=start_seconds,
            end=end_seconds
        )
        filename = output_dir / filename_str
        
        return AudioSegmentInfo(
            speaker=speaker,
            start=start_seconds,
            end=end_seconds,
            duration=duration,
            filename=str(filename)
        )
    
    def _save_segment_metadata(
        self, 
        segments: List[AudioSegmentInfo], 
        output_dir: Path
    ) -> Path:
        """
        Save segment metadata to JSON file.
        
        Args:
            segments: List of segment metadata
            output_dir: Directory to save file in
            
        Returns:
            Path: Path to the JSON file
        """
        segments_json = output_dir / "segments.json"
        
        # Convert to dictionaries for serialization
        segments_data = [segment.model_dump() for segment in segments]
        
        # Write to file using the utility function
        write_str_to_file(segments_json, json.dumps(segments_data, indent=2))
            
        logger.info(f"Segment info saved to {segments_json}")
        return segments_json
    
    def _extract_audio_segment(
        self,
        audio: AudioSegment,
        segment_info: AudioSegmentInfo
    ) -> None:
        """
        Extract a segment of audio and save it to a file.
        
        Args:
            audio: Full audio file
            segment_info: Information about the segment to extract
        """
        try:
            audio_segment = AudioSegment(
                audio[segment_info.start_ms:segment_info.end_ms]
                )
            audio_segment.export(segment_info.filename, format="mp3")
        except Exception as e:
            logger.error(f"Failed to extract audio segment: {e}")
    
    def _log_processing_progress(
        self,
        current_index: int,
        total_count: int
    ) -> None:
        """
        Log processing progress at appropriate intervals.
        
        Args:
            current_index: Current segment index (0-based)
            total_count: Total number of segments
        """
        # Convert to 1-based for logging
        segment_num = current_index + 1
        
        # Log at intervals or at the end
        if (segment_num % ProcessingConfig.PROGRESS_INTERVAL == 0 or 
            segment_num == total_count):
            logger.info(f"Processed {segment_num}/{total_count} segments")
    
    def _process_segment(
        self,
        segment: Dict,
        output_dir: Path,
        audio: Optional[AudioSegment] = None,
        filename_template: Optional[str] = None
    ) -> AudioSegmentInfo:
        """
        Process a single segment from diarization results.
        
        Args:
            segment: Raw segment data from API
            output_dir: Directory for output files
            audio: Optional full audio file for extraction
            filename_template: Optional template for filename
            
        Returns:
            AudioSegmentInfo: Processed segment information
        """
        # Create segment metadata
        segment_info = self._create_segment_info(
            segment, 
            output_dir,
            filename_template
        )
        
        # Extract audio if requested
        if audio is not None:
            self._extract_audio_segment(audio, segment_info)
            
        return segment_info
    
    def process_diarization_results(
        self, 
        results: Dict, 
        audio_path: Path, 
        output_dir: Path,
        extract_audio: bool = False,
        filename_template: Optional[str] = None
    ) -> List[AudioSegmentInfo]:
        """
        Process diarization results to create speaker segments.
        
        Args:
            results: The diarization results from the API
            audio_path: Path to the original audio file
            output_dir: Directory to save speaker segments
            extract_audio: Whether to extract audio segments
            filename_template: Optional template for segment filenames
            
        Returns:
            List[AudioSegmentInfo]: Information about the extracted segments
        """
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract segments from results
        segments = self._extract_diarization_segments(results)
        if not segments:
            return []
        
        # Load audio file if needed
        audio = AudioSegment.from_file(audio_path) if extract_audio else None
        speaker_segments = []
        
        # Process each segment
        for i, segment in enumerate(segments):
            # Process this segment
            segment_info = self._process_segment(
                segment, 
                output_dir,
                audio if extract_audio else None,
                filename_template
            )
            speaker_segments.append(segment_info)
            
            # Log progress
            self._log_processing_progress(i, len(segments))
        
        # Save the segment info as JSON
        self._save_segment_metadata(speaker_segments, output_dir)
        
        logger.info(f"Extracted {len(speaker_segments)} speaker segments")
        return speaker_segments
    
    def _upload_and_start_job(
        self, 
        audio_file_path: Path
    ) -> Optional[str]:
        """
        Upload audio and start diarization job.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Optional[str]: Job ID if successful, None otherwise
        """
        # Upload audio to pyannote
        media_id = self.pyannote.upload_audio(audio_file_path)
        if not media_id:
            logger.error("Failed to upload audio file")
            return None
            
        # Start diarization job
        job_id = self.pyannote.start_diarization(media_id)
        if not job_id:
            logger.error("Failed to start diarization job")
            return None
            
        return job_id
    
    def diarize(
        self, 
        audio_file_path: Path, 
        output_dir: Optional[Path] = None,
        extract_audio: bool = False,
        filename_template: Optional[str] = None,
        polling_interval: int = PyannoteConfig.DEFAULT_POLLING_INTERVAL,
        polling_timeout: int = PyannoteConfig.DEFAULT_POLLING_TIMEOUT
    ) -> Optional[List[AudioSegmentInfo]]:
        """
        Complete diarization process from audio file to speaker segments using polling.
        
        Args:
            audio_file_path: Path to the audio file
            output_dir: Directory to save speaker segments
            extract_audio: Whether to extract audio segments
            filename_template: Optional template for segment filenames
            polling_interval: Seconds between status checks
            polling_timeout: Maximum seconds to wait
            
        Returns:
            Optional[List[AudioSegmentInfo]]: 
                Information about the extracted segments or None if failed
        """
        try:
            # Validate and set up paths
            audio_file_path = Path(audio_file_path).resolve()
            if not audio_file_path.exists():
                logger.error(f"Audio file not found: {audio_file_path}")
                return None

            # Set default output directory if not provided
            if output_dir is None:
                output_dir = audio_file_path.parent / f"{audio_file_path.stem}_segments"
            else:
                output_dir = Path(output_dir).resolve()

            # Upload and start job
            job_id = self._upload_and_start_job(audio_file_path)
            if not job_id:
                return None

            # Get results via polling
            results = self.pyannote.poll_job_until_complete(
                job_id, 
                interval=polling_interval,
                timeout=polling_timeout
            )
            
            if not results:
                logger.error("Failed to get diarization results")
                return None

            # Process results
            return self.process_diarization_results(
                results, 
                audio_file_path, 
                output_dir,
                extract_audio,
                filename_template
            )
            
        except Exception as e:
            logger.error(f"Diarization failed: {e}")
            return None


def diarize(
    audio_file_path: Path, 
    output_dir: Optional[Path] = None,
    extract_audio: bool = False,
    filename_template: Optional[str] = None,
    polling_interval: int = PyannoteConfig.DEFAULT_POLLING_INTERVAL,
    polling_timeout: int = PyannoteConfig.DEFAULT_POLLING_TIMEOUT
) -> Optional[List[AudioSegmentInfo]]:
    """
    Convenient function to perform diarization without creating class instances.
    
    Args:
        audio_file_path: Path to the audio file
        output_dir: Directory to save speaker segments
        extract_audio: Whether to extract audio segments
        filename_template: Optional template for segment filenames
        polling_interval: Seconds between status checks
        polling_timeout: Maximum seconds to wait
        
    Returns:
        Optional[List[AudioSegmentInfo]]: 
            Information about the extracted segments or None if failed
    """
    processor = DiarizationProcessor()
    return processor.diarize(
        audio_file_path, 
        output_dir, 
        extract_audio,
        filename_template,
        polling_interval,
        polling_timeout
    )

def main():
    """Command-line interface for diarization."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Speaker diarization using pyannote.ai"
        )
    parser.add_argument("audio_file", type=str, help="Path to the audio file")
    parser.add_argument("-o", "--output", type=str, 
                        help="Output directory for speaker segments", default=None)
    parser.add_argument("-i", "--interval", type=int, 
                        help="Polling interval in seconds", 
                        default=PyannoteConfig.DEFAULT_POLLING_INTERVAL)
    parser.add_argument("-t", "--timeout", type=int, help="Polling timeout in seconds", 
                        default=PyannoteConfig.DEFAULT_POLLING_TIMEOUT)
    parser.add_argument("--extract", action="store_true", help="Extract audio segments")
    parser.add_argument(
        "--filename-template", 
        type=str, 
        help="Template for segment filenames (e.g., '{speaker}_{start_ms}.mp3')",
        default=None
    )
    
    args = parser.parse_args()
    
    diarize(
        Path(args.audio_file),
        output_dir=args.output and Path(args.output),
        extract_audio=args.extract,
        filename_template=args.filename_template,
        polling_interval=args.interval,
        polling_timeout=args.timeout
    )


if __name__ == "__main__":
    main()