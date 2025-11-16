import os
import sys
from typing import List, Set

from tnh_scholar.logging_config import get_child_logger

logger = get_child_logger(__name__)

def get_env_message(missing_vars: List[str], feature: str = "this feature") -> str:
    """Generate user-friendly environment setup message.
    
    Args:
        missing_vars: List of missing environment variable names
        feature: Name of feature requiring the variables
        
    Returns:
        Formatted error message with setup instructions
    """
    export_cmds = " ".join(f"{var}=your_{var.lower()}_here" for var in missing_vars)
    
    return "\n".join([
        f"\nEnvironment Error: Missing required variables for {feature}:",
        ", ".join(missing_vars),
        "\nSet variables in your shell:",
        f"export {export_cmds}",
        "\nSee documentation for details.",
        "\nFor development: Add to .env file in project root.\n"
    ])

def check_env(required_vars: Set[str], feature: str = "this feature", output: bool = True) -> bool:
    """
    Check environment variables and provide user-friendly error messages.
    
    Args:
        required_vars: Set of environment variable names to check
        feature: Description of feature requiring these variables
        
    Returns:
        bool: True if all required variables are set
    """
    if missing := [var for var in required_vars if not os.getenv(var)]:
        if output:
            message = get_env_message(missing, feature)
            logger.error(f"Missing environment variables: {', '.join(missing)}")
            print(message, file=sys.stderr)
        return False
    return True

# Pre-defined checks
OPENAI_ENV_VARS = {"OPENAI_API_KEY"}
OCR_ENV_VARS = {"GOOGLE_APPLICATION_CREDENTIALS"}

def check_openai_env(output: bool = True) -> bool:
    """Check OpenAI API requirements."""
    return check_env(OPENAI_ENV_VARS, "OpenAI API access", output=output)
    
def check_ocr_env(output: bool = True) -> bool:
    """Check OCR processing requirements."""
    return check_env(OCR_ENV_VARS, "OCR processing", output=output)