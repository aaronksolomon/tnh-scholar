from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

import streamlit as st
import streamlit.components.v1 as components

# ========== APP CONFIG ==========
st.set_page_config(layout="wide", page_title="WaveSurfer Progressive Stages")

# ========== AUDIO SOURCE (upload or local file) ==========
def to_data_url(path: Path) -> str:
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    # If you use .wav, change MIME accordingly (e.g., audio/wav)
    return f"data:audio/mpeg;base64,{b64}"

def pick_audio() -> Optional[str]:
    col_left, col_right = st.columns([1, 2])
    with col_left:
        up = st.file_uploader("Upload audio (mp3/wav)", type=["mp3", "wav"])
    if up is not None:
        bytes_ = up.getvalue()
        mime = "audio/wav" if up.name.lower().endswith(".wav") else "audio/mpeg"
        b64 = base64.b64encode(bytes_).decode("ascii")
        return f"data:{mime};base64,{b64}"

    # fallback to local file next to this script
    fallback = Path(__file__).parent / "test_audio.mp3"
    if fallback.exists():
        with col_right:
            st.info(f"Using fallback: {fallback.name}")
        return to_data_url(fallback)

    with col_right:
        st.error("No audio provided. Upload a file or place 'test_audio.mp3' next to this script.")
    return None

audio_url = pick_audio()
if not audio_url:
    st.stop()

# Small helper to render a stage safely with a unique DOM id suffix
def render_stage(stage_id: str, html_body: str, height: int = 260) -> None:
    # Each stage gets its own bundled HTML with unique element ids via {stage_id}
    html = f"""<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <!-- Core -->
    <script src="https://unpkg.com/wavesurfer.js@7"></script>
    <!-- Plugins (needed for Stages 2–4) -->
    <script src="https://unpkg.com/wavesurfer.js@7/dist/plugins/timeline.min.js"></script>
    <script src="https://unpkg.com/wavesurfer.js@7/dist/plugins/regions.min.js"></script>

    <style>
      html, body {{ margin: 0; padding: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }}
      .wrap-{stage_id} {{ padding: 12px; }}
      .row {{ display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }}
      .status {{ margin-top: 8px; font-size: 12px; color: #666; }}
      .wave {{ height: 160px; width: 100%; outline: none; }}
      .timeline {{ height: 36px; }}
      button {{ padding: 6px 10px; }}
      .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace; font-size: 12px; }}
    </style>
  </head>
  <body>
    {html_body}

    <script>
      // Optional: quick guard to help diagnose missing plugin scripts.
      if (typeof WaveSurfer === 'undefined') {{
        console.error('WaveSurfer core failed to load');
      }} else {{
        if (!WaveSurfer.Timeline) console.warn('Timeline plugin not loaded');
        if (!WaveSurfer.Regions)  console.warn('Regions plugin not loaded');
      }}
    </script>
  </body>
</html>"""
    components.html(html, height=height, scrolling=False)

st.title("WaveSurfer Progressive Prototype (Stages)")

# ========== STAGE 1: bare waveform + play/pause ==========
st.subheader("Stage 1 — Bare waveform + Play/Pause")
stage_id = "s1"
body = f"""
<div class="wrap-{stage_id}">
  <div id="wave-{stage_id}" class="wave" tabindex="0"></div>
  <div class="row">
    <button id="play-{stage_id}">Play/Pause</button>
  </div>
  <div id="status-{stage_id}" class="status mono">init…</div>
</div>
<script>
  const statusEl = document.getElementById("status-{stage_id}");
  function setStatus(msg) {{ statusEl.textContent = msg; }}

  try {{
    const ws = WaveSurfer.create({{
      container: "#wave-{stage_id}",
      url: "{audio_url}",
      height: 160,
      minPxPerSec: 80,
      waveColor: "#9aa5b1",
      progressColor: "#4c78dd",
      backend: "MediaElement",
    }});
    document.getElementById("play-{stage_id}").onclick = () => ws.playPause();
    ws.on("ready", () => setStatus("ready"));
    ws.on("play",  () => setStatus("playing"));
    ws.on("pause", () => setStatus("paused"));
  }} catch (e) {{
    console.error(e);
    setStatus("init error: " + (e?.message || e));
  }}
</script>
"""
render_stage(stage_id, body, height=240)

# ========== STAGE 2: + timeline plugin, stable zoom controls ==========
st.subheader("Stage 2 — + Timeline plugin, Zoom controls (ready-gated)")
stage_id = "s2"
body = f"""
<div class="wrap-{stage_id}">
  <div id="timeline-{stage_id}" class="timeline"></div>
  <div id="wave-{stage_id}" class="wave" tabindex="0"></div>
  <div class="row">
    <button id="play-{stage_id}" disabled>Play/Pause</button>
    <button id="zin-{stage_id}"  disabled>Zoom +</button>
    <button id="zout-{stage_id}" disabled>Zoom -</button>
    <span class="mono" id="zoomval-{stage_id}"></span>
  </div>
  <div id="status-{stage_id}" class="status mono">init…</div>
</div>
<script>
  let pxPerSec_{stage_id} = 100;
  let isReady_{stage_id} = false;

  const statusEl = document.getElementById("status-{stage_id}");
  const zoomEl   = document.getElementById("zoomval-{stage_id}");
  const btnPlay  = document.getElementById("play-{stage_id}");
  const btnIn    = document.getElementById("zin-{stage_id}");
  const btnOut   = document.getElementById("zout-{stage_id}");
  function setStatus(msg) {{ statusEl.textContent = msg; }}
  function setZoomVal()  {{ zoomEl.textContent = "pxPerSec=" + pxPerSec_{stage_id}.toFixed(1); }}

  try {{
    const ws = WaveSurfer.create({{
      container: "#wave-{stage_id}",
      url: "{audio_url}",
      height: 160,
      minPxPerSec: pxPerSec_{stage_id},
      waveColor: "#9aa5b1",
      progressColor: "#4c78dd",
      backend: "MediaElement",
      plugins: [ WaveSurfer.Timeline.create({{ container: "#timeline-{stage_id}" }}) ]
    }});

    // enable controls on ready
    ws.on("ready", () => {{
      isReady_{stage_id} = true;
      btnPlay.disabled = btnIn.disabled = btnOut.disabled = false;
      setStatus("ready");
      setZoomVal();
    }});
    ws.on("play",  () => setStatus("playing"));
    ws.on("pause", () => setStatus("paused"));
    ws.on("seek",  p  => setStatus("seek " + p.toFixed(3)));

    // controls (guarded)
    btnPlay.onclick = () => {{ if (isReady_{stage_id}) ws.playPause(); }};
    btnIn.onclick   = () => {{
      pxPerSec_{stage_id} = Math.min(pxPerSec_{stage_id} * 1.25, 2000);
      if (isReady_{stage_id}) ws.zoom(pxPerSec_{stage_id});
      setZoomVal();
    }};
    btnOut.onclick  = () => {{
      pxPerSec_{stage_id} = Math.max(pxPerSec_{stage_id} / 1.25, 20);
      if (isReady_{stage_id}) ws.zoom(pxPerSec_{stage_id});
      setZoomVal();
    }};
  }} catch (e) {{
    console.error(e);
    setStatus("init error: " + (e?.message || e));
  }}
</script>
"""
render_stage(stage_id, body, height=300)

# ========== STAGE 3: + Regions plugin (demo regions), drag/resize, diagnostics ==========
st.subheader("Stage 3 — + Regions (drag/resize), per-event diagnostics")
stage_id = "s3"
body = f"""
<div class="wrap-{stage_id}">
  <div id="timeline-{stage_id}" class="timeline"></div>
  <div id="wave-{stage_id}" class="wave" tabindex="0"></div>
  <div class="row">
    <button id="play-{stage_id}">Play/Pause</button>
    <button id="zin-{stage_id}">Zoom +</button>
    <button id="zout-{stage_id}">Zoom -</button>
    <span class="mono" id="zoomval-{stage_id}"></span>
  </div>
  <div class="mono" id="diag-{stage_id}" style="margin-top:6px; white-space: pre; background:#f7f7f9; padding:6px; border:1px solid #eee;"></div>
</div>
<script>
  let pxPerSec_s3 = 120;

  const diag = document.getElementById("diag-s3");
  function logDiag(obj) {
    const t = (new Date()).toLocaleTimeString();
    diag.textContent = t + " " + JSON.stringify(obj);
  }

  try {
    const ws = WaveSurfer.create({
      container: "#wave-s3",
      url: "{{AUDIO_URL}}".replace("{{AUDIO_URL}}", ""), /* placeholder ignored by browser */
      height: 160,
      minPxPerSec: pxPerSec_s3,
      waveColor: "#9aa5b1",
      progressColor: "#4c78dd",
      backend: "MediaElement",
      plugins: [
        WaveSurfer.Timeline.create({ container: "#timeline-s3" })
      ]
    });

    // ✅ Register Regions AFTER create and keep a reference
    const regions = ws.registerPlugin(WaveSurfer.Regions.create());

    // demo regions (✅ use regions.addRegion, not ws.addRegion)
    regions.addRegion({ id: "r1", start: 1.0, end: 3.2, color: "rgba(255,0,0,0.20)", drag: true, resize: true });
    regions.addRegion({ id: "r2", start: 5.0, end: 7.0, color: "rgba(0,160,0,0.20)", drag: true, resize: true });

    // controls
    const zoomEl = document.getElementById("zoomval-s3");
    const setZoomVal = () => zoomEl.textContent = "pxPerSec=" + pxPerSec_s3.toFixed(1);
    setZoomVal();

    document.getElementById("play-s3").onclick = () => ws.playPause();
    document.getElementById("zin-s3").onclick = () => { pxPerSec_s3 = Math.min(pxPerSec_s3 * 1.25, 2000); ws.zoom(pxPerSec_s3); setZoomVal(); };
    document.getElementById("zout-s3").onclick = () => { pxPerSec_s3 = Math.max(pxPerSec_s3 / 1.25, 20);   ws.zoom(pxPerSec_s3); setZoomVal(); };

    // keyboard: focus + shortcuts
    const waveDiv = document.getElementById("wave-s3");
    waveDiv.addEventListener("keydown", (e) => {
      if (e.code === "Space") { e.preventDefault(); ws.playPause(); }
      if (e.key === "j") ws.setPlaybackRate(0.5);
      if (e.key === "k") ws.setPlaybackRate(1.0);
      if (e.key === "l") ws.setPlaybackRate(2.0);
    });
    waveDiv.focus();

    // ✅ Region events come from the plugin instance
    ws.on("ready", () => logDiag({ event: "ready" }));
    ws.on("play",  () => logDiag({ event: "play" }));
    ws.on("pause", () => logDiag({ event: "pause" }));
    ws.on("seek",  p  => logDiag({ event: "seek", p: Number(p.toFixed(3)) }));

    regions.on("region-updated", r => logDiag({
      event: "region-updated", id: r.id, start: Number(r.start.toFixed(3)), end: Number(r.end.toFixed(3))
    }));
    regions.on("region-in",  r => logDiag({ event: "region-in",  id: r.id }));
    regions.on("region-out", r => logDiag({ event: "region-out", id: r.id }));

  } catch (e) {
    console.error(e);
    logDiag({ event: "init-error", error: (e?.message || String(e)) });
  }
</script>
"""

render_stage(stage_id, body, height=340)

# ========== STAGE 4: + create/delete regions UI, snap toggle (UX probe) ==========
st.subheader("Stage 4 — + Create/Delete regions, Snap-to-grid toggle (client-side only)")
stage_id = "s4"
body = f"""
<div class="wrap-{stage_id}">
  <div id="timeline-{stage_id}" class="timeline"></div>
  <div id="wave-{stage_id}" class="wave" tabindex="0"></div>
  <div class="row">
    <button id="play-{stage_id}">Play/Pause</button>
    <button id="new-{stage_id}">New Region @ cursor</button>
    <button id="del-{stage_id}">Delete Selected</button>
    <label class="mono"><input type="checkbox" id="snap-{stage_id}" checked /> snap (50ms)</label>
    <button id="zin-{stage_id}">Zoom +</button>
    <button id="zout-{stage_id}">Zoom -</button>
    <span class="mono" id="zoomval-{stage_id}"></span>
  </div>
  <div class="mono" id="diag-{stage_id}" style="margin-top:6px; white-space: pre; background:#f7f7f9; padding:6px; border:1px solid #eee;"></div>
</div>
<script>
  let pxPerSec_{stage_id} = 140;
  let selectedRegion_{stage_id} = null;

  const diag = document.getElementById("diag-{stage_id}");
  function log(obj) {{ diag.textContent = (new Date()).toLocaleTimeString() + " " + JSON.stringify(obj); }}

  function snapTime(t) {{
    const snap = document.getElementById("snap-{stage_id}").checked;
    if (!snap) return t;
    const step = 0.050; // 50ms
    return Math.round(t / step) * step;
  }}

  try {{
    const ws = WaveSurfer.create({{
      container: "#wave-{stage_id}",
      url: "{audio_url}",
      height: 160,
      minPxPerSec: pxPerSec_{stage_id},
      waveColor: "#9aa5b1",
      progressColor: "#4c78dd",
      backend: "MediaElement",
      plugins: [
        WaveSurfer.Timeline.create({{ container: "#timeline-{stage_id}" }}),
        WaveSurfer.Regions.create()
      ]
    }});

    // initial region
    ws.addRegion({{ id: "r1", start: 1.0, end: 2.0, color: "rgba(255,165,0,0.25)" }});

    // selection helpers
    ws.on("region-clicked", (r, e) => {{ e.stopPropagation(); selectedRegion_{stage_id} = r; r.setOptions({{ color: "rgba(0,120,255,0.25)" }}); log({{ event: "region-clicked", id: r.id }}); }});
    ws.on("region-update-end", r => {{
      const s = snapTime(r.start), e = snapTime(r.end);
      if (s !== r.start || e !== r.end) r.setOptions({{ start: s, end: e }});
      log({{ event: "region-update-end", id: r.id, start: Number(r.start.toFixed(3)), end: Number(r.end.toFixed(3)) }});
    }});
    ws.on("interaction", () => {{ if (selectedRegion_{stage_id}) selectedRegion_{stage_id}.setOptions({{ color: "rgba(255,165,0,0.25)" }}); selectedRegion_{stage_id} = null; }});

    // controls
    document.getElementById("play-{stage_id}").onclick = () => ws.playPause();
    const zoomEl = document.getElementById("zoomval-{stage_id}");
    const setZoomVal = () => zoomEl.textContent = "pxPerSec=" + pxPerSec_{stage_id}.toFixed(1); setZoomVal();
    document.getElementById("zin-{stage_id}").onclick = () => {{ pxPerSec_{stage_id} = Math.min(pxPerSec_{stage_id} * 1.25, 2000); ws.zoom(pxPerSec_{stage_id}); setZoomVal(); }};
    document.getElementById("zout-{stage_id}").onclick = () => {{ pxPerSec_{stage_id} = Math.max(pxPerSec_{stage_id} / 1.25, 20);   ws.zoom(pxPerSec_{stage_id}); setZoomVal(); }};

    document.getElementById("new-{stage_id}").onclick = () => {{
      const t = ws.getCurrentTime();
      const s = snapTime(t), e = snapTime(t + 1.0);
      const id = "reg_" + Math.random().toString(36).slice(2,8);
      ws.addRegion({{ id, start: s, end: e, color: "rgba(255,165,0,0.25)" }});
      log({{ event: "region-created", id, start: s, end: e }});
    }};
    document.getElementById("del-{stage_id}").onclick = () => {{
      if (!selectedRegion_{stage_id}) {{ log({{ event: "delete", info: "no selection" }}); return; }}
      const id = selectedRegion_{stage_id}.id;
      selectedRegion_{stage_id}.remove();
      selectedRegion_{stage_id} = null;
      log({{ event: "region-deleted", id }});
    }};

    // keyboard
    const waveDiv = document.getElementById("wave-{stage_id}");
    waveDiv.addEventListener("keydown", (e) => {{
      if (e.code === "Space") {{ e.preventDefault(); ws.playPause(); }}
      if (e.key === "j") ws.setPlaybackRate(0.5);
      if (e.key === "k") ws.setPlaybackRate(1.0);
      if (e.key === "l") ws.setPlaybackRate(2.0);
      if (e.key === "i") ws.setTime(snapTime(ws.getCurrentTime())); // snap seek
    }});
    waveDiv.focus();

  }} catch (e) {{
    console.error(e);
    log({{ event: "init-error", error: (e?.message || String(e)) }});
  }}
</script>
"""
render_stage(stage_id, body, height=380)

# ========== NEXT STEPS (when you’re ready to return events to Python) ==========
st.markdown(
    """
**Next step:** switch one (or all) stages from `components.html(...)` to a real Streamlit
**Component** so JS can send structured events back to Python using `Streamlit.setComponentValue(...)`.
That’s a tiny folder with `index.html` and a `declare_component(...)` call in Python.

For now, each stage shows its own **diagnostics** (status/JSON logs) so we can pinpoint breakage.
If *any* stage hiccups, tell me which one and what the status line shows—we’ll fix at that layer, then move up.
"""
)