import sys
import threading
import time
from typing import Optional

from tqdm import tqdm

BAR_FORMAT = (
    "{desc}: {percentage:3.0f}%|{bar}| " "Total: {total_fmt} sec. [elapsed: {elapsed}]"
)


class ExpectedTimeTQDM:
    """
    A context manager for a time-based tqdm progress bar with optional delay.

    - 'expected_time': number of seconds we anticipate the task might take.
    - 'display_interval': how often (seconds) to refresh the bar.
    - 'desc': a short description for the bar.
    - 'delay_start': how many seconds to wait (sleep) before we even create/start the bar.

    If the task finishes before 'delay_start' has elapsed, the bar may never appear.
    """

    def __init__(
        self,
        expected_time: float,
        display_interval: float = 0.5,
        desc: str = "Time-based Progress",
        delay_start: float = 1.0,
    ) -> None:
        self.expected_time = round(expected_time)  # use nearest second.
        self.display_interval = display_interval
        self.desc = desc
        self.delay_start = delay_start

        self._stop_event = threading.Event()
        self._pbar = None  # We won't create the bar until after 'delay_start'
        self._start_time = None

    def __enter__(self):
        # Record the start time for reference
        self._start_time = time.time()

        # Spawn the background thread; it will handle waiting and then creating/updating the bar
        self._thread = threading.Thread(target=self._update_bar, daemon=True)
        self._thread.start()

        return self

    def _update_bar(self):
        # 1) Delay so warnings/logs can appear before the bar
        if self.delay_start > 0:
            time.sleep(self.delay_start)

        # 2) Create the tqdm bar (only now does it appear)
        self._pbar = tqdm(
            total=self.expected_time, desc=self.desc, unit="sec", bar_format=BAR_FORMAT
        )

        # 3) Update until told to stop
        while not self._stop_event.is_set():
            elapsed = time.time() - self._start_time
            current_value = min(elapsed, self.expected_time)
            if self._pbar:
                self._pbar.n = round(current_value)
                self._pbar.refresh()
            time.sleep(self.display_interval)

    def __exit__(self, exc_type, exc_value, traceback):
        # Signal the thread to stop
        self._stop_event.set()
        self._thread.join()

        # If the bar was actually created (i.e., we didn't finish too quickly),
        # do a final update and close
        if self._pbar:
            elapsed = time.time() - self._start_time
            self._pbar.n = round(min(elapsed, self.expected_time))
            self._pbar.refresh()
            self._pbar.close()

    import time




class TimeProgress:
    """
    A context manager for a time-based progress display using dots.

    The display updates once per second, printing a dot and showing:
    - Expected time (if provided)
    - Elapsed time (always displayed)

    Example:
    >>> import time
    >>> with ExpectedTimeProgress(expected_time=60, desc="Transcribing..."):
    ...     time.sleep(5)  # Simulate work
    [Expected Time: 1:00, Elapsed Time: 0:05] .....

    Args:
        expected_time (Optional[float]): Expected time in seconds. Optional.
        display_interval (float): How often to print a dot (seconds).
        desc (str): Description to display alongside the progress.
    """

    def __init__(
        self,
        expected_time: Optional[float] = None,
        display_interval: float = 1.0,
        desc: str = "",
    ):
        self.expected_time = expected_time
        self.display_interval = display_interval
        self._stop_event = threading.Event()
        self._start_time = None
        self._thread = None
        self.desc = desc
        self._last_length = 0  # To keep track of the last printed line length

    def __enter__(self):
        # Record the start time
        self._start_time = time.time()

        # Spawn the background thread
        self._thread = threading.Thread(target=self._print_progress, daemon=True)
        self._thread.start()

        return self

    def _print_progress(self):
        """
        Continuously prints progress alternating between | and — along with elapsed/expected time.
        """
        symbols = ["|", "/", "—", "\\"]  # Symbols to alternate between
        symbol_index = 0  # Keep track of the current symbol

        while not self._stop_event.is_set():
            elapsed = time.time() - self._start_time

            # Format elapsed time as mm:ss
            elapsed_str = self._format_time(elapsed)

            # Format expected time if provided
            if self.expected_time is not None:
                expected_str = self._format_time(self.expected_time)
                header = f"{self.desc} [Expected Time: {expected_str}, Elapsed Time: {elapsed_str}]"
            else:
                header = f"{self.desc} [Elapsed Time: {elapsed_str}]"

            # Get the current symbol for the spinner
            spinner = symbols[symbol_index]

            # Construct the line with the spinner
            line = f"\r{header} {spinner}"

            # Write to stdout
            sys.stdout.write(line)
            sys.stdout.flush()

            # Update the symbol index to alternate
            symbol_index = (symbol_index + 1) % len(symbols)

            # Sleep before next update
            time.sleep(self.display_interval)

        # Clear the spinner after finishing
        sys.stdout.write("\r" + " " * len(line) + "\r")
        sys.stdout.flush()

    def __exit__(self, exc_type, exc_value, traceback):
        # Signal the thread to stop
        self._stop_event.set()
        self._thread.join()

        # Final elapsed time
        elapsed = time.time() - self._start_time
        elapsed_str = self._format_time(elapsed)

        # Construct the final line
        if self.expected_time is not None:
            expected_str = self._format_time(self.expected_time)
            final_header = f"{self.desc} [Expected Time: {expected_str}, Elapsed Time: {elapsed_str}]"
        else:
            final_header = f"{self.desc} [Elapsed Time: {elapsed_str}]"

        # Final dots
        final_line = f"\r{final_header}"

        # Clear the line and move to the next line
        padding = " " * max(self._last_length - len(final_line), 0)
        sys.stdout.write(final_line + padding + "\n")
        sys.stdout.flush()

    @staticmethod
    def _format_time(seconds: float) -> str:
        """
        Converts seconds to a formatted string (mm:ss).
        """
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02}"
