from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from pydantic import BaseModel

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils.file_utils import ensure_directory_exists, write_str_to_file

from .pyannote_client import DiarizationParams, PyannoteClient

# Load environment variables
load_dotenv()

# Logger placeholder - will be replaced by your logger setup
logger = get_child_logger(__name__)

PYANNOTE_FILE_STR = "_pyannote_diarization"

class PyannoteResult(BaseModel):
    """Raw diarization results from Pyannote API."""
    status: str
    output: Dict
    job_id: Optional[str] = None
    error: Optional[str] = None
    
    @classmethod
    def from_api_response(cls, response: Dict) -> "PyannoteResult":
        """Create model from API response dictionary."""
        return cls(**response)
        
    def save_to_file(self, file_path: Path) -> None:
        """Save raw results to JSON file."""
        content = self.model_dump_json(indent=2)
        write_str_to_file(file_path, content, overwrite=True)
        logger.debug(f"Raw diarization results saved to {file_path}")


class DiarizationProcessor:
    """Process audio files for speaker diarization using pyannote.ai."""
    
    def __init__(
        self,
        audio_file_path: Path,
        output_path: Optional[Path] = None,
        api_key: Optional[str] = None,
        diarization_params: Optional[DiarizationParams] = None,
    ):
        """
        Initialize diarization processor.

        Args:
            audio_file_path: the audio file to process
            output_path: the output file path for results (JSON)
            api_key: Pyannote.ai API key (defaults to environment variable)
        """
        self.pyannote = PyannoteClient(api_key)
        self.last_job_id = None  # Store the most recent job ID
        self.params = diarization_params

        try:
            self.audio_file_path = audio_file_path.resolve()
            if not self.audio_file_path.exists():
                logger.error(f"Audio file not found: {audio_file_path}")
                raise FileNotFoundError(f"Audio file not found {audio_file_path}")
        except (ValueError, OSError) as e:
            logger.error(f"Diarization failed: {e}")
            raise e

        if output_path is None:
            self.output_path = (
                audio_file_path.parent / f"{audio_file_path.stem}{PYANNOTE_FILE_STR}.json"
            )
        else:
            self.output_path = output_path.resolve()
        ensure_directory_exists(self.output_path.parent)

    def save_and_export_diarization(
        self,
        results: Dict,
        extract_audio: bool = False
    ) -> Dict[str, Any]:
        """
        Save and export diarization results to the specified output path.

        Args:
            results: Raw results from the diarization API
            extract_audio: (unused, for future extension)

        Returns:
            Dict[str, Any]: The 'output' field from the diarization result
        """
        diarization_result = PyannoteResult.from_api_response(results)
        diarization_result.save_to_file(self.output_path)
        return diarization_result.model_dump()['output']
    
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
        job_id = self.pyannote.start_diarization(media_id, params=self.params)
        if not job_id:
            logger.error("Failed to start diarization job")
            return None
            
        return job_id

    def diarize(
        self, 
        extract_audio: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Complete diarization process from audio file to speaker segments.
        
        Args:
            extract_audio: Whether to extract audio segments
            polling_interval: Seconds between status checks
            polling_timeout: Maximum seconds to wait
            
        Returns:
            Optional[List[SpeakerChunk]]: Information about segments or None if failed
            
        Note:
            If the job times out, the job ID is still available from self.last_job_id
        """
        # Upload and start job
        job_id = self._upload_and_start_job(self.audio_file_path)
        if not job_id:
            return None
            
        # Store job ID for potential resume later
        self.last_job_id = job_id
        
        # Poll the job
        results = self.pyannote.poll_job_until_complete(job_id)
        
        if not results:
            logger.warning(
                f"Job {job_id} did not complete within timeout. "
                "You can resume later using resume_diarization()."
            )
            return None
            
        # save and return results
        return self.save_and_export_diarization(results, extract_audio)

    def resume_diarization(
            self,
            job_id: Optional[str] = None,
            extract_audio: bool = False,
        ) -> Optional[Dict[str, Any]]:
            """
            Resume a previously started diarization job that may have timed out.
            
            Args:
                job_id: The job ID of the previously started job 
                    (defaults to last_job_id)
                extract_audio: Whether to extract audio segments
                polling_interval: Seconds between status checks
                polling_timeout: Maximum seconds to wait
                
            Returns:
                Optional[List[SpeakerChunk]]: Information about segments 
                    or None if failed
                
            Raises:
                ValueError: If job_id is not provided and last_job_id is not set
            """
            # Use provided job_id or fall back to last_job_id
            target_job_id = job_id or self.last_job_id
            
            if not target_job_id:
                raise ValueError(
                    "No job ID provided and no previous job ID found. "
                    "Please provide a job ID to resume."
                )
                
            logger.info(f"Resuming diarization job: {target_job_id}")
            
            # Poll the job
            results = self.pyannote.poll_job_until_complete(target_job_id)
            
            if not results:
                logger.error(f"Failed to get results for job {target_job_id}")
                return None
                
            # Process results
            return self.save_and_export_diarization(results, extract_audio)


def diarize(
    audio_file_path: Path, 
    output_path: Optional[Path] = None,
    extract_audio: bool = False,
    num_speakers: Optional[int] = None,
    confidence_limit: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
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
 
    params = DiarizationParams(
        num_speakers=num_speakers, 
        confidence=confidence_limit,
        )
    
    processor = DiarizationProcessor(
        audio_file_path,
        output_path=output_path,
        diarization_params=params)
    return processor.diarize( 
        extract_audio,
    )

def resume_diarization(
    audio_file_path: Path,
    job_id: str,
    output_path: Optional[Path] = None,
    extract_audio: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Resume a previously started diarization job.
    
    Args:
        job_id: The job ID to resume
        audio_file_path: Original audio file path (needed for extraction)
        output_dir: Directory to save speaker segments
        extract_audio: Whether to extract audio segments
        polling_interval: Seconds between status checks
        polling_timeout: Maximum seconds to wait
        
    Returns:
        Optional[List[SpeakerChunk]]: 
            Information about the extracted segments or None if failed
    """
    processor = DiarizationProcessor(audio_file_path, output_path)
    processor.last_job_id = job_id  # Set the job ID
    
    return processor.resume_diarization(
        job_id=job_id,
        extract_audio=extract_audio,
    )
    
def check_job_status(job_id: str, api_key: Optional[str] = None) -> Dict:
    """
    Check the status of a diarization job without processing results.
    
    Args:
        job_id: The job ID to check
        api_key: Optional API key (uses environment variable if not provided)
        
    Returns:
        Dict: Job status information with fields:
            - status: Current job status ("pending", "running", "succeeded", "failed")
            - error: Error message if job failed
            - output: Job output if job succeeded
            
    Raises:
        APIKeyError: If API key is missing or invalid
        requests.RequestException: If API request fails
    """
    client = PyannoteClient(api_key)
    status = client.check_job_status(job_id)
    
    if not status:
        logger.error(f"Failed to get status for job {job_id}")
        return {"status": "unknown", "error": "Failed to get job status"}
        
    return status
