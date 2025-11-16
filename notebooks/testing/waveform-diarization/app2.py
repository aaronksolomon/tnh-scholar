from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

# --- Load audio and make a data URL so the iframe can load it directly ---
audio_path: Path = Path(__file__).parent / "test_audio.mp3"
audio_bytes: bytes = audio_path.read_bytes()
audio_b64: str = base64.b64encode(audio_bytes).decode("ascii")
audio_data_url: str = f"data:audio/mpeg;base64,{audio_b64}"

html = f"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <script src="https://unpkg.com/wavesurfer.js@7"></script>
    <style>
      html, body {{ margin: 0; padding: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }}
      #wrap {{ padding: 12px; }}
      #wave {{ height: 180px; width: 100%; }}
      #play {{ margin-top: 12px; }}
    </style>
  </head>
  <body>
    <div id="wrap">
      <div id="wave"></div>
      <button id="play">Play/Pause</button>
    </div>
    <script>
      const wavesurfer = WaveSurfer.create({{
        container: "#wave",
        waveColor: "#9aa5b1",
        progressColor: "#4c78dd",
        backend: "MediaElement",
        url: "{audio_data_url}",
        height: 180,
        minPxPerSec: 80,
        interact: true,
        dragToSeek: true
      }});
      document.getElementById("play").onclick = () => wavesurfer.playPause();
    </script>
  </body>
</html>
"""

components.html(html, height=280, scrolling=False)