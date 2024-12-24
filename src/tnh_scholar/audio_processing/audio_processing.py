import yt_dlp
from pathlib import Path
from pydub import AudioSegment
from openai import OpenAI
from openai.types.audio.transcription_verbose import TranscriptionVerbose
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import whisper
from typing import List, Dict, Tuple, Any, Union
from dataclasses import dataclass
import time
import numpy as np
from tnh_scholar.utils import ExpectedTimeTQDM, TimeProgress
from tnh_scholar.openai_interface import token_count_file
from tnh_scholar.logging_config import get_child_logger
import warnings
import os, io, sys
from pydub.silence import detect_silence

# Define constants
MAX_INT16 = 32768.0  # Maximum absolute value for 16-bit signed integer audio
MIN_SILENCE_LENGTH = 1000 # 1 second in ms, for splitting on silence
SILENCE_DBFS_THRESHOLD = -30    # Silence threshold in dBFS
MAX_DURATION_MS = 10 * 60 * 1000  # Max chunk length in milliseconds, 10m
MAX_DURATION = 10 * 60 # Max chunk length in seconds, 10m
SEEK_LENGTH = 50 # miliseconds. for silence detection, the scan interval
EXPECTED_TIME_FACTOR = 0.45 # a hueristic to scale expected time

logger = get_child_logger("audio_processing")


os.environ["OMP_DISPLAY_ENV"] = "FALSE"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OMP_MAX_ACTIVE_LEVELS"] = "1"

@dataclass
class Boundary:
    """A data structure representing a detected audio boundary.

    Attributes:
        start (float): Start time of the segment in seconds.
        end (float): End time of the segment in seconds.
        text (str): Associated text (empty if silence-based).
    
    Example:
        >>> b = Boundary(start=0.0, end=30.0, text="Hello world")
        >>> b.start, b.end, b.text
        (0.0, 30.0, 'Hello world')
    """
    start: float
    end: float
    text: str = ""

def detect_whisper_boundaries(
    audio_file: Path, 
    model_size: str = 'tiny', 
    language: str = None
) -> List[Boundary]:
    """
    Detect sentence boundaries using a Whisper model.

    Args:
        audio_file (Path): Path to the audio file.
        model_size (str): Whisper model size.
        language (str): Language to force for transcription (e.g. 'en', 'vi'), or None for auto.

    Returns:
        List[Boundary]: A list of sentence boundaries with text.
    
    Example:
        >>> boundaries = detect_whisper_boundaries(Path("my_audio.mp3"), model_size="tiny")
        >>> for b in boundaries:
        ...     print(b.start, b.end, b.text)
    """

    # Load model
    logger.info("Loading Whisper model...")
    model = whisper.load_model(model_size)
    logger.info(f"Model '{model_size}' loaded.")
    
    # Calculate expected transcription time
    # logger.info(f"Estimating boundary generation time...")
    # expected_time = estimate_transcription_time(audio_file, model, language=language) * EXPECTED_TIME_FACTOR # heuristic to divide in half
    # logger.info(f"Expected boundary generation time: {expected_time:3.0f} seconds. This may vary significantly from the actual time.")

    if language:
        logger.info(f"Language for boundaries set to '{language}'")
    else:
        logger.info(f"Language not set. Autodetect will be used in Whisper model.")

    # with TimeProgress(expected_time=expected_time, desc="Generating transcription boundaries"):
    boundary_transcription = whisper_model_transcribe(model, str(audio_file), task="transcribe", word_timestamps=True, language=language, verbose=False)
    
    sentence_boundaries = []
    for segment in boundary_transcription['segments']:
        sentence_boundaries.append(
            Boundary(start=segment['start'], end=segment['end'], text=segment['text'])
        )

    return sentence_boundaries, boundary_transcription

def detect_silence_boundaries(
    audio_file: Path,
    min_silence_len: int = MIN_SILENCE_LENGTH,
    silence_thresh: int = SILENCE_DBFS_THRESHOLD,
    max_duration: int = MAX_DURATION_MS
) -> Tuple[List[Boundary], Dict]:
    """
    Detect boundaries (start/end times) based on silence detection.

    Args:
        audio_file (Path): Path to the audio file.
        min_silence_len (int): Minimum silence length to consider for splitting (ms).
        silence_thresh (int): Silence threshold in dBFS.
        max_duration (int): Maximum duration of any segment (ms).

    Returns:
        List[Boundary]: A list of boundaries with empty text.
    
    Example:
        >>> boundaries = detect_silence_boundaries(Path("my_audio.mp3"))
        >>> for b in boundaries:
        ...     print(b.start, b.end)
    """
    logger.debug(f"Detecting silence boundaries with min_silence={min_silence_len}, silence_thresh={silence_thresh}")

    audio = AudioSegment.from_file(audio_file)
    nonsilent_ranges = detect_nonsilent(audio, 
                                        min_silence_len=min_silence_len, 
                                        silence_thresh=silence_thresh, 
                                        seek_step=SEEK_LENGTH)

    # Combine ranges to enforce max_duration
    if not nonsilent_ranges:
        # If no nonsilent segments found, return entire file as one boundary
        duration_s = len(audio) / 1000.0
        return [Boundary(start=0.0, end=duration_s, text="")]

    combined_ranges = []
    current_start, current_end = nonsilent_ranges[0]
    for start, end in nonsilent_ranges[1:]:
        if (current_end - current_start) + (end - start) <= max_duration:
            # Extend the current segment
            current_end = end
        else:
            combined_ranges.append((current_start, current_end))
            current_start, current_end = start, end
    combined_ranges.append((current_start, current_end))

    boundaries = []
    for (start_ms, end_ms) in combined_ranges:
        boundaries.append(Boundary(start=start_ms/1000.0, end=end_ms/1000.0, text=""))
    return boundaries

def split_audio_at_boundaries(
    audio_file: Path,
    boundaries: List[Boundary],
    output_dir: Path = None,
    max_duration: int = MAX_DURATION
) -> Path:
    """
    Split the audio file into chunks based on provided boundaries, ensuring all audio is included
    and boundaries align with the start of Whisper segments.

    Args:
        audio_file (Path): The input audio file.
        boundaries (List[Boundary]): Detected boundaries.
        output_dir (Path): Directory to store the resulting chunks.
        max_duration (int): Maximum chunk length in seconds.

    Returns:
        Path: Directory containing the chunked audio files.
    
    Example:
        >>> boundaries = [Boundary(34.02, 37.26, "..."), Boundary(38.0, 41.18, "...")]
        >>> out_dir = split_audio_at_boundaries(Path("my_audio.mp3"), boundaries)
    """
    logger.info(f"Splitting audio with max_duration={max_duration} seconds")

    # Load the audio file
    audio = AudioSegment.from_file(audio_file)

    # Create output directory based on filename
    if output_dir is None:
        output_dir = audio_file.parent / f"{audio_file.stem}_chunks"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Clean up the output directory
    for file in output_dir.iterdir():
        if file.is_file():
            logger.info(f"Deleting existing file: {file}")
            file.unlink()

    chunk_start = 0  # Start time for the first chunk in ms
    chunk_count = 1
    current_chunk = AudioSegment.empty()

    for idx, boundary in enumerate(boundaries):
        segment_start_ms = int(boundary.start * 1000)
        if idx + 1 < len(boundaries):
            segment_end_ms = int(boundaries[idx + 1].start * 1000)  # Next boundary's start
        else:
            segment_end_ms = len(audio)  # End of the audio for the last boundary

        # Adjust for the first segment starting at 0
        if idx == 0 and segment_start_ms > 0:
            segment_start_ms = 0  # Ensure we include the very beginning of the audio

        segment = audio[segment_start_ms:segment_end_ms]

        logger.debug(f"Boundary index: {idx}, segment_start: {segment_start_ms / 1000}, segment_end: {segment_end_ms / 1000}, duration: {segment.duration_seconds}")
        logger.debug(f"Current chunk Duration (s): {current_chunk.duration_seconds}")

        if len(current_chunk) + len(segment) <= max_duration * 1000:
            # Add segment to the current chunk
            current_chunk += segment
        else:
            # Export current chunk
            chunk_path = output_dir / f"chunk_{chunk_count}.mp3"
            current_chunk.export(chunk_path, format="mp3")
            logger.info(f"Exported: {chunk_path}")
            chunk_count += 1

            # Start a new chunk with the current segment
            current_chunk = segment

    # Export the final chunk if any audio remains
    if len(current_chunk) > 0:
        chunk_path = output_dir / f"chunk_{chunk_count}.mp3"
        current_chunk.export(chunk_path, format="mp3")
        logger.info(f"Exported: {chunk_path}")

    return output_dir

def split_audio(
    audio_file: Path,
    method: str = "whisper",
    output_dir: Path = None,
    model_size: str = 'tiny',
    language: str = None,
    min_silence_len: int = MIN_SILENCE_LENGTH,
    silence_thresh: int = SILENCE_DBFS_THRESHOLD,
    max_duration: int = MAX_DURATION
) -> Path:
    """
    High-level function to split an audio file into chunks based on a chosen method.

    Args:
        audio_file (Path): The input audio file.
        method (str): Splitting method, "silence" or "whisper".
        output_dir (Path): Directory to store output.
        model_size (str): Whisper model size if method='whisper'.
        language (str): Language for whisper transcription if method='whisper'.
        min_silence_len (int): For silence-based detection, min silence length in ms.
        silence_thresh (int): Silence threshold in dBFS.
        max_duration_s (int): Max chunk length in seconds.
        max_duration_ms (int): Max chunk length in ms (for silence detection combination).

    Returns:
        Path: Directory containing the resulting chunks.

    Example:
        >>> # Split using silence detection
        >>> split_audio(Path("my_audio.mp3"), method="silence")

        >>> # Split using whisper-based sentence boundaries
        >>> split_audio(Path("my_audio.mp3"), method="whisper", model_size="base", language="en")
    """

    logger.info(f"Splitting audio with max_duration={max_duration} seconds")

    if method == "whisper":
        boundaries, _ = detect_whisper_boundaries(audio_file, model_size=model_size, language=language)

    elif method == "silence":
        max_duration_ms = max_duration * 1000 # convert duration in seconds to miliseconds
        boundaries = detect_silence_boundaries(audio_file, 
                                               min_silence_len=min_silence_len, 
                                               silence_thresh=silence_thresh, 
                                               max_duration=max_duration_ms)
    else:
        raise ValueError(f"Unknown method: {method}. Must be 'silence' or 'whisper'.")
    
    # delete all files in the output_dir (this is useful for reprocessing)

    return split_audio_at_boundaries(audio_file, boundaries, output_dir=output_dir, max_duration=max_duration)

def estimate_transcription_time(
    audio_file: Path,
    model,
    language: str | None = None,
    sample_duration: int = 60
) -> float:
    """
    Estimate how long it might take to transcribe the entire audio file using
    a Whisper model by sampling a small chunk (e.g. 60 seconds) in the middle
    and timing the transcription.

    Args:
        audio_file (Path): Path to the audio file.
        model: The Whisper model.
        language (Optional[str]): If known, specify a language code to skip detection
                                  (e.g. "en", "vi"). Otherwise, None for auto-detect.
        sample_duration (int): Length of audio (in seconds) to sample and time 
                               for the estimate.

    Returns:
        float: Estimated total transcription time in seconds.

    Example:
        >>> total_time_est = estimate_transcription_time(Path("example.mp3"), "tiny", "en", 60)
        >>> print(f"Estimated full transcription time: {total_time_est:.2f} sec")
    """
    # 1) Load entire audio to get total length in ms
    audio = AudioSegment.from_file(audio_file)
    total_length_ms = len(audio)
    total_length_sec = total_length_ms / 1000.0

    # 2) Extract a 60-second chunk from the "middle"
    #    If the audio is shorter than sample_duration, we just sample the entire file
    if total_length_sec <= sample_duration:
        sample_audio = audio
    else:
        middle_ms = total_length_ms / 2
        half_sample_ms = sample_duration * 1000 / 2
        start_ms = max(0, middle_ms - half_sample_ms)
        end_ms = min(total_length_ms, middle_ms + half_sample_ms)
        sample_audio = audio[start_ms:end_ms]

    # 3) Convert the chunk to a NumPy array
    audio_array = audio_to_numpy(sample_audio)

    # 4) Time the transcription of just this chunk
    start_time = time.time()

    # Force language if provided, or let Whisper auto-detect otherwise
    transcribe_kwargs = {"language": language} if language else {}
    
    whisper_model_transcribe(model, audio_array, **transcribe_kwargs)
    
    elapsed_chunk_time = time.time() - start_time

    # 5) Scale up by ratio
    #    (If 60s chunk took X seconds to transcribe, we guess that full_length_seconds
    #     will take (full_length_seconds / sample_duration) * X .)
    if total_length_sec > sample_duration:
        scale_factor = total_length_sec / sample_duration
    else:
        scale_factor = 1.0

    estimated_total_time = elapsed_chunk_time * scale_factor
    return estimated_total_time

def audio_to_numpy(audio_segment: AudioSegment) -> np.ndarray:
    """
    Convert an AudioSegment object to a NumPy array suitable for Whisper.

    Args:
        audio_segment (AudioSegment): The input audio segment to convert.

    Returns:
        np.ndarray: A mono-channel NumPy array normalized to the range [-1, 1].

    Example:
        >>> audio = AudioSegment.from_file("example.mp3")
        >>> audio_numpy = audio_to_numpy(audio)
    """
    # Convert the audio segment to raw sample data
    raw_data = np.array(audio_segment.get_array_of_samples()).astype(np.float32)
    
    # Normalize data to the range [-1, 1]
    raw_data /= MAX_INT16
    
    # Ensure mono-channel (use first channel if stereo)
    if audio_segment.channels > 1:
        raw_data = raw_data.reshape(-1, audio_segment.channels)[:, 0]

    return raw_data

def whisper_model_transcribe(
    model: Any,
    input_source: Any,
    *args,
    **kwargs,
) -> Dict[str, Any]:
    """
    Wrapper around model.transcribe that suppresses the known
    'FP16 is not supported on CPU; using FP32 instead' UserWarning
    and redirects unwanted 'OMP' messages to prevent interference.

    This function accepts all args and kwargs that model.transcribe normally does,
    and supports input sources as file paths (str or Path) or in-memory audio arrays.

    Parameters:
        model (Any): The Whisper model instance.
        input_source (Union[str, Path, np.ndarray]): Input audio file path, URL, or in-memory audio array.
        *args: Additional positional arguments for model.transcribe.
        **kwargs: Additional keyword arguments for model.transcribe.

    Returns:
        Dict[str, Any]: Transcription result from model.transcribe.

    Example:
        # Using a file path
        result = whisper_model_transcribe(my_model, "sample_audio.mp3", verbose=True)

        # Using an audio array
        result = whisper_model_transcribe(my_model, audio_array, language="en")
    """
  
    class StdoutFilter(io.StringIO):
        def __init__(self, original_stdout):
            super().__init__()
            self.original_stdout = original_stdout

        def write(self, message):
            # Suppress specific messages like 'OMP:' while allowing others
            if "OMP:" not in message:
                self.original_stdout.write(message)

    with warnings.catch_warnings(), StdoutFilter(sys.stdout) as filtered_stdout:
        warnings.filterwarnings(
            "ignore",
            message="FP16 is not supported on CPU; using FP32 instead",
            category=UserWarning,
        )

        # Redirect stdout to suppress OMP messages
        original_stdout = sys.stdout
        sys.stdout = filtered_stdout

        try:
            # Convert Path to str if needed
            if isinstance(input_source, Path):
                input_source = str(input_source)

            # Call the original transcribe function
            return model.transcribe(input_source, *args, **kwargs)
        finally:
            # Restore original stdout
            sys.stdout = original_stdout
    
def calculate_silence_percentage(audio_file: Path, silence_thresh: int = -30, min_silence_len: int = 3000) -> float:
    """
    Calculate the percentage of silence in an audio file.
    
    Args:
        audio_file (Union[str, Path]): Path to the audio file.
        silence_thresh (int): Silence threshold in dBFS (default: -30 dB).
        min_silence_len (int): Minimum length of silence in milliseconds (default: 1000 ms).
    
    Returns:
        float: Percentage of silence in the audio, as a value between 0 and 1.
    
    Example:
        >>> calculate_silence_percentage("example.mp3", silence_thresh=-30, min_silence_len=500)
        0.25
    """
    # Load the audio file
    audio = AudioSegment.from_file(audio_file)

    # Total duration of the audio in milliseconds
    total_duration = len(audio)

    # Detect silent segments
    silent_segments = detect_silence(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh, seek_step=1000)

    # Calculate total silence duration
    total_silence_duration = sum(end - start for start, end in silent_segments)

    # Calculate and return the percentage of silence
    return total_silence_duration / total_duration if total_duration > 0 else 0.0

# def detect_boundaries(audio_file: Path, model_size: str = 'tiny', language=None) -> List[Dict[str, float]]:
#     """
#     Use Whisper to detect sentence boundaries in the audio file.

#     Args:
#         audio_file (Path): Path to the audio file.
#         model_size (str): Whisper model size (e.g., 'tiny', 'base', 'small').

#     Returns:
#         List[Dict[str, float]]: List of timestamps with sentence boundaries. Each entry contains:
#             - "start": Start time of the sentence (in seconds).
#             - "end": End time of the sentence (in seconds).
#             - "text": Sentence text.
#     """
#     # Load the Whisper model
#     logger.info("Loading model...")
#     model = whisper.load_model(model_size)
#     logger.info(f"Model '{model_size}' loaded.")

#     # Transcribe the audio file
#     logger.info(f"Transcribing with language: {language or 'auto-detected (default: en)'}")
#     logger.info("Transcribing preliminary text...")
#     if language:
#         result = model.transcribe(str(audio_file), task="transcribe", word_timestamps=True, language="vi")
#     else:
#         result = model.transcribe(str(audio_file), task="transcribe", word_timestamps=True, language="en")
#     logger.info("Intial transcription for boundaries generated.")
    
#     # Extract sentence boundaries from segments
#     sentence_boundaries = []
#     for segment in result['segments']:
#         sentence_boundaries.append({
#             "start": segment['start'],
#             "end": segment['end'],
#             "text": segment['text']
#         })
    
#     return sentence_boundaries

# def split_audio_at_boundaries(
#         audio_file: Path, 
#         boundaries: List[Dict[str, float]], 
#         output_dir: Path  = None, 
#         max_duration: int = MAX_DURATION) -> Path:
#     """
#     Split the audio file into chunks close to a specified duration while respecting boundaries.

#     Args:
#         audio_file (Path): Path to the audio file.
#         boundaries (List[Dict[str, float]]): List of boundaries with start and end times.
#         output_dir (Path): Directory to save the chunks.
#         max_duration (int): Maximum duration for each chunk in seconds (default is 10 minutes).

#     Returns:
#         Path: Path to the directory containing the chunks.
#     """
#     # Load the audio file
#     audio = AudioSegment.from_file(audio_file)
    
#     # Create output directory based on filename
#     if output_dir is None:
#         output_dir = audio_file.parent / f"{audio_file.stem}_chunks"
#     output_dir.mkdir(parents=True, exist_ok=True) 

#     logger.info(f"Split audio at boundaries max_duration: {max_duration}")   
#     # Initialize variables
#     current_chunk = AudioSegment.empty()
#     current_start = boundaries[0]["start"]
#     chunk_count = 1

#     for i, boundary in enumerate(boundaries):
#         # Calculate segment duration
#         segment_start_ms = boundary["start"] * 1000
#         segment_end_ms = boundary["end"] * 1000
#         segment = audio[segment_start_ms:segment_end_ms]
        
#         # Add segment to the current chunk if it fits
#         if len(current_chunk) + len(segment) <= max_duration * 1000:
#             current_chunk += segment
#         else:
#             # Export the current chunk
#             chunk_path = output_dir / f"chunk_{chunk_count}.mp3"
#             current_chunk.export(chunk_path, format="mp3")
#             logger.info(f"Exported: {chunk_path}")
            
#             # Start a new chunk
#             chunk_count += 1
#             current_chunk = segment
#             current_start = boundary["start"]
    
#     # Export the final chunk
#     if len(current_chunk) > 0:
#         chunk_path = output_dir / f"chunk_{chunk_count}.mp3"
#         current_chunk.export(chunk_path, format="mp3")
#         logger.info(f"Exported: {chunk_path}")

#     return output_dir

# def split_audio_on_silence(
#     audio_file: Path,
#     output_dir: Path = None,
#     min_silence_len: int = MIN_SILENCE_LENGTH,  # Silence threshold in milliseconds
#     silence_thresh: int = SILENCE_DBFS_THRESHOLD,    # Silence threshold in dBFS
#     max_duration: int = MAX_DURATION_MS  # Max chunk length in milliseconds
# ) -> Path:
#     """
#     Test to split an audio file into chunks based on silence detection.

#     Args:
#         audio_file (Path): Path to the audio file.
#         output_dir (Path): Directory to save the audio chunks. Defaults to a subdirectory of the input file.
#         min_silence_len (int): Minimum silence length to consider a split point 
#         silence_thresh (int): Silence threshold in dBFS 
#         max_duration (int): Maximum length of any chunk 
#     Returns:
#         Path: Directory containing the audio chunks.
#     """
#     logger.debug(f"Audio split parameters: min_silence={min_silence_len}, silence_threshold={silence_thresh}, max_duration={MAX_DURATION_MS}")

#     # Load the audio file
#     logger.debug("loading audio file...")
#     audio = AudioSegment.from_file(audio_file)

#     # Set up output directory
#     if output_dir is None:
#         output_dir = audio_file.parent / f"{audio_file.stem}_s_chunks"
#     output_dir.mkdir(parents=True, exist_ok=True)

#     # Detect nonsilent segments
#     logger.debug("starting silence detection...")
#     nonsilent_ranges = detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh, seek_step=SEEK_LENGTH)
#     logger.debug(f"finished detection: {len(nonsilent_ranges)}")

#     # Combine nonsilent ranges to stay below max_chunk_length
#     logger.debug("Combining ranges to fit within max_chunk_length...")
#     combined_ranges = []
#     current_start, current_end = nonsilent_ranges[0]
#     for start, end in nonsilent_ranges[1:]:
#         # Check if adding the next segment exceeds the max_chunk_length
#         if (current_end - current_start) + (end - start) <= max_duration:
#             # Extend the current range
#             current_end = end
#         else:
#             # Save the current range and start a new one
#             combined_ranges.append((current_start, current_end))
#             current_start, current_end = start, end

#     # Append the final range
#     combined_ranges.append((current_start, current_end))

#     logger.debug(f"Combined ranges: {len(combined_ranges)} chunks created.")

#     # Export chunks
#     logger.info("Exporting chunks")
#     chunk_paths = []
#     for i, (start, end) in enumerate(combined_ranges):
#         chunk = audio[start:end]
#         chunk_path = output_dir / f"chunk_{i + 1}.mp3"
#         chunk.export(chunk_path, format="mp3")
#         logger.info(f"Chunk {i+1} exported.")
#         chunk_paths.append(chunk_path)

#     return output_dir

# def split_audio_at_boundaries(
#     audio_file: Path,
#     boundaries: List[Boundary],
#     output_dir: Path = None,
#     max_duration: int = MAX_DURATION
# ) -> Path:
#     """
#     Split the audio file into chunks based on provided boundaries.

#     Args:
#         audio_file (Path): The input audio file.
#         boundaries (List[Boundary]): Detected boundaries.
#         output_dir (Path): Directory to store the resulting chunks.
#         max_duration (int): Max chunk length in seconds.

#     Returns:
#         Path: Directory containing the chunked audio files.
    
#     Example:
#         >>> boundaries = [Boundary(0.0,30.0,"..."), Boundary(30.0,60.0,"...")]
#         >>> out_dir = split_audio_at_boundaries(Path("my_audio.mp3"), boundaries)
#     """

#     logger.info(f"Splitting audio with max_duration={max_duration} seconds")

#     # Load the audio file
#     audio = AudioSegment.from_file(audio_file)

#     # Create output directory based on filename 
#     if output_dir is None:
#         output_dir = audio_file.parent / f"{audio_file.stem}_chunks"
#     output_dir.mkdir(parents=True, exist_ok=True)

#     # Clean up the output directory
#     for file in output_dir.iterdir():
#         if file.is_file():
#             logger.info(f"Deleting existing file: {file}")
#             file.unlink()

#     current_chunk = AudioSegment.empty()
#     chunk_count = 1

#     for idx, boundary in enumerate(boundaries):
#         seg_start_ms = int(boundary.start * 1000)
#         seg_end_ms = int(boundary.end * 1000)
#         segment = audio[seg_start_ms:seg_end_ms]

#         logger.debug(f"boundary index: {idx}, boundary.start: {boundary.start}, boundary.end: {boundary.end}")
#         logger.debug(f"current chunk length = {len(current_chunk)}, {current_chunk.duration_seconds}")
#         if len(current_chunk) + len(segment) <= max_duration * 1000:
#             current_chunk += segment
#         else:
#             chunk_path = output_dir / f"chunk_{chunk_count}.mp3"
#             current_chunk.export(chunk_path, format="mp3")
#             logger.debug(f"Final chunk length = {len(current_chunk)}, {current_chunk.duration_seconds}")
#             logger.info(f"Exported: {chunk_path}")
#             chunk_count += 1
#             current_chunk = segment

#     # Export the final chunk if present
#     if len(current_chunk) > 0:
#         chunk_path = output_dir / f"chunk_{chunk_count}.mp3"
#         current_chunk.export(chunk_path, format="mp3")
#         logger.info(f"Exported: {chunk_path}")

#     return output_dir
