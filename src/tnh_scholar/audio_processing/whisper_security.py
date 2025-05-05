import contextlib
from functools import partial
from typing import Any, Generator

import torch

from tnh_scholar.logging_config import get_child_logger

logger = get_child_logger(__name__)


@contextlib.contextmanager
def safe_torch_load(weights_only: bool = True) -> Generator[None, None, None]:
    """
    Context manager that temporarily modifies torch.load 
    to use weights_only=True by default.

    This addresses the FutureWarning in PyTorch regarding pickle security:
    https://github.com/pytorch/pytorch/blob/main/SECURITY.md#untrusted-models

    Args:
        weights_only: If True, limits unpickling to tensor data only.

    Yields:
        None

    Example:
        >>> with safe_torch_load():
        ...     model = whisper.load_model("tiny")
    """
    original_torch_load = torch.load
    try:
        torch.load = partial(original_torch_load, weights_only=weights_only)
        logger.debug("Modified torch.load to use weights_only=%s", weights_only)
        yield
    finally:
        torch.load = original_torch_load
        logger.debug("Restored original torch.load")


def load_whisper_model(model_name: str) -> Any:
    """
    Safely load a Whisper model with security best practices.

    Args:
        model_name: Name of the Whisper model to load (e.g., "tiny", "base", "small")

    Returns:
        Loaded Whisper model

    Raises:
        RuntimeError: If model loading fails
    """
    import whisper

    try:
        with safe_torch_load():
            model = whisper.load_model(model_name)
        return model
    except Exception as e:
        logger.error("Failed to load Whisper model %r: %s", model_name, e)
        raise RuntimeError(f"Failed to load Whisper model: {e}") from e


# Usage example:
# if __name__ == "__main__":
#    model = load_whisper_model("tiny")
