import yt_dlp
from pathlib import Path
from pydub import AudioSegment
from openai import OpenAI
from openai.types.audio.transcription_verbose import TranscriptionVerbose
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import whisper
import logging
from typing import List, Dict, Any
import json
import csv
import warnings
from src.logging_config import get_child_logger

MIN_SILENCE_LENGTH = 1000 # 1 second in ms, for splitting on silence
SILENCE_DBFS_THRESHOLD = -30    # Silence threshold in dBFS
MAX_DURATION_MS = 10 * 60 * 1000  # Max chunk length in milliseconds, 10m
MAX_DURATION_S = 10 * 60 # Max chunk length in seconds, 10m
SEEK_LENGTH = 100 # miliseconds. for silence detection, the scan interval
TOKEN_BUFFER = 500   # additional tokens to request as a buffer when parsing text.

from tnh_scholar.gpt_processing import (
    run_transcription_speech, 
    token_count, 
    run_immediate_completion_simple, 
    run_single_batch, 
    get_completion_content, 
    get_completion_object
)

from tnh_scholar.text_processing import get_text_from_file, write_text_to_file

logger = get_child_logger("video_processing")

def custom_to_json(transcript: Any) -> str:
    """
    Custom JSON conversion function to handle problematic float values.

    Args:
        transcript (Any): Object from OpenAI API's transcription.

    Returns:
        str: JSON string with problematic values fixed.
    """
    logger.debug("Begin custom_to_json function.")
    try:
        # Use warnings.catch_warnings to catch specific warnings
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always", UserWarning)  # Catch all UserWarnings
            data = transcript.to_dict()

            # Check if any warnings were caught
            for warning in caught_warnings:
                if issubclass(warning.category, UserWarning):
                    warning_msg = str(warning.message)
                    if "Expected `str` but got `float`" in warning_msg:
                        logger.warning("Known UserWarning in OPENAI .to_dict() float serialization caught and ignored.")
                    else:
                        logger.warning(f"Unexpected warning during to_dict(): {warning_msg}")
    except Exception as e:
        logger.error(f"Error during to_dict(): {e}", exc_info=True)
        return json.dumps({})  # Return an empty JSON as a fallback

    # Traverse the dictionary to convert problematic floats to strings
    for key, value in data.items():
        if isinstance(value, float):  # Handle floats
            data[key] = float(f"{value:.18f}")
    
    # Serialize the cleaned dictionary back to JSON
    logger.debug("Dumping json in custom_to_json")
    return json.dumps(data)

def get_youtube_urls_from_csv(file_path: Path) -> List[str]:
    """
    Reads a CSV file containing YouTube URLs and titles, logs the titles, 
    and returns a list of URLs.

    Args:
        file_path (Path): Path to the CSV file containing YouTube URLs and titles.

    Returns:
        List[str]: List of YouTube URLs.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the CSV file is improperly formatted.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    urls = []
    
    with file_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        if "url" not in reader.fieldnames or "title" not in reader.fieldnames:
            logger.error("CSV file must contain 'url' and 'title' columns.")
            raise ValueError("CSV file must contain 'url' and 'title' columns.")
        
        for row in reader:
            url = row["url"]
            title = row["title"]
            urls.append(url)
            logger.info(f"Found video title: {title}")
    
    return urls

def download_audio_yt(url: str, output_dir: Path, start_time: str = None) -> Path:
    """
    Downloads audio from a YouTube video using yt_dlp.YoutubeDL, with an optional start time.

    Args:
        url (str): URL of the YouTube video.
        output_dir (Path): Directory to save the downloaded audio file.
        start_time (str): Optional start time (e.g., '00:01:30' for 1 minute 30 seconds).

    Returns:
        Path: Path to the downloaded audio file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'postprocessor_args': [],
        'noplaylist': True,
        'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
    }

    # Add start time to the FFmpeg postprocessor if provided
    if start_time:
        ydl_opts['postprocessor_args'].extend(['-ss', start_time])
        logger.info(f"Postprocessor start time set to: {start_time}")

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(url, download=True)
        downloaded_file = Path(ydl.prepare_filename(result)).with_suffix('.mp3')
        return downloaded_file

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

def get_text_from_transcript(transcript: TranscriptionVerbose) -> str:
    """
    Extracts and combines text from all segments of a transcription.

    Args:
        transcript (TranscriptionVerbose): A transcription object containing segments of text.

    Returns:
        str: A single string with all segment texts concatenated, separated by newlines.

    Raises:
        ValueError: If the transcript object is invalid or missing required attributes.

    Example:
        >>> from openai.types.audio.transcription_verbose import TranscriptionVerbose
        >>> transcript = TranscriptionVerbose(segments=[{"text": "Hello"}, {"text": "world"}])
        >>> get_text_from_transcript(transcript)
        'Hello\nworld'
    """
    logger.debug(f"transcript is type: {type(transcript)}")
    
    text = "\n".join(segment.text.strip() for segment in transcript.segments)
    return text

def get_transcription(file: Path, model: str, prompt: str, jsonl_out, mode="transcribe"):
    logger.info(f"Speech transcript parameters: file={file}, model={model}, response_format=verbose_json, mode={mode}\n\tprompt='{prompt}'")
    transcript = run_transcription_speech(
        file,
        model=model,
        response_format="verbose_json",
        prompt=prompt,
        mode=mode
    )
      
    # Use the custom_to_json function
    json_output = custom_to_json(transcript)
    logger.debug(f"Serialized JSON output: {json_output}")
    
    # Write the serialized JSON to the JSONL file
    jsonl_out.write(json_output + "\n")
    
    # Append the transcribed text to the stitched output
    text = get_text_from_transcript(transcript)
    
    return text

def process_audio_chunks(
    directory: Path, 
    output_file: Path, 
    jsonl_file: Path, 
    model: str = "whisper-1", 
    prompt: str = "",
    translate: bool = False 
) -> None:
    """
    Processes all audio chunks in the specified directory using OpenAI's transcription API,
    saves the transcription objects into a JSONL file, and stitches the transcriptions
    into a single text file.

    Args:
        directory (Path): Path to the directory containing audio chunks.
        output_file (Path): Path to the output file to save the stitched transcription.
        jsonl_file (Path): Path to save the transcription objects as a JSONL file.
        model (str): The transcription model to use (default is "whisper-1").
        prompt (str): Optional prompt to provide context for better transcription.
        translate (bool): Optional flag to translate speech to English (useful if the audio input is not English)
    Raises:
        FileNotFoundError: If no audio chunks are found in the directory.
    """

    # Ensure the output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    jsonl_file.parent.mkdir(parents=True, exist_ok=True)

    # Collect all audio chunks in the directory, sorting numerically by chunk number
    audio_files = sorted(
        directory.glob("*.mp3"),
        key=lambda f: int(f.stem.split('_')[1])  # Extract the number from 'chunk_X'
        )
    
    if not audio_files:
        raise FileNotFoundError(f"No audio files found in the directory: {directory}")
    
    audio_file_info = [str(file) for file in audio_files]  # get strings for logging
    logger.info(f"Audio files found:\n\t{audio_file_info}")

    # Initialize the output content
    stitched_transcription = []

    # Open the JSONL file for writing
    with jsonl_file.open("w", encoding="utf-8") as jsonl_out:
        # Process each audio chunk
        for audio_file in audio_files:
            logger.info(f"Processing {audio_file.name}...")
            try:
                if translate:
                    text = get_transcription(audio_file, model, prompt, jsonl_out, mode="translate")
                else:
                    text = get_transcription(audio_file, model, prompt, jsonl_out, mode="transcribe")

                stitched_transcription.append(text)    

            except Exception as e:
                logger.error(f"Error processing {audio_file.name}: {e}", exc_info=True)
                raise e
                
    # Write the stitched transcription to the output file
    with output_file.open("w", encoding="utf-8") as out_file:
        out_file.write(" ".join(stitched_transcription))

    logger.info(f"Stitched transcription saved to {output_file}")
    logger.info(f"Full transcript objects saved to {jsonl_file}")

def postprocess_text(text_input, postprocess_instructions: str, response_object=None, batch=False, max_tokens=0):
    """postprocessing a transcription."""

    user_prompts = [text_input]
    system_message = postprocess_instructions

    if max_tokens == 0:
        tokens = token_count(text_input)
        max_tokens = tokens + TOKEN_BUFFER

    logger.info(f"Postprocessing{' as batch process' if batch else ''} started.")

    description = f"Video processing batch: postprocessing text."

    output_text = ""
    if batch:
        if response_object:
            logger.warning(f"Response object can't be processed in batch mode. Response object ignored:\n\t{response_object}")
        response_list = run_single_batch(user_prompts, system_message, max_token_list=[max_tokens], description=description)
        output_text = response_list[0]
    else:
        completion = run_immediate_completion_simple(system_message, text_input, max_tokens=max_tokens, response_object=response_object)
        if response_object:
            process_object = get_completion_object(completion)
            logger.debug(f"Full completion:\n{completion}")
            return process_object
        else:
            logger.debug(f"Full completion:\n{completion}")
            process_text = get_completion_content(completion)
            return process_text

        

        