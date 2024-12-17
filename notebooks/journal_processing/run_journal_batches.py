# IMPORTS

# General
import os
import io
from pathlib import Path
from typing import List, Dict
import json
import re
import time
from datetime import datetime
import logging
from math import floor

# OCR processing
from google.cloud import vision
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import fitz  # for pdf work: PyMuPDF
from xml.sax.saxutils import escape

# XML
from xml.sax.saxutils import escape

# LOCAL MODULES

# OCR processing
from data_processing.ocr_processing import (
    make_image_preprocess_mask,
    build_processed_pdf, 
    save_processed_pdf_data, 
)

# GPT processing
from data_processing.gpt_processing import (
    start_batch_with_retries, 
    set_model_settings,
)

# XML
from data_processing.xml_processing import  save_pages_to_xml

# pdf journal processsing
from data_processing.gpt_processing.pdf_journal_process import (
    setup_logger,
    generate_clean_batch, batch_section, batch_translate, 
    save_sectioning_data, save_translation_data, save_cleaned_data
)

# PARAMETERS

# Define your list of journal names
JOURNALS = [
    "phat-giao-viet-nam-1956-13",
    "phat-giao-viet-nam-1956-14",
    "phat-giao-viet-nam-1956-15",
    "phat-giao-viet-nam-1956-16",
    "phat-giao-viet-nam-1956-17-18",
    "phat-giao-viet-nam-1956-19",
    "phat-giao-viet-nam-1956-20-21",
    "phat-giao-viet-nam-1956-22",
    "phat-giao-viet-nam-1956-23",
    "phat-giao-viet-nam-1956-24",
    "phat-giao-viet-nam-1956-25-26",
    "phat-giao-viet-nam-1956-27",
    "phat-giao-viet-nam-1956-28"
]

WAIT_TIME_BETWEEN_BATCHES = 1 * 60  # 1 minutes

# Static Project Paths
project_dir = Path("/Users/phapman/Desktop/tnh-scholar/")
data_dir = project_dir / "data_processing"
pdf_dir = data_dir / "PDF" / "Phat_Giao_journals" # directory to read pdfs from
journal_dir = data_dir / "processed_journal_data"
logfile = data_dir / "gpt_processing" / "pdf_journal_process" / "processing_info.log"

# Settings for OCR cleaning
def user_wrap_function_clean(text_block):   # Function to wrap user message sent to model. Currently no wrapping.
    return text_block  

model_settings_clean = {
    "gpt-4o": {
        "max_tokens": 1000, # default value
        "temperature": 0
    }
}

system_message_clean = """You are a meticulous and consistent world expert at cleaning OCR-generated Vietnamese text. 
You are cleaning pages from a 1950's Buddhist Journal. 
Each line of scanned data will be enclosed in <> brackets. Leave <> brackets in place.
Your goal is to minimally modify the text to generate a cleaned version.
Do not remove any content from the main body of the text. 
Do not change the line formatting. 

You can use the semantic meaning of the text to infer corrections—but make no semantic changes. 
You can also add diacritical marks if they are missing or clearly inaccurate. 
Do not change any proper names, except to add missing diacritical marks or to fix orthographic errors if the context is clear.  

This particular text has a title marker in the footer, "Phat Giao Viet Nam," and also a publishing mark diagonally across the text.  
The publishing watermark is "TU VIEN HUE QUANG"  and is faint so only parts of it may appear in some locations in the text. Remove all text corresponding to the watermark.
Text corresponding to the footer, the publishing watermak (or part thereof), and page numbers can be omitted.

IMPORTANT: If the page is blank return: blank page 
IMPORTANT: Output the corrected text only with no comments (including ``` xml)"""

# Settings for sectioning 
model_settings_section = {
    "gpt-4o": {
        "max_tokens": 10000,
        "temperature": 0.25
    }
}

system_message_section = """You are a highly skilled assistant processing a Vietnamese Buddhist journal scanned from OCR. 
Use the title: "Journal of Vietnamese Buddhism."
You will be determining the journal sections by page number. You will also generate metadata for the full text and each section. 
You will return this metadata in JSON format.

Instructions:
1. Analyze the text and divide it into sections based on logical breaks, such as headings, topic changes, or clear shifts in content.
2. Ensure every page is part of a section. The first title page should always be its own section. Blank pages should be titled "blank page".
3. For each section, provide:
   - The original title in Vietnamese (`section_title_vi`).
   - The translated title in English (`section_title_en`).
   - The author's name if it is available (`section_author`). 
   - A one-paragraph summary of the section in English (`section_summary`).
   - A list of keywords for the section that are related to its content, these can be proper names, specific concepts, or contextual information.
   - The section's start and end page numbers (`start_page` and `end_page`).
   - Use "null" for any data that is not available (such as author name) for the section.

4. Return the output as a JSON object with the following schema:
{
    "journal_summary": "A detailed and thorough summary of the whole journal in English.",
    "sections": [
        {
            "title_vi": "Original title in Vietnamese",
            "title_en": "Translated title in English",
            "author": "Name of the author of the section",
            "summary": "One-paragraph summary of the section in English",
            "keywords": "A list of keywords for the section",
            "start_page":  X,
            "end_page":  Y
        },
        ...
    ]
}

5.  Ensure the JSON is well-formed and adheres strictly to the provided schema.
6.  IMPORTANT: ensure every page is part of a section and sections appear in order of pagination."""

# Settings for translation
model_settings_translate = {
    "gpt-4o": {
        "max_tokens": 5000,  # a default value, updated per batch
        "temperature": 0.75
    }
}

system_message_translate = """You are the world's foremost translator of Zen Master Thich Nhat Hanh's Vietnamese writing into English, following the language style of the plumvillage.org website.
The text is based on an OCR scan of a journal you edited from 1956-1958. Use the title: "Journal of Vietnamese Buddhism" for the journal when it is referenced.
You will be translating a single section of the journal and will be provided with the section title in English. 
Translate for the most meaningful, typical, and eloquent English interpretation that is simple, yet poetic. 
Translate precisely; do not add change the text or add commentary.  
Notes on the text can be added in the <notes>.
Make corrections in the text only where necessary (for example if words are missing) to create logical flow. Note all corrections in the <translation-notes>. 
Do not change <pagebreak> tag postioning. Each translated page must match its original page source as pages will be studied side by side with the original Vietnamese.
Infer paragraphs and text structure from the text layout.
Add XML tags for clarity, using only the following tags: 

   <section> for major sections.
   <subsection> for subsections.
   <title> for main titles of sections and subsections. 
   <subtitle> for subtitles of sections and subsections. 
   <heading> for headings that do not mark titles or subtitles
   <p> for paragraphs.
   <br/> for linebreaks that add meaning such as in poems or other structures.
   <TOC> for tables of contents
   <author> for named authors of sections (only)
   <i> for italics. 
   <b> for bold.
   <notes>
   <translation-notes>

You may use <notes> at the end of the section for notes on historical, cultural, spiritual, or other interesting elements of the text.
You want advanced students of Thay to understand the text in its larger historical context, in the context of Vietnamese Buddhism, and in the context of his life.
You may add <translation-notes> at the end of the section as a commentary to summarize your translation choices. 
For <translation-notes>, you may include information on Sino-Vietnamese, complex, unusual, poetic, or other interesting terms, and significant corrections to the text. 
In the <translation-notes> include the original Vietnamese terms for reference.

IMPORTANT: All titles, XML sections, text, poetry, quotations, and terms MUST BE TRANSLATED TO ENGLISH. Do not however, translate names of people; leave names in Vietnamese with diacritics.
IMPORTANT: Return pure XML with no formatting marks such as xml or ```.
IMPORTANT: The returned XML should begin and end with <section> tags."""

# Initialize logger
logger = setup_logger(logfile)
logger.name = "MAIN process loop"

def batch_init(log_message: str, wait_time=WAIT_TIME_BETWEEN_BATCHES):
    """
    Prints a log message and waits for the specified time, 
    showing progress with a '.' every 5 seconds.
    """
    logger.priority_info(f"{log_message}")
    print(f"\033[93mwaiting {wait_time} seconds between batches...\033[0m", end="", flush=True)    

    interval = 5  # Interval for printing progress dots
    for i in range(0, wait_time, interval):
        print(".", end="", flush=True)  # Print a dot without newline
        time.sleep(interval)
    
    print("")  # Move to the next line after progress dots

    
def process_journal(journal_name: str):
    """Process a single journal, handling all pipeline steps."""
    logger.priority_info(f"Starting processing for journal: {journal_name}")
    
    # Update paths dynamically for the journal
    pdf_to_process = pdf_dir / f"{journal_name}.pdf"
    ocr_data_dir = journal_dir
    working_dir = journal_dir / journal_name
    cleaned_xml_path = working_dir / f"full_cleaned_{journal_name}.xml"
    batch_job_dir = working_dir / "processing_batch_files"
    clean_batch_jsonl = batch_job_dir / f"clean_batch_{journal_name}.jsonl"
    section_batch_jsonl = batch_job_dir / "section_batch.jsonl"
    translate_batch_jsonl = batch_job_dir / "translation_batch.jsonl"
    section_metadata_path = working_dir / "section_metadata.json"
    raw_json_metadata_path = working_dir / "raw_metadata_response.txt"
    translation_xml_path = working_dir / f"translation_{journal_name}.xml"
    ocr_file = journal_dir / journal_name / f"full_OCR_{journal_name}.xml"

    try:
        # Stage 1: Process PDF with OCR
        logger.priority_info("Starting OCR processing.")
        try:
            client = vision.ImageAnnotatorClient()
            pre_mask1 = make_image_preprocess_mask(0.1)
            text_pages, word_locations_list, annotated_images, unannotated_images = build_processed_pdf(pdf_to_process, client, pre_mask1)
            save_processed_pdf_data(ocr_data_dir, journal_name, text_pages, word_locations_list, annotated_images, unannotated_images)
            save_pages_to_xml(working_dir / f"full_OCR_{journal_name}.xml", text_pages, overwrite=True)
        except Exception as e:
            raise RuntimeError(f"OCR processing failed for {journal_name}: {e}")

        # Stage 2: Clean OCR Data
        
        try:
            batch_init(f"Cleaning text for {journal_name}:", wait_time=0)  # no need to wait on first batch.
            set_model_settings(model_settings_clean)
            generate_clean_batch(ocr_file, clean_batch_jsonl, system_message_clean, user_wrap_function_clean)
            job_description = f"cleaning for {journal_name} on {ocr_file}"
            cleaned_data = start_batch_with_retries(clean_batch_jsonl, job_description)
            save_cleaned_data(cleaned_xml_path, cleaned_data, journal_name)
        except Exception as e:
            raise RuntimeError(f"OCR data cleaning failed for {journal_name}: {e}")

        # Stage 3: Divide Text into Sections
        batch_init(f"Sectioning text for {journal_name}:")
        try:
            set_model_settings(model_settings_section)
            metadata_serial_json = batch_section(cleaned_xml_path, section_batch_jsonl, system_message_section, journal_name)
            save_sectioning_data(section_metadata_path, raw_json_metadata_path, metadata_serial_json, journal_name)
        except Exception as e:
            raise RuntimeError(f"Sectioning failed for {journal_name}: {e}")

        # Stage 4: Translate Sections
        batch_init(f"Translating text for {journal_name}")
        try:
            set_model_settings(model_settings_translate)
            translation_data = batch_translate(cleaned_xml_path, translate_batch_jsonl, section_metadata_path, system_message_translate, journal_name)
            save_translation_data(translation_xml_path, translation_data, journal_name)
        except Exception as e:
            raise RuntimeError(f"Translation failed for {journal_name}: {e}")

    except RuntimeError as e:
        logger.error(f"\n\t\033[91m*** Error processing journal {journal_name} ***: {e}\033[0m")
        return False

    return True

# Main execution loop
if __name__ == "__main__":
    logger.priority_info("Starting the journal processing pipeline.")
    for journal_name in JOURNALS:
        result = process_journal(journal_name)
        if not result:
            logger.warning(f"Skipping journal {journal_name} due to errors.")
        else:
            logger.priority_info(f"Successfully completed processing for journal: {journal_name}")

    logger.priority_info("Journal processing pipeline completed.")

# # Process pdf with OCR through google vision
# client = vision.ImageAnnotatorClient()
# pre_mask1 = make_image_preprocess_mask(0.1)  #this masks the bottom 10% of the image where the publishing mark is located
# text_pages, word_locations_list, annotated_images, unannotated_images = build_processed_pdf(pdf_to_process, client, pre_mask1) 

# # Clean OCR data
# set_model_settings(model_settings_clean)
# generate_clean_batch(ocr_file, clean_batch_jsonl, system_message_clean, user_wrap_function_clean)
# job_description = f"cleaning for {journal_name} on {ocr_file}"
# cleaned_data = start_batch_with_retries(clean_batch_jsonl, job_description) # run the clean process
# save_cleaned_data(cleaned_xml_path, cleaned_data, journal_name)

# # Divide text into sections for processing
# set_model_settings(model_settings_section)
# metadata_serial_json = batch_section(cleaned_xml_path, section_batch_jsonl, system_message_section, journal_name) # run the section process
# save_sectioning_data(section_metadata_path, raw_json_metadata_path, metadata_serial_json, journal_name)  

# # Translate sections
# set_model_settings(model_settings_translate)
# translation_data = batch_translate(cleaned_xml_path, translate_batch_jsonl, section_metadata_path, system_message_translate, journal_name)
# save_translation_data(translation_xml_path, translation_data, journal_name)
