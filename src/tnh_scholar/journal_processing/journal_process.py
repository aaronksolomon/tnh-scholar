import json
import logging
import re
from math import floor
from pathlib import Path
from types import SimpleNamespace
from typing import List

from tnh_scholar.openai_interface import (
    create_jsonl_file_for_batch,
    generate_messages,
    run_immediate_chat_process,
    start_batch_with_retries,
    token_count,
)
from tnh_scholar.utils.file_utils import get_text_from_file
from tnh_scholar.xml_processing import (
    join_xml_data_to_doc,
    save_pages_to_xml,
    split_xml_on_pagebreaks,
    split_xml_pages,
)

# constants
MAX_TOKEN_LIMIT = 60000
MAX_BATCH_RETRIES = 40  # Number of retries
BATCH_RETRY_DELAY = 5  # seconds to wait before retry

logger = logging.getLogger("journal_process")


# logger setup function
def setup_logger(log_file_path):
    """
    Configures the logger to write to a log file and the console.
    Adds a custom "PRIORITY_INFO" logging level for important messages.
    """
    # Remove existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Include logger name
        handlers=[
            logging.FileHandler(log_file_path, encoding="utf-8"),
            logging.StreamHandler(),  # Optional: to log to the console as well
        ],
    )

    # Suppress DEBUG/INFO logs for specific noisy modules
    modules_to_suppress = ["httpx", "httpcore", "urllib3", "openai", "google"]
    for module in modules_to_suppress:
        logger = logging.getLogger(module)
        logger.setLevel(logging.WARNING)  # Suppress DEBUG and INFO logs

    # Add a custom "PRIORITY_INFO" level
    PRIORITY_INFO_LEVEL = 25  # Between INFO (20) and WARNING (30)
    logging.addLevelName(PRIORITY_INFO_LEVEL, "PRIORITY_INFO")

    def priority_info(self, message, *args, **kwargs):
        if self.isEnabledFor(PRIORITY_INFO_LEVEL):
            self._log(PRIORITY_INFO_LEVEL, f"\033[93m{message}\033[0m", args, **kwargs)

    logging.Logger.priority_info = priority_info

    return logging.getLogger(__name__)


# Journal schema for sectioning
global journal_schema
journal_schema = {
    "type": "object",
    "properties": {
        "journal_summary": {"type": "string"},
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title_vi": {"type": "string"},
                    "title_en": {"type": "string"},
                    "author": {"type": ["string", "null"]},
                    "summary": {"type": "string"},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "start_page": {"type": "integer", "minimum": 1},
                    "end_page": {"type": "integer", "minimum": 1},
                },
                "required": [
                    "title_vi",
                    "title_en",
                    "summary",
                    "keywords",
                    "start_page",
                    "end_page",
                ],
            },
        },
    },
    "required": ["journal_summary", "sections"],
}


# cleaning helper functions:
def wrap_lines(text: str) -> str:
    """
    Encloses each line of the input text with angle brackets.

    Args:
        text (str): The input string containing lines separated by '\n'.

    Returns:
        str: A string where each line is enclosed in angle brackets.

    Example:
        >>> enclose_lines("This is a string with   \n   two lines.")
        '<This is a string with  >\n<    two lines.>'
    """
    return "\n".join(f"<{line}>" for line in text.split("\n"))


def wrap_all_lines(pages):
    return [wrap_lines(page) for page in pages]


def unwrap_lines(text: str) -> str:
    """
    Removes angle brackets (< >) from encapsulated lines and merges them into
    a newline-separated string.

    Parameters:
        text (str): The input string with encapsulated lines.

    Returns:
        str: A newline-separated string with the encapsulation removed.

    Example:
        >>> merge_encapsulated_lines("<Line 1> <Line 2> <Line 3>")
        'Line 1\nLine 2\nLine 3'
        >>> merge_encapsulated_lines("<Line 1>\n<Line 2>\n<Line 3>")
        'Line 1\nLine 2\nLine 3'
    """
    # Find all content between < and > using regex
    matches = re.findall(r"<(.*?)>", text)
    # Join the extracted content with newlines
    return "\n".join(matches)


def unwrap_all_lines(pages):
    result = []
    for page in pages:
        if page == "blank page":
            result.append(page)
        else:
            result.append(unwrap_lines(page))
    return result


# code to processs and validate journal sections
def validate_and_clean_data(data, schema):
    """
    Recursively validate and clean AI-generated data to fit the given schema.
    Any missing fields are filled with defaults, and extra fields are ignored.

    Args:
        data (dict): The AI-generated data to validate and clean.
        schema (dict): The schema defining the required structure.

    Returns:
        dict: The cleaned data adhering to the schema.
    """

    def clean_value(value, field_schema):
        """
        Clean a single value based on its schema, attempting type conversions where necessary.
        """
        field_type = field_schema["type"]

        # Handle type: string
        if field_type == "string":
            if isinstance(value, str):
                return value
            elif value is not None:
                return str(value)
            return "unset"

        # Handle type: integer
        elif field_type == "integer":
            if isinstance(value, int):
                return value
            elif isinstance(value, str) and value.isdigit():
                return int(value)
            try:
                return int(float(value))  # Handle cases like "2.0"
            except (ValueError, TypeError):
                return 0

        # Handle type: array
        elif field_type == "array":
            if isinstance(value, list):
                item_schema = field_schema.get("items", {})
                return [clean_value(item, item_schema) for item in value]
            elif isinstance(value, str):
                # Try splitting comma-separated strings into a list
                return [v.strip() for v in value.split(",")]
            return []

        # Handle type: object
        elif field_type == "object":
            if isinstance(value, dict):
                return validate_and_clean_data(value, field_schema)
            return {}

        # Handle nullable strings
        elif field_type == ["string", "null"]:
            if value is None or isinstance(value, str):
                return value
            return str(value)

        # Default case for unknown or unsupported types
        return "unset"

    def clean_object(obj, obj_schema):
        """
        Clean a dictionary object based on its schema.
        """
        if not isinstance(obj, dict):
            print(
                f"Expected dict but got: \n{type(obj)}: {obj}\nResetting to empty dict."
            )
            return {}
        cleaned = {}
        properties = obj_schema.get("properties", {})
        for key, field_schema in properties.items():
            # Set default value for missing fields
            cleaned[key] = clean_value(obj.get(key), field_schema)
        return cleaned

    # Handle the top-level object
    if schema["type"] == "object":
        cleaned_data = clean_object(data, schema)
        return cleaned_data
    else:
        raise ValueError("Top-level schema must be of type 'object'.")


def validate_and_save_metadata(
    output_file_path: Path, json_metadata_serial: str, schema
):
    """
    Validates and cleans journal data against the schema, then writes it to a JSON file.

    Args:
        data (str): The journal data as a serialized JSON string to validate and clean.
        schema (dict): The schema defining the required structure.
        output_file_path (str): Path to the output JSON file.

    Returns:
        bool: True if successfully written to the file, False otherwise.
    """
    try:
        # Clean the data to fit the schema
        data = deserialize_json(json_metadata_serial)
        cleaned_data = validate_and_clean_data(data, schema)

        # Write the parsed data to the specified JSON file
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(cleaned_data, f, indent=4, ensure_ascii=False)
        logger.info(
            f"Parsed and validated metadata successfully written to {output_file_path}"
        )
        return True
    except Exception as e:
        logger.error(f"An error occurred during validation or writing: {e}")
        raise


def extract_page_groups_from_metadata(metadata):
    """
    Extracts page groups from the section metadata for use with `split_xml_pages`.

    Parameters:
        metadata (dict): The section metadata containing sections with start and end pages.

    Returns:
        List[Tuple[int, int]]: A list of tuples, each representing a page range (start_page, end_page).
    """
    page_groups = []

    # Ensure metadata contains sections
    if "sections" not in metadata or not isinstance(metadata["sections"], list):
        raise ValueError(
            "Metadata does not contain a valid 'sections' key with a list of sections."
        )

    for section in metadata["sections"]:
        try:
            # Extract start and end pages
            start_page = section.get("start_page")
            end_page = section.get("end_page")

            # Ensure both start_page and end_page are integers
            if not isinstance(start_page, int) or not isinstance(end_page, int):
                raise ValueError(f"Invalid page range in section: {section}")

            # Add the tuple to the page groups list
            page_groups.append((start_page, end_page))

        except KeyError as e:
            print(f"Missing key in section metadata: {e}")
        except ValueError as e:
            print(f"Error processing section metadata: {e}")

    logger.debug(f"page groups found: {page_groups}")

    return page_groups


def _get_max_tokens_for_clean(data: str, factor: float = 1, buffer: int = 100):
    return floor(token_count(data) * factor) + buffer


def generate_clean_batch(
    input_xml_file: str, output_file: str, system_message: str, user_wrap_function
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

    try:
        # Read the OCR text from the batch file
        text = get_text_from_file(input_xml_file)
        logger.info(f"Processing file: {input_xml_file}")

        # Split the text into pages for processing
        pages = split_xml_on_pagebreaks(text)
        pages = wrap_all_lines(pages)  # wrap lines with brackets.
        if not pages:
            raise ValueError(f"No pages found in XML file: {input_xml_file}")
        logger.info(f"Found {len(pages)} pages in {input_xml_file}.")

        max_tokens = [_get_max_tokens_for_clean(page) for page in pages]

        # Generate messages for the pages
        batch_message_seq = generate_messages(system_message, user_wrap_function, pages)

        # Save the batch file
        create_jsonl_file_for_batch(
            batch_message_seq, output_file, max_token_list=max_tokens
        )
        logger.info(f"Batch file created successfully: {output_file}")

        return output_file

    except FileNotFoundError:
        logger.error("File not found.")
        raise
    except ValueError as e:
        logger.error(f"Value error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while processing {input_xml_file}: {e}")
        raise


# running batches
def batch_section(
    input_xml_path: Path, batch_jsonl: Path, system_message, journal_name
):
    """
    Splits the journal content into sections using GPT, with retries for both starting and completing the batch.

    Args:
        input_xml_path (str): Path to the input XML file.
        output_json_path (str): Path to save validated metadata JSON.
        raw_output_path (str): Path to save the raw batch results.
        journal_name (str): Name of the journal being processed.
        max_retries (int): Maximum number of retries for batch processing.
        retry_delay (int): Delay in seconds between retries.

    Returns:
        str: the result of the batch sectioning process as a serialized json object.
    """
    try:
        logger.info(
            f"Starting sectioning batch for {journal_name} with file:\n\t{input_xml_path}"
        )
        # Load journal content
        journal_pages = get_text_from_file(input_xml_path)

        # Create GPT messages for sectioning
        user_message_wrapper = lambda text: f"{text}"
        messages = generate_messages(
            system_message, user_message_wrapper, [journal_pages]
        )

        # Create JSONL file for batch processing
        jsonl_file = create_jsonl_file_for_batch(messages, batch_jsonl, json_mode=True)

    except Exception as e:
        logger.error(
            f"Failed to initialize batch sectioning data for journal '{journal_name}'.",
            extra={"input_xml_path": input_xml_path},
            exc_info=True,
        )
        raise RuntimeError(
            f"Error initializing batch sectioning data for journal '{journal_name}'."
        ) from e

    response = start_batch_with_retries(
        jsonl_file,
        description=f"Batch for sectioning journal: {journal_name} | input file: {input_xml_path}",
    )

    if response:
        json_result = response[
            0
        ]  # should return json, just one batch so first response
        # Log success and return output json
        logger.info(
            f"Successfully batch sectioned journal '{journal_name}' with input file: {input_xml_path}."
        )
        return json_result
    else:
        logger.error("Section batch failed to get response.")
        return ""


# Step 2: Translation
def batch_translate(
    input_xml_path: Path,
    batch_json_path: Path,
    metadata_path: Path,
    system_message,
    journal_name: str,
):
    """
    Translates the journal sections using the GPT model.
    Saves the translated content back to XML.

    Args:
        input_xml_path (str): Path to the input XML file.
        metadata_path (str): Path to the metadata JSON file.
        journal_name (str): Name of the journal.
        xml_output_path (str): Path to save the translated XML.
        max_retries (int): Maximum number of retries for batch operations.
        retry_delay (int): Delay in seconds between retries.

    Returns:
        bool: True if the process succeeds, False otherwise.
    """
    logger.info(
        f"Starting translation batch for journal '{journal_name}':\n\twith file: {input_xml_path}\n\tmetadata: {metadata_path}"
    )

    # Data initialization:
    try:
        # load metadata
        serial_json = get_text_from_file(metadata_path)

        section_metadata = deserialize_json(serial_json)
        if not section_metadata:
            raise RuntimeError(f"Metadata could not be loaded from {metadata_path}.")

        # Extract page groups and split XML content
        page_groups = extract_page_groups_from_metadata(section_metadata)
        xml_content = get_text_from_file(input_xml_path)
        section_contents = split_xml_on_pagebreaks(xml_content, page_groups)

        if section_contents:
            logger.debug(f"section_contents[0]:\n{section_contents[0]}")
        else:
            logger.error("No sectin contents.")

    except Exception as e:
        logger.error(
            f"Failed to initialize data for translation batching for journal '{journal_name}'.",
            exc_info=True,
        )
        raise RuntimeError(
            f"Error during data initialization for journal '{journal_name}'."
        ) from e

    translation_data = translate_sections(
        batch_json_path,
        system_message,
        section_contents,
        section_metadata,
        journal_name,
    )
    return translation_data


def translate_sections(
    batch_jsonl_path: Path,
    system_message,
    section_contents,
    section_metadata,
    journal_name,
    immediate=False,
):
    """build up sections in batches to translate"""

    section_mdata = section_metadata["sections"]
    if len(section_contents) != len(section_mdata):
        raise RuntimeError("Section length mismatch.")

    # collate metadata and section content, calculate max_tokens per section:
    section_data_to_send = []
    max_token_list = []
    current_token_count = 0
    collected_translations = []
    section_last_index = len(section_mdata) - 1

    for i, section_info in enumerate(section_mdata):
        section_content = section_contents[i]
        max_tokens = floor(token_count(section_content) * 1.3) + 1000
        max_token_list.append(max_tokens)
        current_token_count += max_tokens
        section_data = SimpleNamespace(
            title=section_info["title_en"], content=section_content
        )
        section_data_to_send.append(section_data)
        logger.debug(f"section {i}: {section_data.title} added for batch processing.")

        if current_token_count >= MAX_TOKEN_LIMIT or i == section_last_index:
            # send sections for batch processing since token limit reached.
            batch_result = send_data_for_tx_batch(
                batch_jsonl_path,
                section_data_to_send,
                system_message,
                max_token_list,
                journal_name,
                immediate,
            )
            collected_translations.extend(batch_result)

            # reset containers to start building up next batch.
            section_data_to_send = []
            max_token_list = []
            current_token_count = 0

    return collected_translations


def send_data_for_tx_batch(
    batch_jsonl_path: Path,
    section_data_to_send: List,
    system_message,
    max_token_list: List,
    journal_name,
    immediate=False,
):
    """
    Sends data for translation batch or immediate processing.

    Args:
        batch_jsonl_path (Path): Path for the JSONL file to save batch data.
        section_data_to_send (List): List of section data to translate.
        system_message (str): System message for the translation process.
        max_token_list (List): List of max tokens for each section.
        journal_name (str): Name of the journal being processed.
        immediate (bool): If True, run immediate chat processing instead of batch.

    Returns:
        List: Translated data from the batch or immediate process.
    """
    try:
        # Generate all messages using the generate_messages function
        user_message_wrapper = (
            lambda section_info: f"Translate this section with title '{section_info.title}':\n{section_info.content}"
        )
        messages = generate_messages(
            system_message, user_message_wrapper, section_data_to_send
        )

        if immediate:
            logger.info(f"Running immediate chat process for journal '{journal_name}'.")
            translated_data = []
            for i, message in enumerate(messages):
                max_tokens = max_token_list[i]
                response = run_immediate_chat_process(message, max_tokens=max_tokens)
                translated_data.append(response)
            logger.info(
                f"Immediate translation completed for journal '{journal_name}'."
            )
            return translated_data
        else:
            logger.info(f"Running batch processing for journal '{journal_name}'.")
            # Create batch file for batch processing
            jsonl_file = create_jsonl_file_for_batch(
                messages, batch_jsonl_path, max_token_list=max_token_list
            )
            if not jsonl_file:
                raise RuntimeError("Failed to create JSONL file for translation batch.")

            # Process batch and return the result
            translation_data = start_batch_with_retries(
                jsonl_file,
                description=f"Batch for translating journal '{journal_name}'",
            )
            logger.info(f"Batch translation completed for journal '{journal_name}'.")
            return translation_data

    except Exception as e:
        logger.error(
            f"Error during translation processing for journal '{journal_name}'.",
            exc_info=True,
        )
        raise RuntimeError("Error in translation process.") from e


# Output
def save_cleaned_data(
    cleaned_xml_path: Path, cleaned_wrapped_pages: List[str], journal_name
):
    try:
        logger.info(f"Saving cleaned content to XML for journal '{journal_name}'.")
        cleaned_wrapped_pages = unwrap_all_lines(cleaned_wrapped_pages)
        save_pages_to_xml(cleaned_xml_path, cleaned_wrapped_pages, overwrite=True)
        logger.info(f"Cleaned journal saved successfully to:\n\t{cleaned_xml_path}")
    except Exception as e:
        logger.error(
            f"Failed to save cleaned data for journal '{journal_name}'.",
            extra={"cleaned_xml_path": cleaned_xml_path},
            exc_info=True,
        )
        raise RuntimeError(
            f"Failed to save cleaned data for journal '{journal_name}'."
        ) from e


def save_sectioning_data(
    output_json_path: Path, raw_output_path: Path, serial_json: str, journal_name
):
    try:
        raw_output_path.write_text(serial_json, encoding="utf-8")
    except Exception as e:
        logger.error(
            f"Failed to write raw response file for journal '{journal_name}'.",
            extra={"raw_output_path": raw_output_path},
            exc_info=True,
        )
        raise RuntimeError(
            f"Failed to write raw response file for journal '{journal_name}'."
        ) from e

    # Validate and save metadata
    try:
        valid = validate_and_save_metadata(
            output_json_path, serial_json, journal_schema
        )
        if not valid:
            raise RuntimeError(
                f"Validation failed for metadata of journal '{journal_name}'."
            )
    except Exception as e:
        logger.error(
            f"Error occurred while validating and saving metadata for journal '{journal_name}'.",
            extra={"output_json_path": output_json_path},
            exc_info=True,
        )
        raise RuntimeError(f"Validation error for journal '{journal_name}'.") from e

    return output_json_path


def save_translation_data(xml_output_path: Path, translation_data, journal_name):
    # Save translated content back to XML
    try:
        logger.info(f"Saving translated content to XML for journal '{journal_name}'.")
        join_xml_data_to_doc(xml_output_path, translation_data, overwrite=True)
        logger.info(f"Translated journal saved successfully to:\n\t{xml_output_path}")

    except Exception as e:
        logger.error(
            f"Failed to save translation data for journal '{journal_name}'.",
            extra={"xml_output_path": xml_output_path},
            exc_info=True,
        )
        raise RuntimeError(
            f"Failed to save translation data for journal '{journal_name}'."
        ) from e


# JSON helpers
def deserialize_json(serialized_data: str):
    """
    Converts a serialized JSON string into a Python dictionary.

    Args:
        serialized_data (str): The JSON string to deserialize.

    Returns:
        dict: The deserialized Python dictionary.
    """
    if not isinstance(serialized_data, str):
        logger.error(
            f"String input required for deserialize_json. Received: {type(serialized_data)}"
        )
        raise ValueError("String input required.")

    try:
        # Convert the JSON string into a dictionary
        return json.loads(serialized_data)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to deserialize JSON: {e}")
        raise


# generate a batch from xml page file
# depricated
def generate_single_oa_batch_from_pages(
    input_xml_file: str,
    output_file: str,
    system_message: str,
    user_wrap_function,
):
    """
    *** Depricated ***
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
