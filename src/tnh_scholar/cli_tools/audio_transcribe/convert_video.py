# convert_video.py
# routines to convert video input files to audio

import subprocess
from pathlib import Path
from typing import Dict, Optional

from tnh_scholar.logging_config import get_child_logger

logger = get_child_logger(__name__)


FFMPEG_VIDEO_CONV_DEFAULT_CONFIG = {
    "audio_codec": "libmp3lame",
    "audio_bitrate": "192k",
    "audio_samplerate": "44100",
}

def convert_video_to_audio(
    video_file: Path, 
    output_dir: Path,
    conversion_params: Optional[Dict[str, str]] = None
) -> Path:
    """
    Convert a video file to an audio file using ffmpeg.
    
    Args:
        video_file: Path to the video file
        output_dir: Directory to save the converted audio file
        conversion_params: Optional dictionary to override default conversion parameters
        
    Returns:
        Path to the converted audio file
    """
    output_file = output_dir / f"{video_file.stem}.mp3"

    if output_file.exists():
        logger.info(f"Audio file already exists: {output_file}")
        return output_file

    # Merge default config with any supplied parameters
    params = {**FFMPEG_VIDEO_CONV_DEFAULT_CONFIG}
    if conversion_params:
        params |= conversion_params

    logger.info(f"Converting video to audio: {video_file} -> {output_file}")
    logger.debug(f"Using conversion parameters: {params}")

    try:
        cmd = [
            "ffmpeg", 
            "-i", str(video_file),
            "-vn",
            "-acodec", params["audio_codec"],
            "-ab", params["audio_bitrate"],
            "-ar", params["audio_samplerate"],
            "-y",  # Overwrite output file if it exists
            str(output_file)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f"Conversion successful: {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        logger.error(f"Conversion failed: {e.stderr.decode() if e.stderr else str(e)}")
        raise RuntimeError(f"Failed to convert video: {video_file}") from e