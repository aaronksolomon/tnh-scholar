import logging
from pathlib import Path
import re
from data_processing.text_processing import get_text_from_file

from data_processing.gpt_processing import generate_messages, run_immediate_chat_process, create_jsonl_file_for_batch, start_batch
from data_processing.gpt_processing import get_completed_batches, get_batch_response
from data_processing.xml_processing import split_xml_pages, save_pages_to_xml

def generate_single_oa_batch_from_pages(
    input_xml_file: str,
    output_file: str,
    system_message: str,
    user_wrap_function,
):
    """
    Generate a batch file for the OpenAI (OA) API using a single input XML file.

    Parameters:
        batch_file (str): Full path to the input XML file to process.
        output_file (str): Full path to the output batch JSONL file.
        system_message (str): System message template for batch processing.
        user_wrap_function (callable): Function to wrap user input for processing pages.

    Returns:
        str: Path to the created batch file.

    Raises:
        Exception: If an error occurs during file processing.
    """
    logger = logging.getLogger(__name__)

    try:
        # Read the OCR text from the batch file
        text = get_text_from_file(input_xml_file)
        logger.info(f"Processing file: {input_xml_file}")

        # Split the text into pages for processing
        pages = split_xml_pages(text)
        if not pages:
            raise ValueError(f"No pages found in XML file: {input_xml_file}")
        logger.info(f"Found {len(pages)} pages in {input_xml_file}.")

        # Generate messages for the pages
        batch_message_seq = generate_messages(system_message, user_wrap_function, pages)

        # Save the batch file
        create_jsonl_file_for_batch(batch_message_seq, output_file)
        logger.info(f"Batch file created successfully: {output_file}")

        return output_file

    except FileNotFoundError:
        logger.error(f"File not found: {input_xml_file}")
        raise
    except ValueError as e:
        logger.error(f"Value error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while processing {input_xml_file}: {e}")
        raise

def generate_all_batches(
    processed_document_dir: str,
    system_message: str,
    user_wrap_function,
    file_regex: str = r".*\.xml",
):
    """
    Generate cleaning batches for all journals in the specified directory.

    Parameters:
        processed_journals_dir (str): Path to the directory containing processed journal data.
        system_message (str): System message template for batch processing.
        user_wrap_function (callable): Function to wrap user input for processing pages.
        file_regex (str): Regex pattern to identify target files (default: ".*\\.xml").

    Returns:
        None
    """
    logger = logging.getLogger(__name__)
    document_dir = Path(processed_document_dir)
    regex = re.compile(file_regex)

    for journal_file in document_dir.iterdir():
        if journal_file.is_file() and regex.search(journal_file.name):
            try:
                # Derive output file path
                output_file = journal_file.with_suffix(".jsonl")
                logger.info(f"Generating batch for {journal_file}...")

                # Call single batch function
                generate_single_oa_batch_from_pages(
                    input_xml_file=str(journal_file),
                    output_file=str(output_file),
                    system_message=system_message,
                    user_wrap_function=user_wrap_function,
                )
            except Exception as e:
                logger.error(f"Failed to process {journal_file}: {e}")
                continue

    logger.info("Batch generation completed.")