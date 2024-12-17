import os
import time
from openai import OpenAI
from pathlib import Path

test_file = Path("./temp_batch_run.jsonl")

def start_and_poll_batch(jsonl_file: Path, interval: int = 10, description=""):
    """
    Starts a batch process and polls the batch status until it completes or fails.
    Runs for a maximum of 100 attempts to demonstrate intermittent failures.

    Args:
        jsonl_file (Path): Path to the .jsonl batch file.
        interval (int): Time interval in seconds to wait between polling attempts.
        description (str): Metadata description for the batch job.

    Returns:
        bool: True if successful, False if the batch fails.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def get_batch_status(batch_id):
        batch = client.batches.retrieve(batch_id)
        return batch.status
    
    for attempt in range(100):
        # Start the batch
        with jsonl_file.open("rb") as file:
            batch_input_file = client.files.create(file=file, purpose="batch")

        batch = client.batches.create(
            input_file_id=batch_input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={"description": description}
        )
        batch_id = batch.id
        print(f"Batch started successfully: {batch_id}")

        time.sleep(interval)

        while(True):
            batch_status = get_batch_status(batch_id)
            
            if batch_status == "completed":
                print("Batch completed successfully.")
                return True

            elif batch_status == "failed":
                print(f"Batch failed on attempt {attempt + 1}. Retrying...")
                break # exit this loop and retry batches.

            else:
                print(f"batch status: {batch_status}")
                time.sleep(interval)
                continue

    print("Exceeded maximum attempts (100). Exiting.")
    return False