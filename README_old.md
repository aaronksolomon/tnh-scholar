# TNH Scholar

**TNH Scholar** is an AI-driven project designed to explore, query, process and translate the teachings of Thich Nhat Hanh and other Plum Village Monastics. The project aims to create a resource for practitioners and scholars to deeply engage with mindfulness and spiritual wisdom through natural language processing and machine learning models.

## Project Overview

This project leverages machine learning models, including fine-tuned BERT, GPT, MarianMT (and potentially other) models, to support:

- **Text Query and Search**: Retrieve relevant passages from Thich Nhat Hanh's writings, Dharma talks, and interviews.
- **Conversational Interactions**: Explore teachings interactively using a fine-tuned GPT-based system.
- **Multilingual Translation and Transcription**: Transcribe (from audio or other sources) and Translate texts across Thich Nhat Hanh's (and other Dharma Teachers') primary teaching languages—English, Vietnamese, and French.

### Current Goals

- Start with a proof-of-concept implementation using a small dataset of English texts.
- Evaluate model performance across querying, translation, transcription and simple interactive tasks.
- Gradually expand the dataset to include transcriptions of Dharma talks and interactive sessions, and support multiple languages.

### Current Progress and Status

- Version 0.1.0 'initial prototyping' is relatively stable with CLI tools: audio-transcribe, tnh-fab, ytt-fetch, nfmt, tnh-setup being functional.
- Text processing (primarily cleaning and sectioning) of sample ebooks (*Transformation and Healing* and *Love in Action*) completed as a test run of these processes. Proof of concept query-text pairs successfully generated via gpt-4o using the OpenAI API. **See notebooks/query_text_generation**.
- OCR processing of Thay's old 1950's 'Phat Giao Viet Nam' journals was completed through jupyter notebook processing. **See notebooks/journal_processing**
- A segment of Deer Park Dharma talks from youtube was downloaded, transcribed and processed/cleaned to xml using jupyter notebooks and audio-transcribe cli tool.
- Baseline functionality for ai text processing through Jupyter notebooks using 'patterns' in the style of Daniel Messier's 'fabric' is functional with functions: **punctuate_text, find_sections, translate_text_by_lines, process_text_by_sections, process_text_by_paragraphs**.
- Next steps are to implement a CLI tool: tnh-fab which will allow CLI access to these core functionalities for ai text processing through the command line. see

### Notes and Configurations

- Developed on MacOS. All filenames and directories are in lowercase to accommodate non-case sensitive default of MacOS.

## Directory Structure

The repository is organized as follows:

/src

- The source code in python for the project

/notebooks

- All jupyter notebooks used with the project

/data_processing

- Datasets and preprocessing scripts.
- Includes textual datasets such as books, Dharma talks, interviews in English, Vietnamese, and French.

/models

- Fine-tuning and training scripts.
- Scripts to fine-tune models (BERT for query, GPT for interaction, MarianMT for translation).

/evaluation

- Preliminary evaluation and testing scripts.
- Includes evaluation scripts to test model performance on dataset subsets.

/docs

- Documentation for the project setup, training processes, and progress.
- To include project goals, design, feasibility, steps, etc.

## Models and Tools

We are starting by evaluating the following models and tools:

- **BERT** for text query and search, focusing on retrieving relevant teachings.
- **GPT** for interactive textual exploration (using GPT-3.5 via OpenAI API, testing with GPT-2, ?diablo?).
- **MarianMT** or **mBART** for multilingual translation tasks (starting with English, Vietnamese, and French).
  
Additional tools:

- **Google Cloud** Planned use for data storage and deployment. Current use: Google vision for OCR.
- **Hugging Face** Potential use for model hosting and fine-tuning frameworks. Likely alternate is OpenAI API and Anthropic API. These professional level API's offering more robust support (however require cost of use, account creation).

## Setup Instructions

### Prerequisites

- **Python 3.12+** with necessary packages (see `requirements.txt`).
- **Hugging Face API** and **OpenAI API** access for model training and interaction.
- **Google Cloud SDK** for cloud-based infrastructure; currently used for Google vision to process OCR data.

### Steps

1. **Clone the repository**:

- git clone <https://github.com/aaronksolomon/tnh-scholar.git>
- cd tnh-scholar
  
2. **Install dependencies**:

  pip install  <- NEEDS FIX

3. **Data Preparation**:

- Place datasets in the `/data` directory.
- Use preprocessing scripts in `/data` to clean and tokenize the data as needed.

4. **Model Fine-Tuning**:

- Fine-tuning scripts are located in `/models`.
- Run fine-tuning for each model (query, translation, interaction) based on the instructions in `docs/fine_tuning.md`.

5. **Evaluation**:

- Evaluation scripts are located in `/evaluation`.
- Use these scripts to test the models on specific tasks, and view performance metrics.

## Future Plans

- Expand the dataset to include more texts, transcriptions of Dharma talks, and additional languages.
- Improve model fine-tuning for better contextual understanding and nuanced translations.
- Deploy a user-friendly interface for practitioners to query and interact with the system.

## Contributions

This project depends on contributions! Please check the `CONTRIBUTING.md` file for guidelines on how to contribute to this project.

## License

This project is licensed under the [GPL-3.0 License](LICENSE) - see the `LICENSE.md` file for details.
