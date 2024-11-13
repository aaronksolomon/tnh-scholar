import tiktoken
import os
from openai import OpenAI
import json
from datetime import datetime


MAX_TOKENS = 5000
open_ai_working_model = "gpt-4o"
open_ai_current_client = None

encoding = tiktoken.encoding_for_model(open_ai_working_model)

def token_count(text):
    return len(encoding.encode(text))

def get_api_client():
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
    
def create_jsonl_file_for_batch(messages, output_file_path=None, response_object=None, max_tokens=MAX_TOKENS):
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
    if response_object:
            
        for i, message in enumerate(messages):
            request_obj = {
                "custom_id": f"request-{i+1}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": open_ai_working_model,
                    "messages": message,
                    "response"
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