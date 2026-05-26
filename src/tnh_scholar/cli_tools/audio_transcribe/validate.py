from pathlib import Path

_NO_ACTIONS_MESSAGE = (
    "No actions requested. At least one of --yt_download, --split, --transcribe, or --full must be set."
)
_TRANSCRIBE_WITHOUT_CHUNKS_MESSAGE = (
    "Transcription requested without splitting or downloading and "
    "no_chunks=False. Must provide --chunk_dir with pre-split chunks."
)
_BOUNDARY_FLAGS_WITHOUT_SPLIT_MESSAGE = (
    "Boundary detection flags given but splitting is not requested. Remove these flags or enable --split."
)
_NO_BOUNDARY_METHOD_MESSAGE = (
    "No boundary method selected for splitting. Enable either whisper or silence boundaries."
)


def validate_inputs(
    is_download: bool,
    yt_url: str | None,
    yt_url_list: Path | None,
    audio_file: Path | None,
    split: bool,
    transcribe: bool,
    chunk_dir: Path | None,
    no_chunks: bool,
    silence_boundaries: bool,
    whisper_boundaries: bool,
) -> None:
    """Validate the CLI inputs for coherent download, split, and transcribe flows."""
    _validate_requested_actions(is_download, split, transcribe)
    _validate_download_inputs(is_download, yt_url, yt_url_list)
    _validate_local_input_requirements(
        is_download=is_download,
        audio_file=audio_file,
        split=split,
        transcribe=transcribe,
        chunk_dir=chunk_dir,
        no_chunks=no_chunks,
    )
    _validate_no_chunks_constraints(split=split, chunk_dir=chunk_dir, no_chunks=no_chunks)
    _validate_boundary_flags(
        split=split,
        silence_boundaries=silence_boundaries,
        whisper_boundaries=whisper_boundaries,
    )


def _validate_requested_actions(is_download: bool, split: bool, transcribe: bool) -> None:
    if is_download or split or transcribe:
        return
    raise ValueError(_NO_ACTIONS_MESSAGE)


def _validate_download_inputs(
    is_download: bool,
    yt_url: str | None,
    yt_url_list: Path | None,
) -> None:
    if not is_download:
        return
    if yt_url and yt_url_list:
        raise ValueError("Both --yt_process_url and --yt_process_url_list provided. Only one allowed.")
    if yt_url or yt_url_list:
        return
    raise ValueError(
        "When --yt_download is specified, you must provide --yt_process_url or --yt_process_url_list."
    )


def _validate_local_input_requirements(
    *,
    is_download: bool,
    audio_file: Path | None,
    split: bool,
    transcribe: bool,
    chunk_dir: Path | None,
    no_chunks: bool,
) -> None:
    if is_download:
        return
    if split and audio_file is None:
        raise ValueError(
            "Splitting requested but no audio file provided and no YouTube download source available."
        )
    if not transcribe or split:
        return
    if no_chunks:
        if audio_file is None:
            raise ValueError("Transcription requested with no_chunks=True but no audio file provided.")
        return
    if chunk_dir is None:
        raise ValueError(_TRANSCRIBE_WITHOUT_CHUNKS_MESSAGE)


def _validate_no_chunks_constraints(
    *,
    split: bool,
    chunk_dir: Path | None,
    no_chunks: bool,
) -> None:
    if not no_chunks:
        return
    if split:
        raise ValueError("Cannot use --no_chunks and --split together. Choose one option.")
    if chunk_dir is not None:
        raise ValueError("Cannot specify --chunk_dir when --no_chunks is set.")


def _validate_boundary_flags(
    *,
    split: bool,
    silence_boundaries: bool,
    whisper_boundaries: bool,
) -> None:
    if not split:
        if silence_boundaries or whisper_boundaries:
            raise ValueError(_BOUNDARY_FLAGS_WITHOUT_SPLIT_MESSAGE)
        return
    if silence_boundaries and whisper_boundaries:
        raise ValueError("Cannot use both --silence_boundaries and --whisper_boundaries simultaneously.")
    if silence_boundaries or whisper_boundaries:
        return
    raise ValueError(_NO_BOUNDARY_METHOD_MESSAGE)
