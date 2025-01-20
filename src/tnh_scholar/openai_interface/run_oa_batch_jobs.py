# NOT IN USE
# this is  prototyping module: testing only.

import json
import re
from pathlib import Path
from typing import Dict, List

from tnh_scholar.openai_interface import (
    set_api_client,
    start_batch,
    token_count,
)

# Constants
ENQUEUED_BATCH_TOKEN_LIMIT = 90000  # Adjust this based on your API rate limits
BATCH_JOB_PATH = Path("UNSET")


def get_active_batches(client) -> List[Dict]:
    """
    Retrieve the list of active batches using the OpenAI API.
    """
    try:
        response = client.get("/v1/batches")
        return response.get("data", [])
    except Exception as e:
        print(f"Error fetching active batches: {e}")
        return []


def calculate_enqueued_tokens(active_batches: List[Dict]) -> int:
    """
    Calculate the total number of enqueued tokens from active batches.
    """
    total_tokens = 0
    for batch in active_batches:
        # Assuming batches have an attribute `input_tokens` or equivalent
        total_tokens += batch.get("input_tokens", 0)
    return total_tokens


def process_batch_files(client, batch_file_directory, match_regexp=None):
    """
    Process batch files in the batch job directory, enqueue new batches if space permits.
    """
    batch_info = []
    active_batches = get_active_batches(client)
    enqueued_tokens = calculate_enqueued_tokens(active_batches)
    remaining_tokens = ENQUEUED_BATCH_TOKEN_LIMIT - enqueued_tokens

    for path_obj in Path(batch_file_directory).iterdir():
        if not match_regexp:
            match_regex = regex = re.compile(r"^clean_batch_.*\.jsonl")
        if path_obj.is_file() and regex.search(path_obj.name):
            batch_file = BATCH_JOB_PATH / path_obj.name
            print(f"Found batch file: {batch_file}")

            # Calculate the token count for this batch
            try:
                with open(batch_file, "r") as file:
                    data = file.read()
                    batch_tokens = token_count(data)
            except Exception as e:
                print(f"Failed to calculate token count for {batch_file}: {e}")
                continue

            # Enqueue batch if there's space
            if batch_tokens <= remaining_tokens:
                try:
                    batch = start_batch(client, batch_file)
                    batch_info.append(batch)
                    remaining_tokens -= batch_tokens
                    print(f"Batch enqueued: {batch}")
                except Exception as e:
                    print(f"Failed to enqueue batch {batch_file}: {e}")
            else:
                print(f"Insufficient token space for {batch_file}. Skipping.")
    return batch_info


def main():
    """
    Main function to manage and monitor batch jobs.
    """
    # Initialize API client
    client = set_api_client()
    if not client:
        print("Failed to initialize API client. Exiting.")
        return

    # Process batch files
    batch_info = process_batch_files(client)
    print(f"Batch processing completed. Enqueued batches: {len(batch_info)}")


if __name__ == "__main__":
    main()


### ----


import time
from pathlib import Path
from typing import Dict, List

# Constants
ENQUEUED_BATCH_TOKEN_LIMIT = 90000  # Adjust this based on your API rate limits
CHECK_INTERVAL_SECONDS = 60  # Time to wait between polling for batch status updates

# Global Variables
enqueued_tokens = 0
sent_batches = (
    {}
)  # Dictionary to track batches: {batch_id: {"batch": batch_obj, "token_size"}}


def calculate_enqueued_tokens(active_batches: List[Dict]) -> int:
    """
    Calculate the total number of enqueued tokens from active batches.
    """
    total_tokens = 0
    for batch in active_batches:
        total_tokens += batch.get("input_tokens", 0)
    return total_tokens


def download_batch_result(client, batch_id):
    """
    Download the result of a completed batch.
    """
    try:
        response = client.get(f"/v1/batches/{batch_id}")
        result = response.get("result", {})
        output_file = f"batch_results_{batch_id}.json"
        with open(output_file, "w") as file:
            json.dump(result, file, indent=4)
        print(f"Batch {batch_id} completed. Result saved to {output_file}.")
    except Exception as e:
        print(f"Error downloading result for batch {batch_id}: {e}")


def process_batch_files(client, batch_file_directory, remaining_tokens):
    """
    Process batch files in the batch job directory, enqueue new batches if space permits.
    """
    global enqueued_tokens, sent_batches
    batch_info = []

    for path_obj in Path(batch_file_directory).iterdir():
        regex = re.compile(r"^.*\.jsonl$")
        if path_obj.is_file() and regex.search(path_obj.name):
            batch_file = Path(batch_file_directory) / path_obj.name
            print(f"Found batch file: {batch_file}")

            # Calculate the token count for this batch
            try:
                with open(batch_file, "r") as file:
                    data = file.read()
                    batch_tokens = token_count(data)
            except Exception as e:
                print(f"Failed to calculate token count for {batch_file}: {e}")
                continue

            # Enqueue batch if there's space
            if batch_tokens <= remaining_tokens:
                try:
                    batch = start_batch(client, batch_file)
                    sent_batches[batch["id"]] = {
                        "batch": batch,
                        "token_size": batch_tokens,
                    }
                    enqueued_tokens += batch_tokens
                    remaining_tokens -= batch_tokens
                    print(f"Batch enqueued: {batch['id']}")
                except Exception as e:
                    print(f"Failed to enqueue batch {batch_file}: {e}")
            else:
                print(f"Insufficient token space for {batch_file}. Skipping.")
    return batch_info


def poll_batches(client):
    """
    Poll for completed batches and update global enqueued_tokens.
    """
    global enqueued_tokens, sent_batches
    completed_batches = []

    for batch_id, info in sent_batches.items():
        batch = info["batch"]
        try:
            response = client.get(f"/v1/batches/{batch_id}")
            status = response.get("status")
            if status == "completed":
                download_batch_result(client, batch_id)
                enqueued_tokens -= info["token_size"]
                completed_batches.append(batch_id)
            elif status == "failed":
                print(f"Batch {batch_id} failed. Removing from tracking.")
                enqueued_tokens -= info["token_size"]
                completed_batches.append(batch_id)
        except Exception as e:
            print(f"Error checking status for batch {batch_id}: {e}")

    # Remove completed batches from sent_batches
    for batch_id in completed_batches:
        del sent_batches[batch_id]


def main():
    """
    Main function to manage and monitor batch jobs.
    """
    global enqueued_tokens, sent_batches
    client = set_api_client()
    if not client:
        print("Failed to initialize API client. Exiting.")
        return

    batch_file_directory = "./journal_cleaning_batches"

    while True:
        # Poll for completed batches
        print("Polling for completed batches...")
        poll_batches(client)

        # Calculate remaining tokens
        remaining_tokens = ENQUEUED_BATCH_TOKEN_LIMIT - enqueued_tokens
        print(f"Remaining tokens: {remaining_tokens}")

        # Enqueue new batches if there's space
        print("Processing batch files...")
        process_batch_files(client, batch_file_directory, remaining_tokens)

        # Wait for the next polling cycle
        print(f"Waiting for {CHECK_INTERVAL_SECONDS} seconds before next check...")
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
