import json
import warnings
from pathlib import Path

from openai.types.audio.transcription_verbose import TranscriptionVerbose

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.openai_interface import run_transcription_speech

logger = get_child_logger(__name__)


def custom_to_json(transcript: TranscriptionVerbose) -> str:
    """
    Custom JSON conversion function to handle problematic float values from Open AI API interface.

    Args:
        transcript (Any): Object from OpenAI API's transcription.

    Returns:
        str: JSON string with problematic values fixed.
    """
    logger.debug("Entered custom_to_json function.")
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
                        logger.debug(
                            "Known UserWarning in OPENAI .to_dict() float serialization caught and ignored."
                        )
                    else:
                        logger.warning(
                            f"Unexpected warning during to_dict(): {warning_msg}"
                        )
    except Exception as e:
        logger.error(f"Error during to_dict(): {e}", exc_info=True)
        return json.dumps({})  # Return an empty JSON as a fallback

    # Traverse the dictionary to convert problematic floats to strings
    for key, value in data.items():
        if isinstance(value, float):  # Handle floats
            data[key] = float(f"{value:.18f}")

    # Serialize the cleaned dictionary back to JSON
    logger.debug("Dumping json in custom_to_json...")
    return json.dumps(data)


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

    return "\n".join(segment.text.strip() for segment in transcript.segments)


def get_transcription(
    file: Path, model: str, prompt: str, jsonl_out, mode="transcribe"
):
    logger.info(
        f"Speech transcript parameters: file={file}, model={model}, response_format=verbose_json, mode={mode}\n\tprompt='{prompt}'"
    )
    transcript = run_transcription_speech(
        file, model=model, response_format="verbose_json", prompt=prompt, mode=mode
    )

    # Use the custom_to_json function
    json_output = custom_to_json(transcript)
    logger.debug(f"Serialized JSON output excerpt: {json_output[:1000]}...")

    # Write the serialized JSON to the JSONL file
    jsonl_out.write(json_output + "\n")

    return get_text_from_transcript(transcript)


def process_audio_chunks(
    directory: Path,
    output_file: Path,
    jsonl_file: Path,
    model: str = "whisper-1",
    prompt: str = "",
    translate: bool = False,
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
        key=lambda f: int(f.stem.split("_")[1]),  # Extract the number from 'chunk_X'
    )

    if not audio_files:
        raise FileNotFoundError(f"No audio files found in the directory: {directory}")

    # log files to process:
    audio_file_names = [file.name for file in audio_files]  # get strings for logging
    audio_file_name_str = "\n\t".join(audio_file_names)
    audio_file_count = len(audio_file_names)
    logger.info(
        f"{audio_file_count} audio files found in {directory}:\n\t{audio_file_name_str}"
    )

    # Initialize the output content
    stitched_transcription = []

    # Open the JSONL file for writing
    with jsonl_file.open("w", encoding="utf-8") as jsonl_out:
        # Process each audio chunk
        for audio_file in audio_files:
            logger.info(f"Processing {audio_file.name}...")
            try:
                if translate:
                    text = get_transcription(
                        audio_file, model, prompt, jsonl_out, mode="translate"
                    )
                else:
                    text = get_transcription(
                        audio_file, model, prompt, jsonl_out, mode="transcribe"
                    )

                stitched_transcription.append(text)

            except Exception as e:
                logger.error(f"Error processing {audio_file.name}: {e}", exc_info=True)
                raise e

    # Write the stitched transcription to the output file
    with output_file.open("w", encoding="utf-8") as out_file:
        out_file.write(" ".join(stitched_transcription))

    logger.info(f"Stitched transcription saved to {output_file}")
    logger.info(f"Full transcript objects saved to {jsonl_file}")


def process_audio_file(
    audio_file: Path,
    output_file: Path,
    jsonl_file: Path,
    model: str = "whisper-1",
    prompt: str = "",
    translate: bool = False,
) -> None:
    """
    Processes a single audio file using OpenAI's transcription API,
    saves the transcription objects into a JSONL file.

    Args:
        audio_file (Path): Path to the the audio file for processing
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

    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file {audio_file} not found.")
    else:
        logger.info(f"Audio file found: {audio_file}")

    # Open the JSONL file for writing
    with jsonl_file.open("w", encoding="utf-8") as jsonl_out:
        logger.info(f"Processing {audio_file.name}...")
        try:
            if translate:
                text = get_transcription(
                    audio_file, model, prompt, jsonl_out, mode="translate"
                )
            else:
                text = get_transcription(
                    audio_file, model, prompt, jsonl_out, mode="transcribe"
                )
        except Exception as e:
            logger.error(f"Error processing {audio_file.name}: {e}", exc_info=True)
            raise e

    # Write the stitched transcription to the output file
    with output_file.open("w", encoding="utf-8") as out_file:
        out_file.write(text)

    logger.info(f"Transcription saved to {output_file}")
    logger.info(f"Full transcript objects saved to {jsonl_file}")
