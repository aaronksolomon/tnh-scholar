import os
import sys

if os.name == "nt":  # Windows
    pass
else:  # Unix-like (Linux, macOS)
    pass


import os
from typing import Optional


def get_single_char(prompt: Optional[str] = None) -> str:
    """
    Get a single character from input, adapting to the execution environment.
    
    Args:
        prompt: Optional prompt to display before getting input
        
    Returns:
        A single character string from user input
        
    Note:
        - In terminal environments, uses raw input mode without requiring Enter
        - In Jupyter/IPython, falls back to regular input with message about Enter
    """
    # Check if we're in IPython/Jupyter
    is_notebook = hasattr(sys, 'ps1') or bool(sys.flags.interactive)

    if prompt:
        print(prompt, end='', flush=True)

    if is_notebook:
        # Jupyter/IPython environment - use regular input
        entry = input("Single character input required ")
        return entry[0] if entry else "\n" # Use newline if no entry
    
    # Terminal environment
    if os.name == "nt":  # Windows
        import msvcrt
        return msvcrt.getch().decode("utf-8")
    else:  # Unix-like
        import termios
        import tty

        try:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                char = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return char
        except termios.error:
            # Fallback if terminal handling fails
            return input("Single character input required ")[0]


def get_user_confirmation(prompt: str, default: bool = True) -> bool:
    """
    Prompt the user for a yes/no confirmation with single-character input.
    Cross-platform implementation. Returns True if 'y' is entered, and False if 'n'
    Allows for default value if return is entered.

    Example usage
        if get_user_confirmation("Do you want to continue"):
            print("Continuing...")
        else:
            print("Exiting...")
    """
    print(f"{prompt} ", end="", flush=True)

    while True:
        char = get_single_char().lower()
        if char == "y":
            print(char)  # Echo the choice
            return True
        elif char == "n":
            print(char)
            return False
        elif char in ("\r", "\n"):  # Enter key (use default)
            print()  # Add a newline
            return default
        else:
            print(
                f"\nInvalid input: {char}. Please type 'y' or 'n': ", end="", flush=True
            )
