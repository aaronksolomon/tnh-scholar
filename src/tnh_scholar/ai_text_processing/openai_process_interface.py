from typing import Optional, Type, Union

from pydantic import BaseModel

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.openai_interface import (
    get_completion_content,
    get_completion_object,
    run_immediate_completion_simple,
    run_single_batch,
    token_count,
)

logger = get_child_logger(__name__)

TOKEN_BUFFER = 500

def openai_process_text(
    text_input: str,
    process_instructions: str,
    model: Optional[str] = None,
    response_format: Optional[Type[BaseModel]] = None,
    batch: bool = False,
    max_tokens: int = 0,
) -> Union[BaseModel, str]:
    """postprocessing a transcription."""

    user_prompts = [text_input]
    system_message = process_instructions

    logger.debug(f"OpenAI Process Text with process instructions:\n{system_message}")
    if max_tokens == 0:
        tokens = token_count(text_input)
        max_tokens = tokens + TOKEN_BUFFER

    model_name = model or "default"

    logger.info(
        f"Open AI Text Processing{' as batch process' if batch else ''} "
        f"with model '{model_name}' initiated.\n"
        f"Requesting a maximum of {max_tokens} tokens."
    )

    if batch:
        return _run_batch_process_text(
            response_format, user_prompts, system_message, max_tokens
        )
    completion = run_immediate_completion_simple(
        system_message,
        text_input,
        max_tokens=max_tokens,
        response_format=response_format,
    )
    logger.debug(f"Full completion:\n{completion}")
    if response_format:
        process_object = get_completion_object(completion)
        logger.info("Processing completed.")
        return process_object
    else:
        process_text = get_completion_content(completion)
        logger.info("Processing completed.")
        return process_text


def _run_batch_process_text(response_format, user_prompts, system_message, max_tokens):
    if response_format:
        logger.warning(
            f"Response object can't be processed in batch mode. "
            f"Response format ignored:\n\t{response_format}"
        )
    description = "Processing batch: processing text."

    response_list = run_single_batch(
        user_prompts,
        system_message,
        max_token_list=[max_tokens],
        description=description,
    )
    process_text = response_list[0]
    logger.info("Processing completed.")
    return process_text
