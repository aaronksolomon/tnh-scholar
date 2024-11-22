import tiktoken
import os
from openai import OpenAI
import json
from datetime import datetime
from typing import List, Dict

MAX_TOKENS = 16000
MAX_BATCH_LIST = 100
open_ai_working_model = "gpt-4o"
open_ai_current_client = None

open_ai_encoding = tiktoken.encoding_for_model(open_ai_working_model)

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

def run_immediate_chat_process(messages, response_object=None):
    global open_ai_current_client

    if open_ai_current_client is None:
        raise ClientNotInitializedError(
            "The OpenAI client is not initialized. Please set `open_ai_current_client` before calling this function."
        )
    
    try:
        if response_object:
            chat_completion = open_ai_current_client.beta.chat.completions.parse(
                messages=messages,
                model=open_ai_working_model,
                response_format=response_object
            )
        else: 
            chat_completion = open_ai_current_client.chat.completions.create(
                messages=messages,
                model=open_ai_working_model,
            )
        return chat_completion
    
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def create_jsonl_file_for_batch(messages, output_file_path=None, max_tokens=MAX_TOKENS):
    """
    Creates a JSONL file for batch processing, with each request using the same system message and different user messages.

    Args:
        messages: to be sent for completion
        output_file_path (str): The path where the .jsonl file will be saved.
    
    Returns:
        str: The path to the generated .jsonl file.
    """
    if output_file_path is None:
        date_str = datetime.now().strftime("%m%d%Y")
        output_file_path = f"batch_requests_{date_str}.jsonl"

    requests = []      
    for i, message in enumerate(messages):
        request_obj = {
            "custom_id": f"request-{i+1}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": open_ai_working_model,
                "messages": message,
                "max_tokens": max_tokens,
            },
        }
        requests.append(request_obj)

    # Write requests to JSONL file
    with open(output_file_path, "w") as f:
        for request in requests:
            json.dump(request, f)
            f.write("\n")
    
    return output_file_path

def start_batch(jsonl_file, description=None):
    """
    Starts a batch process using OpenAI's client with an optional description and JSONL batch file.

    Args:
        client: An initialized OpenAI client instance.
        jsonl_file (str): Path to the .jsonl batch file to be used as input.
        description (str, optional): A description for metadata to label the batch job. 
                                     If None, a default description is generated with the 
                                     current date-time and file name.

    Returns:
        dict: A dictionary containing the batch object if successful, or an error message if failed.
    
    Example:
        client = openai.Client(api_key="your-api-key")
        jsonl_file = "batch_requests.jsonl"
        start_batch(client, jsonl_file)
    """
    global open_ai_current_client

    if open_ai_current_client is None:
        raise ClientNotInitializedError(
            "The OpenAI client is not initialized. Please set `open_ai_current_client` before calling this function."
        )
    
    basename = os.path.splitext(os.path.basename(jsonl_file))[0]

    # Generate a default description if none is provided
    if description is None:
        current_time = datetime.now().astimezone().strftime("%m-%d-%Y %H:%M:%S %Z")
        description = f"{current_time} | {jsonl_file}"

    try:
        # Attempt to create the input file for the batch process
        batch_input_file = open_ai_current_client.files.create(
            file=open(jsonl_file, "rb"),
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

import ast

def get_batch_response(batch_id):
    """
    Retrieves the status of a batch job and returns the result if completed.
    Parses the JSON result file, collects the output messages (query-text pairs),
    and converts them to Python lists.
    
    Args:
    - batch (Batch): The batch object to retrieve status and results for.

    Returns:
    - If completed: A list of lists containing query-text pairs.
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
        return None


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