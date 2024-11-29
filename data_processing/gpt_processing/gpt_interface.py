import tiktoken
import os
from openai import OpenAI
import json
from datetime import datetime
from typing import List, Dict
from pathlib import Path
import ast

MAX_BATCH_LIST = 30
OPEN_AI_DEFAULT_MODEL = "gpt-4o"
open_ai_current_client = None
DEFAULT_MODEL_SETTINGS = {
    "gpt-4o": {
        "max_tokens": 16000,
        "context_limit": 128000  # Total context limit for the model
    },
    "gpt-3.5-turbo": {
        "max_tokens": 4096,  # Set conservatively to avoid errors
        "context_limit": 16384  # Same as gpt-4o
        }
    }

# Dictionary of model configurations
open_ai_model_settings = DEFAULT_MODEL_SETTINGS

open_ai_encoding = tiktoken.encoding_for_model(OPEN_AI_DEFAULT_MODEL)

class ClientNotInitializedError(Exception):
    """Exception raised when the OpenAI client is not initialized."""
    pass

def token_count(text):
    return len(open_ai_encoding.encode(text))

def get_api_client():
    if open_ai_current_client is None:
        raise ClientNotInitializedError(
            "The OpenAI client is not initialized. Please set `open_ai_current_client` before calling this function."
        )
    return open_ai_current_client

def set_api_client():
    global open_ai_current_client

    try:
        client = OpenAI(
            # This is the default and can be omitted
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        open_ai_current_client = client
        return client
    except Exception as e:
        print(f"Error: {e}")
        return False
    
def set_model_settings(model_settings_dict):
    global open_ai_model_settings
    open_ai_model_settings = model_settings_dict
    
def generate_messages(system_message, user_message_wrapper, text_list_to_process):
    messages = []
    for text_element in text_list_to_process:    
        message_block = [
                    {
                        "role": "system",
                        "content": system_message
                    },
                    {
                        "role": "user",
                        "content": user_message_wrapper(text_element),                                         
                    }
                ]
        messages.append(message_block)        
    return messages

def run_immediate_chat_process(messages, response_object=None, model=OPEN_AI_DEFAULT_MODEL):
    global open_ai_current_client

    if open_ai_current_client is None:
        raise ClientNotInitializedError(
            "The OpenAI client is not initialized. Please set `open_ai_current_client` before calling this function."
        )
    
    try:
        if response_object:
            chat_completion = open_ai_current_client.beta.chat.completions.parse(
                messages=messages,
                model=model,
                response_format=response_object
            )
        else: 
            chat_completion = open_ai_current_client.chat.completions.create(
                messages=messages,
                model=model,
            )
        return chat_completion
    
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def create_jsonl_file_for_batch(messages, output_file_path=None, model=OPEN_AI_DEFAULT_MODEL, tools=None, json_mode=False):
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

    max_tokens = open_ai_model_settings[model]['max_tokens']
    temperature = open_ai_model_settings[model]['temperature']

    if output_file_path is None:
        date_str = datetime.now().strftime("%m%d%Y")
        output_file_path = f"batch_requests_{date_str}.jsonl"

    requests = []      
    for i, message in enumerate(messages):
        # Add the function schema if provided
        request_obj = {
            "custom_id": f"request-{i+1}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model,
                "messages": message,
                "max_tokens": max_tokens,
                "temperature": temperature
            },
        }
        if json_mode:
            request_obj["body"]["response_format"] = {"type": "json_object"}
        if tools:
            request_obj["body"]["tools"] = tools
        
        print_request_info(request_obj)

        requests.append(request_obj)

    # Write requests to JSONL file
    with open(output_file_path, "w") as f:
        for request in requests:
            json.dump(request, f)
            f.write("\n")
    
    print(f"JSONL file created at: {output_file_path}")
    return output_file_path

def print_request_info(request_obj):
    body = request_obj["body"]
    for key, value in body.items():
        if key != "messages":
            print(f"{key}: {value}")

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
    global open_ai_current_client

    if open_ai_current_client is None:
        raise ClientNotInitializedError(
            "The OpenAI client is not initialized. Please set `open_ai_current_client` before calling this function."
        )
    
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
            batch_input_file = open_ai_current_client.files.create(
                file=file,
                purpose="batch"
            )
        batch_input_file_id = batch_input_file.id
    except Exception as e:
        return {"error": f"File upload failed: {e}"}
    
    try:
        # Attempt to create the batch with specified input file and metadata description
        batch = open_ai_current_client.batches.create(
            input_file_id=batch_input_file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={
                "description": description,
                "basename": basename
            }
        )
        print(f"Batch Initiated: {description}")
        return batch
    except Exception as e:
        return {"error": f"Batch creation failed: {e}"}
    
def get_active_batches() -> List[Dict]:
    """
    Retrieve the list of active batches using the OpenAI API.
    """
    try:
        batches = open_ai_current_client.batches.list(limit=MAX_BATCH_LIST)
        batch_list = []
        for batch in batches:
            if batch.status == "in_progress":
                batch_info = {
                    'id': batch.id,
                    'status': batch.status,
                    'created_at': batch.created_at,
                    # Add other relevant attributes as needed
                }
                batch_list.append(batch_info)
        return batch_list
    except Exception as e:
        print(f"Error fetching active batches: {e}")
        return []

def get_batch_status(batch_id):
    global open_ai_current_client

    batch = open_ai_current_client.batches.retrieve(batch_id)
    return batch.status


def get_completed_batches() -> List[Dict]:
    """
    Retrieve the list of active batches using the OpenAI API.
    """
    global open_ai_current_client

    if open_ai_current_client is None:
        raise ClientNotInitializedError(
            "The OpenAI client is not initialized. Please set `open_ai_current_client` before calling this function."
        )
    
    try:
        batches = open_ai_current_client.batches.list(limit=MAX_BATCH_LIST)
        batch_list = []
        for batch in batches:
            if batch.status == "completed":
                batch_info = {
                    'id': batch.id,
                    'status': batch.status,
                    'created_at': batch.created_at,
                    'output_file_id': batch.output_file_id,
                    'metadata': batch.metadata
                    # Add other relevant attributes as needed
                }
                batch_list.append(batch_info)
        return batch_list
    except Exception as e:
        print(f"Error fetching active batches: {e}")
        return []


def get_all_batch_info():
    """
    Retrieve the list of batches up to MAX_BATCH_LIST using the OpenAI API.
    """
    global open_ai_current_client

    if open_ai_current_client is None:
        raise ClientNotInitializedError(
            "The OpenAI client is not initialized. Please set `open_ai_current_client` before calling this function."
        )
    
    try:
        batches = open_ai_current_client.batches.list(limit=MAX_BATCH_LIST)
        batch_list = []
        for batch in batches:
            batch_info = {
                'id': batch.id,
                'status': batch.status,
                'created_at': batch.created_at,
                'output_file_id': batch.output_file_id,
                'metadata': batch.metadata
                # Add other relevant attributes as needed
            }
            batch_list.append(batch_info)
        return batch_list
    except Exception as e:
        print(f"Error fetching active batches: {e}")
        return []

def get_batch_response(batch_id):
    """
    Retrieves the status of a batch job and returns the result if completed.
    Parses the JSON result file, collects the output messages,
    and returns them as a Python list.
    
    Args:
    - batch (Batch): The batch object to retrieve status and results for.

    Returns:
    - If completed: A list containing the message content for each response of the batch process.
    - If not completed: A string with the batch status.
    """
    global open_ai_current_client

    if open_ai_current_client is None:
        raise ClientNotInitializedError(
            "The OpenAI client is not initialized. Please set `open_ai_current_client` before calling this function."
        )
    
    # Check the batch status
    batch_status = open_ai_current_client.batches.retrieve(batch_id)
    if batch_status.status != 'completed':
        print(f"Batch status: {batch_status.status}")
        return batch_status.status

    # Retrieve the output file contents
    file_id = batch_status.output_file_id
    file_response = open_ai_current_client.files.content(file_id)

    # Parse the JSON lines in the output file
    results = []
    for line in file_response.text.splitlines():
        data = json.loads(line)  # Parse each line as JSON
        response_body = data.get("response", {}).get("body", {})
        if response_body:
            content = response_body["choices"][0]["message"]["content"]
            results.append(content)

    return results

def get_last_batch_response(n: int = 0):
    assert n < MAX_BATCH_LIST
    completed = get_completed_batches()
    return get_batch_response(completed[n]['id'])

def run_single_oa_batch(
    user_prompts: List,
    system_message: str,
    user_wrap_function: callable = None,
):
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
    #logger = logging.getLogger(__name__)

    try:
        if not user_wrap_function:
            user_wrap_function = lambda x: x

        # Generate messages for the pages
        batch_message_seq = generate_messages(system_message, user_wrap_function, user_prompts)

        batch_file = Path("./temp_batch_run.jsonl")

        # Save the batch file
        create_jsonl_file_for_batch(batch_message_seq, batch_file)
        #logger.info(f"Batch file created successfully: {output_file}")

    except FileNotFoundError:
        #logger.error(f"File not found: {input_xml_file}")
        raise
    except ValueError as e:
        #logger.error(f"Value error: {e}")
        raise
    except Exception as e:
        #logger.error(f"Unexpected error while processing {input_xml_file}: {e}")
        raise

    try: 
        batch =  start_batch(batch_file, description="temp batch process run.")
        return batch.id
    
    except Exception as e:
        raise

def delete_old_files(cutoff_date: datetime):
    """
    Delete all files on OpenAI's storage older than a given date at midnight.

    Parameters:
    - cutoff_date (datetime): The cutoff date. Files older than this date will be deleted.
    """
    # Set the OpenAI API key
    global open_ai_current_client

    client = open_ai_current_client

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
                print(f"Failed to delete file {file.id}: {e}")