# --- Prototype: for viewing Speaker Blocks with Streamlit ---

import io
import json
import os
import signal
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import List

import plotly.colors as pc
import plotly.graph_objects as go
import streamlit as st

from tnh_scholar.audio_processing.diarization.models import SpeakerBlock
from tnh_scholar.utils import TNHAudioSegment as AudioSegment

# from tnh_scholar.utils.timing_utils import TimeMs


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

    # --- Deserialize SpeakerBlocks from dicts ---
    blocks = [SpeakerBlock.from_dict(seg) for seg in segments]

    # Enable wide mode for Streamlit app
    st.set_page_config(layout="wide")
    st.write("## Segment Timeline Plot (seconds)")
    if not blocks:
        st.error("No segment blocks found.")
        st.stop()


    # --- Timeline Plot: group by speaker, color by speaker, number blocks ---
    try:
        speakers = list({block.speaker for block in blocks})
        color_map = {
            spk: pc.qualitative.Plotly[i % len(pc.qualitative.Plotly)] for i, spk in enumerate(speakers)
        }

        fig = go.Figure()
        speaker_blocks = defaultdict(list)
        for idx, block in enumerate(blocks):
            speaker_blocks[block.speaker].append((idx, block))

        bar_thickness = 0.6
        for speaker, items in speaker_blocks.items():
            y_val = speaker
            for idx, block in items:
                start_sec = block.start.to_seconds()
                duration_sec = block.duration.to_seconds()
                fig.add_trace(go.Bar(
                    x=[duration_sec],
                    y=[y_val],
                    base=[start_sec],
                    orientation='h',
                    marker_color=color_map[speaker],
                    name=f"{idx+1}: {speaker}",
                    hovertext=f"{idx+1}: {speaker} ({start_sec:.2f}s-{start_sec+duration_sec:.2f}s)",
                    width=bar_thickness
                ))
        fig.update_layout(
            title="All Segments (seconds)",
            xaxis_title="Time (seconds)",
            yaxis_title="Speaker",
            showlegend=False,
            bargap=0.2,
            barmode="overlay"
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error generating timeline plot: {e}")


    # --- Segment selection via entry box ---
    st.write("## Enter Segment Number to Play")
    max_segment = len(blocks)
    segment_num = st.number_input(
        "Segment number (1-based)",
        min_value=1,
        max_value=max_segment,
        value=1,
        step=1,
        help=f"Enter a segment number between 1 and {max_segment}"
    )
    selected_idx = segment_num - 1

    block = blocks[selected_idx]
    start_ms = block.start.to_ms()
    end_ms = block.end.to_ms()
    st.write(f"Selected Segment: {segment_num} | Speaker: {block.speaker}")
    st.write(
        f"Start: {block.start.to_seconds():.2f}s, "
        f"End: {block.end.to_seconds():.2f}s, "
        f"Duration: {block.duration.to_seconds():.2f}s"
    )

    # --- Play audio for selected segment ---
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