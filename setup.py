from setuptools import setup, find_packages

setup(
    name='tnh-scholar',
    version='0.1',
    packages=find_packages(include=['data_processing', 'data_processing.*']),
    install_requires=[
        beautifulsoup4==4.12.3
        click==8.1.7
        colorlog==6.9.0
        EbookLib==0.17
        fitz==0.0.1.dev2
        lxml==5.3.0
        openai==1.57.4
        openai_whisper==20240930
        pdf2image==1.17.0
        Pillow==11.0.0
        protobuf==5.29.1
        pydantic==2.10.3
        pydub==0.25.1
        python-dotenv==1.0.1
        setuptools==75.6.0
        spacy==3.7.6
        streamlit==1.40.1
        tiktoken==0.8.0
        transformers==4.47.0
        yt_dlp==2024.12.13
    ],  # Add any dependencies here
    entry_points={
        "console_scripts": [
            "audio-transcribe=CLI_tools.audio_transcribe.audio_transcribe:main",
        ],
    },
)