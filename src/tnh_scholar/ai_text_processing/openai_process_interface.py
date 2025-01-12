from typing import Optional
from tnh_scholar.ai_text_processing.typing import ResponseFormat
from tnh_scholar.logging_config import get_child_logger


logger = get_child_logger("openai_text_processing")

TOKEN_BUFFER = 500

from tnh_scholar.openai_interface import (
    token_count, 
    run_single_batch, 
    run_immediate_completion_simple, 
    get_completion_object, 
    get_completion_content
)

def openai_process_text(
    text_input: str, 
    process_instructions: str, 
    model: Optional[str] = None, 
    response_format: Optional[ResponseFormat] = None, 
    batch: bool = False, 
    max_tokens: int =0
    ):
    """postprocessing a transcription."""

    user_prompts = [text_input]
    system_message = process_instructions

    if max_tokens == 0:
        tokens = token_count(text_input)
        max_tokens = tokens + TOKEN_BUFFER

    model_name = model or "default"
    
    logger.info(f"Open AI Text Processing{' as batch process' if batch else ''} with model '{model_name}' started...")

    if batch:
        return _run_batch_process_text(
            response_format, user_prompts, system_message, max_tokens
        )
    completion = run_immediate_completion_simple(system_message, text_input, max_tokens=max_tokens, response_format=response_format)
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
        logger.warning(f"Response object can't be processed in batch mode. Response format ignored:\n\t{response_format}")
    description = "Processing batch: processing text."

    response_list = run_single_batch(user_prompts, system_message, max_token_list=[max_tokens], description=description)
    process_text = response_list[0]
    logger.info("Processing completed.")
    return process_text