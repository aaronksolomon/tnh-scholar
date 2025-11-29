import os
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from git import Optional
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

from tnh_scholar.audio_processing.whisper_security import load_whisper_model
from tnh_scholar.logging_config import get_child_logger

# Define constants
MAX_INT16 = 32768.0  # Maximum absolute value for 16-bit signed integer audio
MIN_SILENCE_LENGTH = 1000  # 1 second in ms, for splitting on silence
SILENCE_DBFS_THRESHOLD = -30  # Silence threshold in dBFS
MAX_DURATION_MS = 10 * 60 * 1000  # Max chunk length in milliseconds, 10m
MAX_DURATION = 10 * 60  # Max chunk length in seconds, 10m
SEEK_LENGTH = 50  # milliseconds. for silence detection, the scan interval
EXPECTED_TIME_FACTOR = 0.45  # a heuristic to scale expected time

logger = get_child_logger("audio_processing")


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
    audio_file: Path, model_size: str = "tiny", language: str = None
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

    os.environ["KMP_WARNINGS"] = "0"  # Turn of OMP warning message

    # Load model
    logger.info("Loading Whisper model...")
    model = load_whisper_model(model_size)
    logger.info(f"Model '{model_size}' loaded.")

    if language:
        logger.info(f"Language for boundaries set to '{language}'")
    else:
        logger.info("Language not set. Autodetect will be used in Whisper model.")

    # with TimeProgress(expected_time=expected_time, desc="Generating transcription boundaries"):
    boundary_transcription = whisper_model_transcribe(
        model,
        str(audio_file),
        task="transcribe",
        word_timestamps=True,
        language=language,
        verbose=False,
    )

    sentence_boundaries = [
        Boundary(start=segment["start"], end=segment["end"], text=segment["text"])
        for segment in boundary_transcription["segments"]
    ]
    return sentence_boundaries, boundary_transcription


def detect_silence_boundaries(
    audio_file: Path,
    min_silence_len: int = MIN_SILENCE_LENGTH,
    silence_thresh: int = SILENCE_DBFS_THRESHOLD,
    max_duration: int = MAX_DURATION_MS,
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
    logger.debug(
        f"Detecting silence boundaries with min_silence={min_silence_len}, silence_thresh={silence_thresh}"
    )

    audio = AudioSegment.from_file(audio_file)
    nonsilent_ranges = detect_nonsilent(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        seek_step=SEEK_LENGTH,
    )

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

    return [
        Boundary(start=start_ms / 1000.0, end=end_ms / 1000.0, text="")
        for start_ms, end_ms in combined_ranges
    ]

def split_audio_at_boundaries(
    audio_file: Path,
    boundaries: List[Boundary],
    output_dir: Path = None,
    max_duration: int = MAX_DURATION,
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
            segment_end_ms = int(
                boundaries[idx + 1].start * 1000
            )  # Next boundary's start
        else:
            segment_end_ms = len(audio)  # End of the audio for the last boundary

        # Adjust for the first segment starting at 0
        if idx == 0 and segment_start_ms > 0:
            segment_start_ms = 0  # Ensure we include the very beginning of the audio

        segment = audio[segment_start_ms:segment_end_ms]

        logger.debug(
            f"Boundary index: {idx}, segment_start: {segment_start_ms / 1000}, segment_end: {segment_end_ms / 1000}, duration: {segment.duration_seconds}"
        )
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
    output_dir: Optional[Path] = None,
    model_size: str = "tiny",
    language: str = None,
    min_silence_len: int = MIN_SILENCE_LENGTH,
    silence_thresh: int = SILENCE_DBFS_THRESHOLD,
    max_duration: int = MAX_DURATION,
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
        max_duration (int): Max chunk length in seconds (also used to derive ms threshold).

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
        boundaries, _ = detect_whisper_boundaries(
            audio_file, model_size=model_size, language=language
        )

    elif method == "silence":
        max_duration_ms = (
            max_duration * 1000
        )  # convert duration in seconds to milliseconds
        boundaries = detect_silence_boundaries(
            audio_file,
            min_silence_len=min_silence_len,
            silence_thresh=silence_thresh,
            max_duration=max_duration_ms,
        )
    else:
        raise ValueError(f"Unknown method: {method}. Must be 'silence' or 'whisper'.")

    # delete all files in the output_dir (this is useful for reprocessing)

    return split_audio_at_boundaries(
        audio_file, boundaries, output_dir=output_dir, max_duration=max_duration
    )


# def estimate_transcription_time(
#     audio_file: Path,
#     model,
#     language: str | None = None,
#     sample_duration: int = 60
# ) -> float:
#     """
#     Estimate how long it might take to transcribe the entire audio file using
#     a Whisper model by sampling a small chunk (e.g. 60 seconds) in the middle
#     and timing the transcription.

#     Args:
#         audio_file (Path): Path to the audio file.
#         model: The Whisper model.
#         language (Optional[str]): If known, specify a language code to skip detection
#                                   (e.g. "en", "vi"). Otherwise, None for auto-detect.
#         sample_duration (int): Length of audio (in seconds) to sample and time
#                                for the estimate.

#     Returns:
#         float: Estimated total transcription time in seconds.

#     Example:
#         >>> total_time_est = estimate_transcription_time(Path("example.mp3"), "tiny", "en", 60)
#         >>> print(f"Estimated full transcription time: {total_time_est:.2f} sec")
#     """
#     # 1) Load entire audio to get total length in ms
#     audio = AudioSegment.from_file(audio_file)
#     total_length_ms = len(audio)
#     total_length_sec = total_length_ms / 1000.0

#     # 2) Extract a 60-second chunk from the "middle"
#     #    If the audio is shorter than sample_duration, we just sample the entire file
#     if total_length_sec <= sample_duration:
#         sample_audio = audio
#     else:
#         middle_ms = total_length_ms / 2
#         half_sample_ms = sample_duration * 1000 / 2
#         start_ms = max(0, middle_ms - half_sample_ms)
#         end_ms = min(total_length_ms, middle_ms + half_sample_ms)
#         sample_audio = audio[start_ms:end_ms]

#     # 3) Convert the chunk to a NumPy array
#     audio_array = audio_to_numpy(sample_audio)

#     # 4) Time the transcription of just this chunk
#     start_time = time.time()

#     # Force language if provided, or let Whisper auto-detect otherwise
#     transcribe_kwargs = {"language": language} if language else {}

#     whisper_model_transcribe(model, audio_array, **transcribe_kwargs)

#     elapsed_chunk_time = time.time() - start_time

#     # 5) Scale up by ratio
#     #    (If 60s chunk took X seconds to transcribe, we guess that full_length_seconds
#     #     will take (full_length_seconds / sample_duration) * X .)
#     if total_length_sec > sample_duration:
#         scale_factor = total_length_sec / sample_duration
#     else:
#         scale_factor = 1.0

#     return elapsed_chunk_time * scale_factor


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
    *args: Any,
    **kwargs: Any,
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

    # class StdoutFilter(io.StringIO):
    #     def __init__(self, original_stdout):
    #         super().__init__()
    #         self.original_stdout = original_stdout

    #     def write(self, message):
    #         # Suppress specific messages like 'OMP:' while allowing others
    #         if "OMP:" not in message:
    #             self.original_stdout.write(message)

    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="FP16 is not supported on CPU; using FP32 instead",
            category=UserWarning,
        )

        # Redirect stdout to suppress OMP messages
        # original_stdout = sys.stdout
        # sys.stdout = filtered_stdout

        try:
            # Convert Path to str if needed
            if isinstance(input_source, Path):
                input_source = str(input_source)

            # Call the original transcribe function
            return model.transcribe(input_source, *args, **kwargs)
        finally:
            # Restore original stdout
            # sys.stdout = original_stdout
            pass
