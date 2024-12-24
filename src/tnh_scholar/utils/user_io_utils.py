import sys
import os

if os.name == 'nt':  # Windows
    import msvcrt
else:  # Unix-like (Linux, macOS)
    import tty
    import termios

def get_single_char() -> str:
    """
    Get a single character from standard input without requiring Enter.
    Cross-platform implementation for Windows and Unix-like systems.
    """
    if os.name == 'nt':
        return msvcrt.getch().decode('utf-8')  # Windows
    else:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            char = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return char

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
        if char == 'y':
            print(char)  # Echo the choice
            return True
        elif char == 'n':
            print(char)
            return False
        elif char in ('\r', '\n'):  # Enter key (use default)
            print()  # Add a newline
            return default
        else:
            print(f"\nInvalid input: {char}. Please type 'y' or 'n': ", end="", flush=True)

