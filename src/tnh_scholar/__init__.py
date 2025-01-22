"""TNH Scholar: Text Processing and Analysis Tools

TNH Scholar is an AI-driven project designed to explore, query, process and translate
the teachings of Thich Nhat Hanh and other Plum Village Dharma Teachers. The project aims 
to create a resource for practitioners and scholars to deeply engage with mindfulness 
and spiritual wisdom through natural language processing and machine learning models.

Core Features:
    - Audio transcription and processing
    - Multi-lingual text processing and translation
    - Pattern-based text analysis
    - OCR processing for historical documents
    - CLI tools for batch processing

Package Structure:
    - tnh_scholar/
       - CLI_tools/          - Command line interface tools
       - audio_processing/   - Audio file handling and transcription
       - journal_processing/ - Journal and publication processing
       - ocr_processing/     - Optical character recognition tools
       - openai_interface/   - OpenAI API integration
       - text_processing/    - Core text processing utilities
       - video_processing/   - Video file handling and transcription
       - utils/             - Shared utility functions
       - xml_processing/    - XML parsing and generation

Environment Configuration:
    - The package uses environment variables for configuration, including:
       - TNH_PATTERN_DIR - Directory for text processing patterns
       - OPENAI_API_KEY     - OpenAI API authentication
       - GOOGLE_VISION_KEY  - Google Cloud Vision API key for OCR

CLI Tools:
    - audio-transcribe  - Audio file transcription utility
    - tnh-fab          - Text processing and analysis toolkit

For more information, see:
    - Documentation: https://aaronksolomon.github.io/tnh-scholar/
    - Source: https://github.com/aaronksolomon/tnh-scholar
    - Issues: https://github.com/aaronksolomon/tnh-scholar/issues

Dependencies:
    - Core: click, pydantic, openai, yt-dlp
    - Optional: streamlit (GUI), spacy (NLP), google-cloud-vision (OCR)
"""

from pathlib import Path

# Package version
__version__ = "0.1.0"

from pathlib import Path

# Dynamically determine and set up paths for the project
TNH_ROOT_SRC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT_DIR = (
    TNH_ROOT_SRC_DIR.resolve().parent.parent
)  # always assume structure is: root_dir/src/TNH_BASE_DIR
CLI_TOOLS_DIR = TNH_ROOT_SRC_DIR / "cli_tools"
LOG_DIR = PROJECT_ROOT_DIR / "logs"
DEFAULT_PATTERN_DIR = Path.home() / ".config" / "tnh_scholar" / "patterns"

# Ensure pattern directory exists
DEFAULT_PATTERN_DIR.mkdir(parents=True, exist_ok=True)

if not TNH_ROOT_SRC_DIR.exists():
    raise FileNotFoundError(f"Base directory {TNH_ROOT_SRC_DIR} does not exist.")
if not CLI_TOOLS_DIR.exists():
    raise FileNotFoundError(f"CLI tools directory {CLI_TOOLS_DIR} does not exist.")


