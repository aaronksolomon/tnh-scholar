import json
import warnings
from pathlib import Path

from openai.types.audio.transcription_verbose import TranscriptionVerbose

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.openai_interface import run_transcription_speech

logger = get_child_logger(__name__)

def custom_to_json(transcript: TranscriptionVerbose) -> str:
    """
    Custom JSON conversion function to handle 
    problematic float values from Open AI API interface.

    Args:
        transcript (Any): Object from OpenAI API's transcription.

    Returns:
        str: JSON string with problematic values fixed.
    """
    logger.debug("Entered custom_to_json function.")

    data = _handle_open_ai_json(transcript)
    
    # Traverse the dictionary to convert problematic floats to strings
    for key, value in data.items():
        if isinstance(value, float):  # Handle floats
            data[key] = float(f"{value:.18f}")

    # Serialize the cleaned dictionary back to JSON
    logger.debug("Dumping json in custom_to_json...")
    return json.dumps(data)

def _handle_open_ai_json(transcript: TranscriptionVerbose):
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
        return data
    except Exception as e:
        logger.error(f"Error during to_dict(): {e}", exc_info=True)
        return {}  # Return an empty dict as a fallback

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
    audio_file: Path, model: str, prompt: str, jsonl_out, mode="transcribe"
):
    logger.info(
        f"Speech transcript parameters: file={audio_file}, model={model}\n"
        f"response_format=verbose_json, mode={mode}\n"
        f"\tprompt='{prompt}'"
    )
    transcript = run_transcription_speech(
        audio_file, model=model, response_format="verbose_json", prompt=prompt, mode=mode
    )

    # Use the custom_to_json function
    json_output = custom_to_json(transcript)
    logger.debug(f"Serialized JSON output excerpt: {json_output[:1000]}...")

    # Write the serialized JSON to the JSONL file
    jsonl_out.write(json_output + "\n")

    return get_text_from_transcript(transcript)