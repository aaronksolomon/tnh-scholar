from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from pydantic import BaseModel

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils.file_utils import ensure_directory_exists, write_str_to_file

from .pyannote_interface import PyannoteClient

# Load environment variables
load_dotenv()

# Logger placeholder - will be replaced by your logger setup
logger = get_child_logger(__name__)

class ProcessingConfig:
    """Configuration for audio processing."""
        

class DiarizationResult(BaseModel):
    """Raw diarization results from Pyannote API."""
    status: str
    output: Dict
    job_id: Optional[str] = None
    error: Optional[str] = None
    
    @classmethod
    def from_api_response(cls, response: Dict) -> "DiarizationResult":
        """Create model from API response dictionary."""
        return cls(**response)
        
    def save_to_file(self, file_path: Path) -> None:
        """Save raw results to JSON file."""
        content = self.model_dump_json(indent=2)
        write_str_to_file(file_path, content, overwrite=True)
        logger.debug(f"Raw diarization results saved to {file_path}")
        
class DiarizationProcessor:
    """Process audio files for speaker diarization using pyannote.ai."""
    
    def __init__(self, 
                 audio_file_path: Path, 
                 output_dir: Optional[Path] = None,
                 api_key: Optional[str] = None,
                 num_speakers: Optional[int] = None,
                 confidence_limit: Optional[float] = None,
                 ):
        
        """
        Initialize diarization processor.
        
        Args:
            audio_file_path: the audio file to process
            output_dir: the output directory for results if specified
            api_key: Pyannote.ai API key (defaults to environment variable)
            
        """
        self.pyannote = PyannoteClient(api_key)
        self.last_job_id = None  # Store the most recent job ID
        
        try:
            self.audio_file_path = audio_file_path.resolve()
            if not self.audio_file_path.exists():
                logger.error(f"Audio file not found: {audio_file_path}")
                raise FileNotFoundError(f"Audio file not found {audio_file_path}")
        except (ValueError, OSError) as e:
            logger.error(f"Diarization failed: {e}")
            raise e
        
        if output_dir is None:
            self.output_dir = audio_file_path.parent \
                / f"{audio_file_path.stem}_segments"
        else:
            self.output_dir = output_dir.resolve()
            
        ensure_directory_exists(self.output_dir)

    def save_and_export_diarization(
        self, 
        results: Dict, 
        extract_audio: bool = False
    ) -> Dict[str, Any]:
        """
        """

        # Convert to model and save raw results
        diarization_result = DiarizationResult.from_api_response(results)
        raw_results_path = self.output_dir / "raw_diarization_results.json"
        diarization_result.save_to_file(raw_results_path)
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
        job_id = self.pyannote.start_diarization(media_id)
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
    output_dir: Optional[Path] = None,
    extract_audio: bool = False,
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
    processor = DiarizationProcessor(audio_file_path, output_dir)
    return processor.diarize( 
        extract_audio,
    )

def resume_diarization(
    audio_file_path: Path,
    job_id: str,
    output_dir: Optional[Path] = None,
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
    processor = DiarizationProcessor(audio_file_path, output_dir)
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

# def _log_processing_progress(
#         self,
#         current_index: int,
#         total_count: int
#     ) -> None:
#         """
#         Log processing progress at appropriate intervals.
        
#         Args:
#             current_index: Current segment index (0-based)
#             total_count: Total number of segments
#         """
#         # Convert to 1-based for logging
#         segment_num = current_index + 1
        
#         # Log at intervals or at the end
#         if (segment_num % ProcessingConfig.PROGRESS_INTERVAL == 0 or 
#             segment_num == total_count):
#             logger.info(f"Processed {
#                 segment_num}/{total_count} segments")
        
# def main():
#     """Command-line interface for diarization."""
#     import argparse
    
#     parser = argparse.ArgumentParser(
#         description="Speaker diarization using pyannote.ai"
#         )
#     parser.add_argument("audio_file", type=str, help="Path to the audio file")
#     parser.add_argument("-o", "--output", type=str, 
#                         help="Output directory for speaker segments", default=None)
#     parser.add_argument("--extract", action="store_true", help="Extract audio segments")
#     parser.add_argument(
#         "--filename-template", 
#         type=str, 
#         help="Template for segment filenames (e.g., '{speaker}_{start_ms}.mp3')",
#         default=None
#     )
    
#     args = parser.parse_args()
    
#     diarize(
#         Path(args.audio_file),
#         output_dir=args.output and Path(args.output),
#         extract_audio=args.extract
#     )



# if __name__ == "__main__":
#     main()

# def _extract_diarization_segments(self, results: Dict) -> Optional[List[Dict]]:
#     """
#     Extract diarization segments from API response.
    
#     Args:
#         results: The diarization results from the API
        
#     Returns:
#         Optional[List[Dict]]: Extracted segments or None if not found/invalid
#     """
#     # Check job status
#     if results.get(PyannoteConfig.STATUS_FIELD) != PyannoteConfig.SUCCESS_STATUS:
#         error = results.get(PyannoteConfig.ERROR_FIELD, "No error details provided")
#         logger.error(
#             f"Job failed with status: {results.get(PyannoteConfig.STATUS_FIELD)}"
#             )
#         logger.error(f"Error details: {error}")
#         return None
    
#     # Get diarization segments
#     output = results.get(PyannoteConfig.OUTPUT_FIELD, {})
#     segments = output.get(PyannoteConfig.DIARIZATION_FIELD, [])
    
#     if not segments:
#         logger.error("No diarization segments found in results")
#         return None
    
#     logger.info(f"Found {len(segments)} diarization segments")
#     return segments

# def _is_long_segment(
#     self,
#     segment: DiarizationSegment,
#     target_chunk_size: float
#     ) -> bool:
#     """Check if a segment exceeds the target chunk size."""
#     return segment.duration > target_chunk_size

# def _handle_long_segment(
#     self,
#     segment: DiarizationSegment,
#     target_chunk_size: float
# ) -> SpeakerChunk:
#     """Process a segment that exceeds the target chunk size."""
#     logger.warning(
#         f"Segment duration ({segment.duration:.2f}s) "
#         f"exceeds target chunk size ({target_chunk_size}s). "
#         f"Using as standalone chunk."
#     )
#     return SpeakerChunk.from_segment(segment)

# def _add_segment(
#     self, 
#     segment: DiarizationSegment, 
#     current_chunk: SpeakerChunk | None, 
#     chunks: List[SpeakerChunk], 
#     ):
    
    
#     if current_chunk is None:
#         return None, chunks
    
#     if current_chunk.can_merge(segment, self.spacing_threshold):
#         current_chunk.merge_segment(segment)
#         if current_chunk.exceeds_target_size(self.target_chunk_size):
#             chunks.append(current_chunk)
#             current_chunk = None
#     else:
#         chunks.append(current_chunk)
#         current_chunk = SpeakerChunk.from_segment(segment)
        
#     return current_chunk, chunks

# class AudioSegmentChunk(BaseModel):
#     """Represents a merged chunk of speaker segments."""
#     speaker: str = Field(..., description="Speaker identifier")
#     start: float = Field(..., description="Start time in seconds")
#     end: float = Field(..., description="End time in seconds")
#     duration: float = Field(..., description="Duration in seconds")
#     filename: str = Field(..., description="Path to the audio file")
#     original_segments: List[Dict] = Field(
#         default_factory=list, 
#         description="Original API segments that were merged"
#         )
    
#     def export(self, format: str = "json", pretty: bool = True) -> str:
#         """
#         Export segment chunk information to the specified format.
        
#         Args:
#             format: Output format ("json" for now)
#             pretty: Whether to use pretty-printing (indentation)
            
#         Returns:
#             Formatted string representation of the segment info
#         """
#         if format.lower() == "json":
#             return self.model_dump_json(indent=2 if pretty else None)
#         else:
#             raise ValueError(f"Unsupported export format: {format}")
            
#     def save_to_file(
#         self, 
#         file_path: Path, 
#         format: str = "json", 
#         pretty: bool = True
#         ) -> None:
#         """
#         Save segment chunk information to a file.
        
#         Args:
#             file_path: Path where to save the information
#             format: Output format ("json" for now)
#             pretty: Whether to use pretty-printing (indentation)
#         """
#         content = self.export(format, pretty)
#         write_str_to_file(file_path, content, overwrite=True)
#         logger.debug(f"Segment chunk info saved to {file_path}")
           
#     @property
#     def start_ms(self) -> int:
#         """Get start time in milliseconds."""
#         return int(self.start * 1000)
    
#     @property
#     def end_ms(self) -> int:
#         """Get end time in milliseconds."""
#         return int(self.end * 1000)

# class SpeakerChunk(BaseModel):
#     """Represents a merged chunk of speaker segments."""
#     speaker: str = Field(..., description="Speaker identifier")
#     start: float = Field(..., description="Start time in seconds")
#     end: float = Field(..., description="End time in seconds")
#     original_segments: List[DiarizationSegment] = Field(
#         default_factory=list, 
#         description="Original API segments that were merged"
#     )
    
#     @property
#     def duration(self) -> float:
#         """Calculate chunk duration in seconds."""
#         return self.end - self.start
    
#     @property
#     def start_ms(self) -> int:
#         """Get start time in milliseconds."""
#         return int(self.start * 1000)
    
#     @property
#     def end_ms(self) -> int:
#         """Get end time in milliseconds."""
#         return int(self.end * 1000)
        
#     def can_merge(
#         self, 
#         segment: DiarizationSegment, 
#         spacing_threshold: float
#     ) -> bool:
#         """Check if a segment can be merged into this chunk."""
#         if segment.speaker != self.speaker:
#             return False
            
#         # Check time gap
#         gap = self.end - segment.start
#         return gap <= spacing_threshold
    
#     def merge_segment(self, segment: DiarizationSegment) -> None:
#         """Merge a segment into this chunk."""
#         self.end = max(self.end, segment.end)
#         self.original_segments.append(segment)
    
#     def exceeds_target_size(self, target_size: float) -> bool:
#         """Check if chunk exceeds target size."""
#         return self.duration >= target_size
    
#     def build_filename(
#         self, 
#         output_dir: Path, 
#         template: str
#     ) -> str:
#         """Generate filename based on template."""
#         filename_str = template.format(
#             speaker=self.speaker,
#             start_ms=self.start_ms,
#             end_ms=self.end_ms,
#             start=self.start,
#             end=self.end
#         )
#         return str(output_dir / filename_str)
        
#     @classmethod
#     def from_segment(cls, segment: DiarizationSegment) -> "SpeakerChunk":
#         """Create a new chunk from a single segment."""
#         return cls(
#             speaker=segment.speaker,
#             start=segment.start,
#             end=segment.end,
#             original_segments=[segment]
#         )
# class DiarizationSegment(BaseModel):
#     """Represents a single speaker segment from Diarization"""
#     speaker: str
#     start: float
#     end: float
    
#     @property
#     def duration(self) -> float:
#         """Calculate segment duration in seconds."""
#         return self.end - self.start
        
#     def overlaps_with(self, other: "DiarizationSegment") -> bool:
#         """Check if this segment overlaps with another segment."""
#         return (self.start <= other.end) and (other.start <= self.end)
        
#     def gap_to(self, other: "DiarizationSegment") -> float:
#         """
#         Calculate time gap between this segment and another.
#         Returns positive value if other is after this one, negative if they overlap.
#         """
#         return other.start - self.end
    
#     def same_speaker_as(self, other: "DiarizationSegment") -> bool:
#         """Check if this segment has the same speaker as another segment."""
#         return self.speaker == other.speaker
    
#     def merge_with(self, other: "DiarizationSegment") -> "DiarizationSegment":
#         """
#         Create a new segment by merging this one with another one.
#         Assumes segments are from the same speaker.
#         """
#         if not self.same_speaker_as(other):
#             raise ValueError("Cannot merge segments with different speakers")
            
#         return DiarizationSegment(
#             speaker=self.speaker,
#             start=min(self.start, other.start),
#             end=max(self.end, other.end)
#         )

