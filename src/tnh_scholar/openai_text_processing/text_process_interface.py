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

def process_text(text_input, process_instructions: str, response_object=None, batch=False, max_tokens=0):
    """postprocessing a transcription."""

    user_prompts = [text_input]
    system_message = process_instructions

    if max_tokens == 0:
        tokens = token_count(text_input)
        max_tokens = tokens + TOKEN_BUFFER

    logger.info(f"Processing{' as batch process' if batch else ''} started...")

    output_text = ""
    if batch:
        return _run_batch_process_text(
            response_object, user_prompts, system_message, max_tokens
        )
    completion = run_immediate_completion_simple(system_message, text_input, max_tokens=max_tokens, response_object=response_object)
    logger.debug(f"Full completion:\n{completion}")
    if response_object:
        process_object = get_completion_object(completion) 
        logger.info("Processing completed.")
        return process_object
    else:
        process_text = get_completion_content(completion)
        logger.info("Processing completed.")
        return process_text

def _run_batch_process_text(response_object, user_prompts, system_message, max_tokens):
    if response_object:
        logger.warning(f"Response object can't be processed in batch mode. Response object ignored:\n\t{response_object}")
    description = "Processing batch: processing text."

    response_list = run_single_batch(user_prompts, system_message, max_token_list=[max_tokens], description=description)
    process_text = response_list[0]
    logger.info("Processing completed.")
    return process_text