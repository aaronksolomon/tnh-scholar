from pathlib import Path


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
    """
    Validate the CLI inputs to ensure logical consistency given all the flags.

    Conditions & Requirements:
    1. At least one action (yt_download, split, transcribe) should be requested.
       Otherwise, nothing is done, so raise an error.

    2. If yt_download is True:
       - Must specify either yt_process_url OR yt_process_url_list (not both, not none).

    3. If yt_download is False:
       - If split is requested, we need a local audio file (since no download will occur).
       - If transcribe is requested without split and without yt_download:
         - If no_chunks = False, we must have chunk_dir to read existing chunks.
         - If no_chunks = True, we must have a local audio file (direct transcription) or previously downloaded file
           (but since yt_download=False, previously downloaded file scenario doesn't apply here,
           so effectively we need local audio in that scenario).

    4. no_chunks flag:
       - If no_chunks = True, we are doing direct transcription on entire audio without chunking.
         - Cannot use split if no_chunks = True. (Mutually exclusive)
         - chunk_dir is irrelevant if no_chunks = True; since we don't split into chunks,
           requiring a chunk_dir doesn't make sense. If provided, it's not useful, but let's allow it silently
           or raise an error for clarity. It's safer to raise an error to prevent user confusion.

    5. Boundaries flags (silence_boundaries, whisper_boundaries):
       - These flags control how splitting is done.
       - If split = False, these are irrelevant. Not necessarily an error, but could be a no-op.
         For robustness, raise an error if user specifies these without split, to avoid confusion.
       - If split = True and no_chunks = True, that’s contradictory already, so no need for boundary logic there.
       - If split = True, exactly one method should be chosen:
         If both silence_boundaries and whisper_boundaries are True simultaneously or both are False simultaneously,
         we need a clear default or raise an error. By the code snippet logic, whisper_boundaries is default True
         if not stated otherwise. To keep it robust:
           - If both are True, raise error.
           - If both are False, that means user explicitly turned them off or never turned on whisper.
             The code snippet sets whisper_boundaries True by default. If user sets it False somehow,
             we can then default to silence. Just ensure at run-time we have a deterministic method:
             If both are False, we can default to whisper or silence. Let's default to whisper if no flags given.
             However, given the code snippet, whisper_boundaries has a default of True.
             If the user sets whisper_boundaries to False and also does not set silence_boundaries,
             then no method is chosen. Let's then raise an error if both ended up False to avoid ambiguity.

    Raises:
        ValueError: If the input arguments are not logically consistent.
    """

    # 1. Check that we have at least one action
    if not is_download and not split and not transcribe:
        raise ValueError(
            "No actions requested. At least one of --yt_download, --split, --transcribe, or --full must be set."
        )

    # 2. Validate YouTube download logic
    if is_download:
        if yt_url and yt_url_list:
            raise ValueError(
                "Both --yt_process_url and --yt_process_url_list provided. Only one allowed."
            )
        if not yt_url and not yt_url_list:
            raise ValueError(
                "When --yt_download is specified, you must provide --yt_process_url or --yt_process_url_list."
            )

    # 3. Logic when no YouTube download:
    if not is_download:
        # If splitting but no download, need an audio file
        if split and audio_file is None:
            raise ValueError(
                "Splitting requested but no audio file provided and no YouTube download source available."
            )

        if transcribe and not split:
            if no_chunks:
                # Direct transcription, need an audio file
                if audio_file is None:
                    raise ValueError(
                        "Transcription requested with no_chunks=True but no audio file provided."
                    )
            elif chunk_dir is None:
                raise ValueError(
                    "Transcription requested without splitting or downloading and no_chunks=False. Must provide --chunk_dir with pre-split chunks."
                )

    # Check no_chunks scenario:
    # no_chunks and split are mutually exclusive
    # If transcribing but not splitting or downloading:
    # If no_chunks and chunk_dir provided, it doesn't make sense since we won't use chunks at all.
    # 4. no_chunks flag validation:
    # no_chunks=False, we need chunks from chunk_dir
    if no_chunks:
        if split:
            raise ValueError(
                "Cannot use --no_chunks and --split together. Choose one option."
            )
        if chunk_dir is not None:
            raise ValueError("Cannot specify --chunk_dir when --no_chunks is set.")

    # 5. Boundaries flags:
    # If splitting is not requested but boundaries flags are set, it's meaningless.
    # The code snippet defaults whisper_boundaries to True, so if user tries to turn it off and sets silence?
    # We'll require that boundaries only matter if split is True.
    if not split and (silence_boundaries or whisper_boundaries):
        raise ValueError(
            "Boundary detection flags given but splitting is not requested. Remove these flags or enable --split."
        )

    # If split is True, we must have a consistent boundary method:
    if split:
        # If both whisper and silence are somehow True:
        if silence_boundaries and whisper_boundaries:
            raise ValueError(
                "Cannot use both --silence_boundaries and --whisper_boundaries simultaneously."
            )

        # If both are False:
        # Given the original snippet, whisper_boundaries is True by default.
        # For the sake of robustness, let's say if user sets both off, we can't proceed:
        if not silence_boundaries and not whisper_boundaries:
            raise ValueError(
                "No boundary method selected for splitting. Enable either whisper or silence boundaries."
            )

    # If we got here, inputs are logically consistent.
