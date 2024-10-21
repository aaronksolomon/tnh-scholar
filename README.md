# TNH Scholar

**TNH Scholar** is an AI-driven project designed to explore, query, and translate the teachings of Thich Nhat Hanh. The project aims to create a resource for practitioners and scholars to deeply engage with mindfulness and spiritual wisdom through natural language processing and machine learning models.

## Project Overview

This project leverages machine learning models, including fine-tuned BERT, GPT, MarianMT (and potentially other) models, to support:
- **Text Query and Search**: Retrieve relevant passages from Thich Nhat Hanh's writings, Dharma talks, and interviews.
- **Conversational Interactions**: Explore teachings interactively using a fine-tuned GPT-based system.
- **Multilingual Translation**: Translate texts across Thich Nhat Hanh's primary teaching languages—English, Vietnamese, and French.

### Current Goals
- Start with a proof-of-concept implementation using a small dataset of English texts.
- Evaluate model performance across querying, translation, and interactive tasks.
- Gradually expand the dataset to include transcriptions of Dharma talks and interactive sessions, and support multiple languages.

## Directory Structure

The repository is organized as follows:

/data
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
  - Includes project goals, steps, and setup instructions.

## Models and Tools

We are starting by evaluating the following models and tools:
- **BERT** for text query and search, focusing on retrieving relevant teachings.
- **GPT** for interactive textual exploration (using GPT-3.5 via OpenAI API, testing with GPT-2, ?diablo?).
- **MarianMT** or **mBART** for multilingual translation tasks (starting with English, Vietnamese, and French).
  
Additional tools:
- **Google Cloud** for data storage, model training, and deployment.
- **Hugging Face** for model hosting and fine-tuning frameworks.

## Setup Instructions

### Prerequisites
- **Python 3.11+** with necessary packages (see `requirements.txt`).
- **Hugging Face API** and **OpenAI API** access for model training and interaction.
- **Google Cloud SDK** for cloud-based infrastructure.

### Steps

1. **Clone the repository**:
- git clone https://github.com/your-username/tnh-scholar.git
- cd tnh-scholar
  
2. **Install dependencies**:
- pip install -r requirements.txt

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
