from io import BytesIO
from typing import Any, BinaryIO, Dict, Optional

# Allowed audio file extensions for Whisper/OpenAI API
_ALLOWED_EXTENSIONS = [
    "mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm", "ogg", "flac", "aac", "wma", "opus"
]


def patch_file_with_name(file_obj: BytesIO, extension: str) -> BinaryIO:
    """
    Ensures the file-like object has a .name attribute with the correct extension.
    """
    file_obj.name = f"filename_placeholder.{extension}"
    return file_obj

def patch_whisper_options(
    options: Optional[Dict[str, Any]],
    file_extension: str
    ) -> Dict[str, Any]:
    """
    Patch routine to ensure 'file_extension' is present in transcription options dict.
    This is a workaround for OpenAI Whisper API, which requires file-like objects to have a
    filename/extension. Only allows known audio extensions.

    Args:
        options: Transcription options dictionary (will not be mutated)
        file_extension: File extension string (with or without leading dot)

    Returns:
        New options dictionary with 'file_extension' set appropriately

    Raises:
        ValueError: If file_extension is not in the allowed list
    """
    patched = dict(options) if options is not None else {}
    ext = file_extension.lstrip('.')
    if ext.lower() not in _ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file extension '{ext}'. Allowed extensions: {_ALLOWED_EXTENSIONS}"
        )
    patched['file_extension'] = ext
    return patched
    