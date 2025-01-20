import json
import os
import time
from datetime import datetime
from math import floor
from pathlib import Path
from typing import Dict, List, Optional

import tiktoken
from dotenv import load_dotenv
from openai import OpenAI

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils.file_utils import get_text_from_file

MAX_BATCH_LIST = 30
OPEN_AI_DEFAULT_MODEL = "gpt-4o"
DEFAULT_MAX_BATCH_RETRY = 60
DEBUG_DISPLAY_BUFFER = 1000

DEFAULT_MODEL_SETTINGS = {
    "gpt-4o": {"max_tokens": 16000, "context_limit": 128000, "temperature": 1.0},
    "gpt-3.5-turbo": {"max_tokens": 4096, "context_limit": 16384, "temperature": 1.0},
    "gpt-4o-mini": {"max_tokens": 16000, "context_limit": 128000, "temperature": 1.0},
}

# Dictionary of model configurations
open_ai_model_settings = DEFAULT_MODEL_SETTINGS

open_ai_encoding = tiktoken.encoding_for_model(OPEN_AI_DEFAULT_MODEL)

# logger for this module
logger = get_child_logger(__name__)


class OpenAIClient:
    """Singleton class for managing the OpenAI client."""

    _instance = None

    def __init__(self, api_key: str):
        """Initialize the OpenAI client."""
        self.client = OpenAI(api_key=api_key)

    @classmethod
    def get_instance(cls):
        """
        Get or initialize the OpenAI client.

        Returns:
            OpenAI: The singleton OpenAI client instance.
        """
        if cls._instance is None:
            # Load the .env file
            load_dotenv()

            if api_key := os.getenv("OPENAI_API_KEY"):
                # Initialize the singleton instance
                cls._instance = cls(api_key)
            else:
                raise ValueError(
                    "API key not found. Set it in the .env file with the key 'OPENAI_API_KEY'."
                )

        return cls._instance.client


class ClientNotInitializedError(Exception):
    """Exception raised when the OpenAI client is not initialized."""

    pass


def token_count(text):
    return len(open_ai_encoding.encode(text))


def token_count_file(text_file: Path):
    text = get_text_from_file(text_file)
    return token_count(text)


def get_api_client():
    return OpenAIClient.get_instance()


def set_model_settings(model_settings_dict):
    global open_ai_model_settings
    open_ai_model_settings = model_settings_dict


def get_model_settings(model, parameter):
    return open_ai_model_settings[model][parameter]


def generate_messages(
    system_message: str,
    user_message_wrapper: callable,
    data_list_to_process: List,
    log_system_message=True,
):
    messages = []
    for data_element in data_list_to_process:
        message_block = [
            {"role": "system", "content": system_message},
            {
                "role": "user",
                "content": user_message_wrapper(data_element),
            },
        ]
        messages.append(message_block)
    return messages


def run_immediate_chat_process(
    messages, max_tokens: int = 0, response_format=None, model=OPEN_AI_DEFAULT_MODEL
):
    client = get_api_client()

    max_model_tokens = open_ai_model_settings[model]["max_tokens"]
    if max_tokens == 0:
        max_tokens = max_model_tokens

    if max_tokens > max_model_tokens:
        logger.warning(
            "Maximum token request exceeded: {max_tokens} for model: {model}"
        )
        logger.warning(f"Setting max_tokens to model maximum: {max_model_tokens}")
        max_tokens = max_model_tokens

    try:
        return (
            client.beta.chat.completions.parse(
                messages=messages,
                model=model,
                response_format=response_format,
                max_completion_tokens=max_tokens,
            )
            if response_format
            else client.chat.completions.create(
                messages=messages,
                model=model,
                max_completion_tokens=max_tokens,
            )
        )
    except Exception as e:
        logger.error(f"Error running immediate chat: {e}", exc_info=True)
        return None


def run_immediate_completion_simple(
    system_message: str,
    user_message: str,
    model=None,
    max_tokens: int = 0,
    response_format=None,
):
    """Runs a single chat completion with a system message and user message.

    This function simplifies the process of running a single chat completion with the OpenAI API by handling
    model selection, token limits, and logging. It allows for specifying a response format and handles potential
    `ValueError` exceptions during the API call.

    Args:
        system_message (str): The system message to guide the conversation.
        user_message (str): The user's message as input for the chat completion.
        model (str, optional): The OpenAI model to use. Defaults to None, which uses the default model.
        max_tokens (int, optional): The maximum number of tokens for the completion. Defaults to 0, which uses the model's maximum.
        response_format (dict, optional): The desired response format. Defaults to None.

    Returns:
        OpenAIObject | None: The chat completion response if successful, or None if a `ValueError` occurs.

    Raises:
        ValueError: if max_tokens exceeds the model's maximum token limit.
    """

    client = get_api_client()

    if not model:
        model = OPEN_AI_DEFAULT_MODEL

    max_model_tokens = open_ai_model_settings[model]["max_tokens"]
    if max_tokens == 0:
        max_tokens = max_model_tokens

    if max_tokens > max_model_tokens:
        logger.warning(
            "Maximum token request exceeded: {max_tokens} for model: {model}"
        )
        logger.warning(f"Setting max_tokens to model maximum: {max_model_tokens}")
        max_tokens = max_model_tokens

    logger.debug(f"User message content:\n{user_message[:DEBUG_DISPLAY_BUFFER]} ...")
    message_block = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]

    try:
        logger.debug(
            f"Starting chat completion with response_format={response_format} and max_tokens={max_tokens}..."
        )

        return (
            client.beta.chat.completions.parse(
                messages=message_block,  # type: ignore
                model=model,
                response_format=response_format,
                max_completion_tokens=max_tokens,
            )
            if response_format
            else client.chat.completions.create(
                messages=message_block,  # type: ignore
                model=model,
                max_completion_tokens=max_tokens,
            )
        )
    except ValueError as e:
        logger.error(f"Value Error running immediate chat: {e}", exc_info=True)
        return None


def run_transcription_speech(
    audio_file: Path,
    model: str = OPEN_AI_DEFAULT_MODEL,
    response_format="verbose_json",
    prompt="",
    mode: str = "transcribe",
):  # mode can be "transcribe" or "translate"

    client = get_api_client()

    with audio_file.open("rb") as file:
        if mode == "transcribe":
            transcript = client.audio.transcriptions.create(
                model=model, response_format=response_format, prompt=prompt, file=file
            )
        elif mode == "translate":
            transcript = client.audio.translations.create(
                model=model, response_format=response_format, prompt=prompt, file=file
            )
        else:
            logger.error(f"Invalid mode: {mode}, in speech transcription generation.")
            raise ValueError(f"'translate' or 'transcribe' expected, not {mode}.")

    return transcript


def get_completion_content(chat_completion):
    return chat_completion.choices[0].message.content


def get_completion_object(chat_completion):
    return chat_completion.choices[0].message.parsed


def _log_batch_creation_info(
    batch_file_path: Path, request_obj: Dict, total_tokens: int
):
    """
    Logs details about the JSONL batch creation process as a single coherent log message.

    Parameters:
        batch_file_path (Path): The path to the JSONL batch file being created.
        request_obj (Dict): The request object being logged, containing details like method, URL, and body.

    Returns:
        None
    """
    logger.info(
        f"Creating JSONL batch file with \033[91m{total_tokens}\033[0m requested tokens:\n\t{batch_file_path}"
    )
    logger.debug(
        f"Batch request details: Method={request_obj['method']}, URL={request_obj['url']}"
    )

    # Prepare batch parameters as a coherent string
    body = request_obj.get("body", {})
    batch_parameters = "\n".join(
        f"    {key}: {value}" for key, value in body.items() if key != "messages"
    )

    # Log the combined parameters
    logger.debug(f"Batch parameters:\n{batch_parameters}")


def create_jsonl_file_for_batch(
    messages: List[str],
    output_file_path: Optional[Path] = None,
    max_token_list: Optional[List[int]] = None,
    model: str = OPEN_AI_DEFAULT_MODEL,
    tools=None,
    json_mode: Optional[bool] = False,
):
    """
    Creates a JSONL file for batch processing, with each request using the same system message, user messages,
    and optional function schema for function calling.

    Args:
        messages: List of message objects to be sent for completion.
        output_file_path (str): The path where the .jsonl file will be saved.
        model (str): The model to use (default is set globally).
        functions (list, optional): List of function schemas to enable function calling.

    Returns:
        str: The path to the generated .jsonl file.
    """
    global open_ai_model_settings

    total_tokens = 0

    if not max_token_list:
        max_tokens = open_ai_model_settings[model]["max_tokens"]
        message_count = len(messages)
        max_token_list = [max_tokens] * message_count

    temperature = open_ai_model_settings[model]["temperature"]
    total_tokens = sum(max_token_list)

    if output_file_path is None:
        date_str = datetime.now().strftime("%m%d%Y")
        output_file_path = Path(f"batch_requests_{date_str}.jsonl")

    # Ensure the directory for the output file exists
    output_dir = Path(output_file_path).parent
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    requests = []
    for i, message in enumerate(messages):

        # get max_tokens
        max_tokens = max_token_list[i]

        request_obj = {
            "custom_id": f"request-{i+1}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model,
                "messages": message,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        }
        if json_mode:
            request_obj["body"]["response_format"] = {"type": "json_object"}
        if tools:
            request_obj["body"]["tools"] = tools

        if i == 0:  # log first iteration only.
            _log_batch_creation_info(output_file_path, request_obj, total_tokens)

        requests.append(request_obj)

    # Write requests to JSONL file
    with open(output_file_path, "w") as f:
        for request in requests:
            json.dump(request, f)
            f.write("\n")

    logger.info(f"JSONL file created at: {output_file_path}")
    return output_file_path


def poll_batch_for_response(
    batch_id: str,
    interval: int = 10,
    timeout: int = 3600,
    backoff_factor: float = 1.3,
    max_interval: int = 600,
) -> bool | list:
    """
    Poll the batch status until it completes, fails, or expires.

    Args:
        batch_id (str): The ID of the batch to poll.
        interval (int): Initial time (in seconds) to wait between polls. Default is 10 seconds.
        timeout (int): Maximum duration (in seconds) to poll before timing out. Use 1 hour as default.
        backoff_factor (int): Factor by which the interval increases after each poll.
        max_interval (int): Maximum polling interval in seconds.

    Returns:
        list: The batch response if successful.
        bool: Returns False if the batch fails, times out, or expires.

    Raises:
        RuntimeError: If the batch ID is not found or if an unexpected error occurs.
    """
    start_time = time.time()
    logger.info(f"Polling batch status for batch ID {batch_id} ...")

    attempts = 0
    while True:
        try:
            time.sleep(interval)
            elapsed_time = time.time() - start_time

            # Check for timeout
            if elapsed_time > timeout:
                logger.error(
                    f"Polling timed out after {timeout} seconds for batch ID {batch_id}."
                )
                return False

            # Get batch status
            batch_status = get_batch_status(batch_id)
            logger.debug(f"Batch ID {batch_id} status: {batch_status}")

            if not batch_status:
                raise RuntimeError(
                    f"Batch ID {batch_id} not found or invalid response from `get_batch_status`."
                )

            # Handle completed batch
            if batch_status == "completed":
                logger.info(
                    f"Batch processing for ID {batch_id} completed successfully."
                )
                try:
                    return get_batch_response(batch_id)
                except Exception as e:
                    logger.error(
                        f"Error retrieving response for batch ID {batch_id}: {e}",
                        exc_info=True,
                    )
                    raise RuntimeError(
                        f"Failed to retrieve response for batch ID {batch_id}."
                    ) from e

            # Handle failed batch
            elif batch_status == "failed":
                logger.error(f"Batch processing for ID {batch_id} failed.")
                return False

            # Log ongoing status and adjust interval
            logger.info(
                f"Batch status: {batch_status}. Retrying in {interval} seconds..."
            )
            attempts += 1
            interval = min(floor(interval * backoff_factor), max_interval)

        except Exception as e:
            logger.error(
                f"Unexpected error while polling batch ID {batch_id}: {e}",
                exc_info=True,
            )
            raise RuntimeError(f"Error during polling for batch ID {batch_id}.") from e


def _log_batch_start_info(batch, description):
    """
    Log the batch object and its metadata using the logger. Helper function for start_batch

    Args:
        batch: The Batch object returned by start_batch.
        logger: The logger instance for logging.
    """
    logger.info(f"Batch Initiated with description: {description}")
    logger.info(f"batch info: {batch.id}, {batch.created_at}, {batch.input_file_id} ")


def start_batch(jsonl_file: Path, description=""):
    """
    Starts a batch process using OpenAI's client with an optional description and JSONL batch file.

    Args:
        jsonl_file (Path): Path to the .jsonl batch file to be used as input. Must be a pathlib.Path object.
        description (str, optional): A description for metadata to label the batch job.
                                     If None, a default description is generated with the
                                     current date-time and file name.

    Returns:
        dict: A dictionary containing the batch object if successful, or an error message if failed.

    Example:
        jsonl_file = Path("batch_requests.jsonl")
        start_batch(jsonl_file)
    """
    client = get_api_client()

    if not isinstance(jsonl_file, Path):
        raise TypeError("The 'jsonl_file' argument must be a pathlib.Path object.")

    if not jsonl_file.exists():
        raise FileNotFoundError(f"The file {jsonl_file} does not exist.")

    basename = jsonl_file.stem

    # Generate description:
    current_time = datetime.now().astimezone().strftime("%m-%d-%Y %H:%M:%S %Z")
    description = f"{current_time} | {jsonl_file.name} | {description}"

    try:
        # Attempt to create the input file for the batch process
        with jsonl_file.open("rb") as file:
            batch_input_file = client.files.create(file=file, purpose="batch")
        batch_input_file_id = batch_input_file.id
    except Exception as e:
        return {"error": f"File upload failed: {e}"}

    try:
        # Attempt to create the batch with specified input file and metadata description
        batch = client.batches.create(
            input_file_id=batch_input_file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={"description": description, "basename": basename},
        )

        # log the batch
        _log_batch_start_info(batch, description)
        return batch

    except Exception as e:
        return {"error": f"Batch creation failed: {e}"}


def start_batch_with_retries(
    jsonl_file: Path,
    description: str = "",
    max_retries: int = DEFAULT_MAX_BATCH_RETRY,
    retry_delay: int = 5,
    poll_interval: int = 10,
    timeout: int = 3600,
) -> list[str]:
    """
    Starts a batch with retries and polls for its completion.

    Args:
        jsonl_file (Path): Path to the JSONL file for batch input.
        description (str): A description for the batch job (optional).
        max_retries (int): Maximum number of retries to start and complete the batch (default: 3).
        retry_delay (int): Delay in seconds between retries (default: 60).
        poll_interval (int): Interval in seconds for polling batch status (default: 10).
        timeout (int): Timeout in seconds for polling (default: 23 hours).

    Returns:
        list: The batch response if completed successfully.

    Raises:
        RuntimeError: If the batch fails after all retries or encounters an error.
    """
    for attempt in range(max_retries):
        try:
            # Start the batch
            batch = start_batch(jsonl_file, description=description)
            if not batch or "error" in batch:
                raise RuntimeError(
                    f"Failed to start batch: {batch.get('error', 'Unknown error')}"
                )

            batch_id = batch.id
            if not batch_id:
                raise RuntimeError("Batch started but no ID was returned.")

            logger.info(
                f"Batch started: attempt {attempt + 1}.",
                extra={"batch_id": batch_id, "description": description},
            )

            # Poll for batch completion
            response_list = poll_batch_for_response(
                batch_id, interval=poll_interval, timeout=timeout
            )

            # Check for a response
            if response_list:
                logger.info(
                    f"Batch completed successfully after {attempt + 1} attempts.",
                    extra={"batch_id": batch_id, "description": description},
                )
                break  # exit for loop

            else:  # No response means batch failed. Retry.
                logger.error(
                    f"Attempt {attempt + 1} failed. Retrying batch process in {retry_delay} seconds...",
                    extra={
                        "attempt": attempt + 1,
                        "max_retries": max_retries,
                        "description": description,
                    },
                )
                time.sleep(retry_delay)

        except Exception as e:
            logger.error(
                f"Batch start and polling failed on attempt {attempt + 1}: {e}",
                exc_info=True,
                extra={"attempt": attempt + 1, "description": description},
            )
            time.sleep(retry_delay)

    else:  # else the loop completed before succesful result
        logger.error(
            f"Failed to complete batch after {max_retries} retries.",
            extra={"description": description},
        )
        raise RuntimeError(
            f"Error: Failed to complete batch after {max_retries} retries."
        )

    return response_list


def run_single_batch(
    user_prompts: List,
    system_message: str,
    user_wrap_function: callable = None,
    max_token_list: List[int] = None,
    description="",
) -> List[str]:
    """
    Generate a batch file for the OpenAI (OA) API and send it.

    Parameters:
        system_message (str): System message template for batch processing.
        user_wrap_function (callable): Function to wrap user input for processing pages.

    Returns:
        str: Path to the created batch file.

    Raises:
        Exception: If an error occurs during file processing.
    """

    if max_token_list is None:
        max_token_list = []
    try:
        if not user_wrap_function:
            user_wrap_function = lambda x: x

        # Generate messages for the pages
        batch_message_seq = generate_messages(
            system_message, user_wrap_function, user_prompts
        )

        batch_file = Path("./temp_batch_run.jsonl")

        # Save the batch file
        create_jsonl_file_for_batch(
            batch_message_seq, batch_file, max_token_list=max_token_list
        )
        # logger.info(f"Batch file created successfully: {output_file}")

    except Exception as e:
        logger.error(f"Error while creating immediate batch file {batch_file}: {e}")
        raise

    try:

        if not description:
            description = (
                f"Single batch process: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        response_list = start_batch_with_retries(batch_file, description=description)

    except Exception as e:
        logger.error(f"Failed to complete batch process: {e}", exc_info=True)
        raise

    return response_list


def get_active_batches() -> List[Dict]:
    """
    Retrieve the list of active batches using the OpenAI API.
    """
    client = get_api_client()

    try:
        batches = client.batches.list(limit=MAX_BATCH_LIST)
        batch_list = []
        for batch in batches:
            if batch.status == "in_progress":
                batch_info = {
                    "id": batch.id,
                    "status": batch.status,
                    "created_at": batch.created_at,
                    # Add other relevant attributes as needed
                }
                batch_list.append(batch_info)
        return batch_list
    except Exception as e:
        logger.error(f"Error fetching active batches: {e}")
        return []


def get_batch_status(batch_id):
    client = get_api_client()

    batch = client.batches.retrieve(batch_id)
    return batch.status


def get_completed_batches() -> List[Dict]:
    """
    Retrieve the list of active batches using the OpenAI API.
    """
    client = get_api_client()

    try:
        batches = client.batches.list(limit=MAX_BATCH_LIST)
        batch_list = []
        for batch in batches:
            if batch.status == "completed":
                batch_info = {
                    "id": batch.id,
                    "status": batch.status,
                    "created_at": batch.created_at,
                    "output_file_id": batch.output_file_id,
                    "metadata": batch.metadata,
                    # Add other relevant attributes as needed
                }
                batch_list.append(batch_info)
        return batch_list
    except Exception as e:
        logger.error(f"Error fetching active batches: {e}", exc_info=True)
        return []


def get_all_batch_info():
    """
    Retrieve the list of batches up to MAX_BATCH_LIST using the OpenAI API.
    """
    client = get_api_client()

    try:
        batches = client.batches.list(limit=MAX_BATCH_LIST)
        batch_list = []
        for batch in batches:
            batch_info = {
                "id": batch.id,
                "status": batch.status,
                "created_at": batch.created_at,
                "output_file_id": batch.output_file_id,
                "metadata": batch.metadata,
                # Add other relevant attributes as needed
            }
            batch_list.append(batch_info)
        return batch_list
    except Exception as e:
        logger.error(f"Error fetching active batches: {e}", exc_info=True)
        return []


def get_batch_response(batch_id: str) -> List[str]:
    """
    Retrieves the status of a batch job and returns the result if completed.
    Parses the JSON result file, collects the output messages,
    and returns them as a Python list.

    Args:
    - batch_id : The batch_id string to retrieve status and results for.

    Returns:
    - If completed: A list containing the message content for each response of the batch process.
    - If not completed: A string with the batch status.
    """
    client = get_api_client()

    # Check the batch status
    batch_status = client.batches.retrieve(batch_id)
    if batch_status.status != "completed":
        logger.info(f"Batch status for {batch_id}: {batch_status.status}")
        return batch_status.status

    # Retrieve the output file contents
    file_id = batch_status.output_file_id
    file_response = client.files.content(file_id)

    # Parse the JSON lines in the output file
    results = []
    for line in file_response.text.splitlines():
        data = json.loads(line)  # Parse each line as JSON
        if response_body := data.get("response", {}).get("body", {}):
            content = response_body["choices"][0]["message"]["content"]
            results.append(content)

    return results


def get_last_batch_response(n: int = 0):
    assert n < MAX_BATCH_LIST
    completed = get_completed_batches()
    return get_batch_response(completed[n]["id"])


def delete_api_files(cutoff_date: datetime):
    """
    Delete all files on OpenAI's storage older than a given date at midnight.

    Parameters:
    - cutoff_date (datetime): The cutoff date. Files older than this date will be deleted.
    """
    # Set the OpenAI API key
    client = get_api_client()

    # Get a list of all files
    files = client.files.list()

    for file in files.data:
        # Parse the file creation timestamp
        file_created_at = datetime.fromtimestamp(file.created_at)
        # Check if the file is older than the cutoff date
        if file_created_at < cutoff_date:
            try:
                # Delete the file
                client.files.delete(file.id)
                print(f"Deleted file: {file.id} (created on {file_created_at})")
            except Exception as e:
                logger.error(f"Failed to delete file {file.id}: {e}", exc_info=True)
