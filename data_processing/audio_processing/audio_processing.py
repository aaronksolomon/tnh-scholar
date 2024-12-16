import yt_dlp
from pathlib import Path
from pydub import AudioSegment
from openai import OpenAI
from openai.types.audio.transcription_verbose import TranscriptionVerbose
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import whisper
import logging
from typing import List, Dict
from dataclasses import dataclass
import json
import csv
import warnings
from logging_config import get_child_logger

MIN_SILENCE_LENGTH = 1000 # 1 second in ms, for splitting on silence
SILENCE_DBFS_THRESHOLD = -30    # Silence threshold in dBFS
MAX_DURATION_MS = 10 * 60 * 1000  # Max chunk length in milliseconds, 10m
MAX_DURATION_S = 10 * 60 # Max chunk length in seconds, 10m
SEEK_LENGTH = 100 # miliseconds. for silence detection, the scan interval

logger = get_child_logger("audio_processing")

def detect_boundaries(audio_file: Path, model_size: str = 'tiny', language=None) -> List[Dict[str, float]]:
    """
    Use Whisper to detect sentence boundaries in the audio file.

    Args:
        audio_file (Path): Path to the audio file.
        model_size (str): Whisper model size (e.g., 'tiny', 'base', 'small').

    Returns:
        List[Dict[str, float]]: List of timestamps with sentence boundaries. Each entry contains:
            - "start": Start time of the sentence (in seconds).
            - "end": End time of the sentence (in seconds).
            - "text": Sentence text.
    """
    # Load the Whisper model
    logger.info("Loading model...")
    model = whisper.load_model(model_size)
    logger.info(f"Model '{model_size}' loaded.")

    # Transcribe the audio file
    logger.info(f"Transcribing with language: {language or 'auto-detected (default: en)'}")
    logger.info("Transcribing preliminary text...")
    if language:
        result = model.transcribe(str(audio_file), task="transcribe", word_timestamps=True, language="vi")
    else:
        result = model.transcribe(str(audio_file), task="transcribe", word_timestamps=True, language="en")
    logger.info("Intial transcription for boundaries generated.")
    
    # Extract sentence boundaries from segments
    sentence_boundaries = []
    for segment in result['segments']:
        sentence_boundaries.append({
            "start": segment['start'],
            "end": segment['end'],
            "text": segment['text']
        })
    
    return sentence_boundaries

def split_audio_at_boundaries(
        audio_file: Path, 
        boundaries: List[Dict[str, float]], 
        output_dir: Path  = None, 
        max_duration: int = MAX_DURATION_S) -> Path:
    """
    Split the audio file into chunks close to a specified duration while respecting boundaries.

    Args:
        audio_file (Path): Path to the audio file.
        boundaries (List[Dict[str, float]]): List of boundaries with start and end times.
        output_dir (Path): Directory to save the chunks.
        max_duration (int): Maximum duration for each chunk in seconds (default is 10 minutes).

    Returns:
        Path: Path to the directory containing the chunks.
    """
    # Load the audio file
    audio = AudioSegment.from_file(audio_file)
    
    # Create output directory based on filename
    if output_dir is None:
        output_dir = audio_file.parent / f"{audio_file.stem}_chunks"
    output_dir.mkdir(parents=True, exist_ok=True) 

    logger.info(f"Split audio at boundaries max_duration: {max_duration}")   
    # Initialize variables
    current_chunk = AudioSegment.empty()
    current_start = boundaries[0]["start"]
    chunk_count = 1

    for i, boundary in enumerate(boundaries):
        # Calculate segment duration
        segment_start_ms = boundary["start"] * 1000
        segment_end_ms = boundary["end"] * 1000
        segment = audio[segment_start_ms:segment_end_ms]
        
        # Add segment to the current chunk if it fits
        if len(current_chunk) + len(segment) <= max_duration * 1000:
            current_chunk += segment
        else:
            # Export the current chunk
            chunk_path = output_dir / f"chunk_{chunk_count}.mp3"
            current_chunk.export(chunk_path, format="mp3")
            logger.info(f"Exported: {chunk_path}")
            
            # Start a new chunk
            chunk_count += 1
            current_chunk = segment
            current_start = boundary["start"]
    
    # Export the final chunk
    if len(current_chunk) > 0:
        chunk_path = output_dir / f"chunk_{chunk_count}.mp3"
        current_chunk.export(chunk_path, format="mp3")
        logger.info(f"Exported: {chunk_path}")

    return output_dir

def split_audio_on_silence(
    audio_file: Path,
    output_dir: Path = None,
    min_silence_len: int = MIN_SILENCE_LENGTH,  # Silence threshold in milliseconds
    silence_thresh: int = SILENCE_DBFS_THRESHOLD,    # Silence threshold in dBFS
    max_duration: int = MAX_DURATION_MS  # Max chunk length in milliseconds
) -> Path:
    """
    Test to split an audio file into chunks based on silence detection.

    Args:
        audio_file (Path): Path to the audio file.
        output_dir (Path): Directory to save the audio chunks. Defaults to a subdirectory of the input file.
        min_silence_len (int): Minimum silence length to consider a split point 
        silence_thresh (int): Silence threshold in dBFS 
        max_duration (int): Maximum length of any chunk 
    Returns:
        Path: Directory containing the audio chunks.
    """
    logger.debug(f"Audio split parameters: min_silence={min_silence_len}, silence_threshold={silence_thresh}, max_duration={MAX_DURATION_MS}")

    # Load the audio file
    logger.debug("loading audio file...")
    audio = AudioSegment.from_file(audio_file)

    # Set up output directory
    if output_dir is None:
        output_dir = audio_file.parent / f"{audio_file.stem}_s_chunks"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Detect nonsilent segments
    logger.debug("starting silence detection...")
    nonsilent_ranges = detect_nonsilent(audio, min_silence_len=min_silence_len, silence_thresh=silence_thresh, seek_step=SEEK_LENGTH)
    logger.debug(f"finished detection: {len(nonsilent_ranges)}")

    # Combine nonsilent ranges to stay below max_chunk_length
    logger.debug("Combining ranges to fit within max_chunk_length...")
    combined_ranges = []
    current_start, current_end = nonsilent_ranges[0]
    for start, end in nonsilent_ranges[1:]:
        # Check if adding the next segment exceeds the max_chunk_length
        if (current_end - current_start) + (end - start) <= max_duration:
            # Extend the current range
            current_end = end
        else:
            # Save the current range and start a new one
            combined_ranges.append((current_start, current_end))
            current_start, current_end = start, end

    # Append the final range
    combined_ranges.append((current_start, current_end))

    logger.debug(f"Combined ranges: {len(combined_ranges)} chunks created.")

    # Export chunks
    logger.info("Exporting chunks")
    chunk_paths = []
    for i, (start, end) in enumerate(combined_ranges):
        chunk = audio[start:end]
        chunk_path = output_dir / f"chunk_{i + 1}.mp3"
        chunk.export(chunk_path, format="mp3")
        logger.info(f"Chunk {i+1} exported.")
        chunk_paths.append(chunk_path)

    return output_dir

### alternative version

MIN_SILENCE_LENGTH = 1000 # ms
SILENCE_DBFS_THRESHOLD = -30
MAX_DURATION_MS = 10 * 60 * 1000
MAX_DURATION_S = 10 * 60
SEEK_LENGTH = 100  # ms

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
    logger.info("Loading Whisper model...")
    model = whisper.load_model(model_size)
    logger.info(f"Model '{model_size}' loaded. Transcribing...")

    if language:
        result = model.transcribe(str(audio_file), task="transcribe", word_timestamps=True, language=language)
    else:
        # default to English if not specified
        result = model.transcribe(str(audio_file), task="transcribe", word_timestamps=True, language="en")

    sentence_boundaries = []
    for segment in result['segments']:
        sentence_boundaries.append(
            Boundary(start=segment['start'], end=segment['end'], text=segment['text'])
        )

    return sentence_boundaries

def detect_silence_boundaries(
    audio_file: Path,
    min_silence_len: int = MIN_SILENCE_LENGTH,
    silence_thresh: int = SILENCE_DBFS_THRESHOLD,
    max_duration: int = MAX_DURATION_MS
) -> List[Boundary]:
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
    max_duration: int = MAX_DURATION_S
) -> Path:
    """
    Split the audio file into chunks based on provided boundaries.

    Args:
        audio_file (Path): The input audio file.
        boundaries (List[Boundary]): Detected boundaries.
        output_dir (Path): Directory to store the resulting chunks.
        max_duration (int): Max chunk length in seconds.

    Returns:
        Path: Directory containing the chunked audio files.
    
    Example:
        >>> boundaries = [Boundary(0.0,30.0,"..."), Boundary(30.0,60.0,"...")]
        >>> out_dir = split_audio_at_boundaries(Path("my_audio.mp3"), boundaries)
    """
    audio = AudioSegment.from_file(audio_file)
    if output_dir is None:
        output_dir = audio_file.parent / f"{audio_file.stem}_chunks"
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Splitting audio with max_duration={max_duration} seconds")

    current_chunk = AudioSegment.empty()
    chunk_count = 1

    for boundary in boundaries:
        seg_start_ms = int(boundary.start * 1000)
        seg_end_ms = int(boundary.end * 1000)
        segment = audio[seg_start_ms:seg_end_ms]

        if len(current_chunk) + len(segment) <= max_duration * 1000:
            current_chunk += segment
        else:
            chunk_path = output_dir / f"chunk_{chunk_count}.mp3"
            current_chunk.export(chunk_path, format="mp3")
            logger.info(f"Exported: {chunk_path}")
            chunk_count += 1
            current_chunk = segment

    # Export the final chunk if present
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
    max_duration_s: int = MAX_DURATION_S,
    max_duration_ms: int = MAX_DURATION_MS
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
    if method == "whisper":
        boundaries = detect_whisper_boundaries(audio_file, model_size=model_size, language=language)
    elif method == "silence":
        boundaries = detect_silence_boundaries(audio_file, 
                                               min_silence_len=min_silence_len, 
                                               silence_thresh=silence_thresh, 
                                               max_duration=max_duration_ms)
    else:
        raise ValueError(f"Unknown method: {method}. Must be 'silence' or 'whisper'.")

    return split_audio_at_boundaries(audio_file, boundaries, output_dir=output_dir, max_duration=max_duration_s)