from typing import Optional, Type, Union

from pydantic import BaseModel

from tnh_scholar.gen_ai_service.adapters.simple_completion import simple_completion
from tnh_scholar.gen_ai_service.utils.token_utils import token_count
from tnh_scholar.logging_config import get_child_logger

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
            user_prompts, system_message, max_tokens, model_name, response_format
        )

    completion_result = simple_completion(
        system_message=system_message,
        user_message=text_input,
        model=model,
        max_tokens=max_tokens,
        response_model=response_format,
    )
    logger.info("Processing completed.")
    return completion_result


def _run_batch_process_text(user_prompts, system_message, max_tokens, model_name, response_format):
    if response_format:
        logger.warning(
            f"Response object can't be processed in batch mode. "
            f"Response format ignored:\n\t{response_format}"
        )
    logger.info(
        "Processing batch sequentially via simple_completion (temporary migration fallback)."
    )
    responses = []
    for idx, prompt in enumerate(user_prompts):
        logger.debug("Processing batch item %s/%s", idx + 1, len(user_prompts))
        response = simple_completion(
            system_message=system_message,
            user_message=prompt,
            model=model_name,
            max_tokens=max_tokens,
        )
        responses.append(response)

    logger.info("Processing completed.")
    return responses[0] if responses else ""
