# --- Prototype: Function wrapper for launching Streamlit with temp data ---
import io
import json
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List

import pandas as pd
import plotly.express as px
import streamlit as st

from tnh_scholar.audio_processing.diarization.models import SpeakerBlock
from tnh_scholar.utils import TNHAudioSegment as AudioSegment


def launch_segment_viewer(segments: List[SpeakerBlock], master_audio_file: Path):
    """
    Export segment data to a temporary JSON file and launch Streamlit viewer.
    Args:
        segments: List of dicts with diarization info (start, end, speaker).
        master_audio_file: Path to the master audio file.
    """
    # Attach master audio file path to metadata
    meta = {"master_audio": str(master_audio_file)}
    serial_segments = [segment.to_dict() for segment in segments]
    payload = {"segments": serial_segments, "meta": meta}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(payload, f)
        temp_path = f.name
    cmd = [sys.executable, "-m", "streamlit", "run", str(Path(__file__).resolve()), "--", temp_path]
    print(f"Launching Streamlit viewer with data: {temp_path}")
    proc = subprocess.Popen(cmd)
    return proc.pid

# --- Helper to close Streamlit viewer by PID ---
def close_segment_viewer(pid: int):
    """Terminate the Streamlit viewer process by PID."""
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Closed Streamlit viewer (PID {pid})")
    except Exception as e:
        print(f"Failed to close Streamlit viewer (PID {pid}): {e}")

# --- Main Streamlit App ---
def load_segments_from_file(path):
    with open(path, "r") as f:
        return json.load(f)

def main():
    # If a data file is passed as argument, load it


    segments = None
    meta = None
    error_msg = None
    if len(sys.argv) > 1 and os.path.exists(sys.argv[-1]):
        try:
            payload = load_segments_from_file(sys.argv[-1])
            segments = payload.get("segments")
            meta = payload.get("meta")
        except Exception as e:
            error_msg = f"Failed to load segment data: {e}"
    else:
        st.error("No segment data file provided. This viewer requires explicit segment and audio file input.")
        st.stop()

    if error_msg:
        st.error(error_msg)
        st.stop()

    if not segments or not meta or not meta.get("master_audio"):
        st.error("Segments and master audio file must be provided.")
        st.stop()

    master_audio_path = meta["master_audio"]

    # Show first block only
    first_block = segments[0] if segments else None
    if not first_block:
        st.error("No segment blocks found.")
        st.stop()

    st.write("## First SpeakerBlock Data")
    st.json(first_block)

    # Extract start/end in seconds, ensure float
    start_ms = first_block.get("start", 0)
    end_ms = first_block.get("end", 0)
    st.write(f"Start: {start_ms}ms, End: {end_ms}s, Duration: {end_ms - start_ms}ms")

    # Play audio for this segment
    try:
        audio = AudioSegment.from_file(master_audio_path)
        segment_audio = audio[start_ms:end_ms]
        buf = io.BytesIO()
        segment_audio.export(buf, format="wav")
        st.audio(buf.getvalue(), format="audio/wav")
    except Exception as e:
        st.error(f"Error extracting or playing audio segment: {e}")

if __name__ == "__main__":
    # Only run Streamlit app if called as main
    main()