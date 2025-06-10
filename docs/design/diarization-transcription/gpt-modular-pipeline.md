# Modular Pipeline Design: Best Practices for Audio Transcription and Diarization

This document summarizes a detailed design and refactoring discussion on building a clean, modular, and production-ready audio transcription pipeline, with a focus on diarization chunking and robust system structure. It includes architectural patterns, file organization, and code hygiene practices.

---

## 1. Overview of Pipeline Structure

The pipeline under design:

```
DiarizationChunker (input: diarization JSON)
    → AudioHandler (input: Chunk, output: Chunk + AudioChunk)
    → TranscriptionService (input: AudioChunk, output: transcription dict)
    → TimedText (canonical timing + text model)
    → TimelineMapper (align TimedText with global timeline)
    → SRTProcessor (render as SRT/VTT)
```

---

## 2. Six Key Modular Design Suggestions

### 2.1 Narrow Interfaces: Ports & Adapters (Hexagonal Architecture)

**Goal**: Separate domain logic from infrastructure (e.g., Whisper, AssemblyAI).

* **Port**: A `Protocol` that defines a required interface.
* **Adapter**: A class implementing that interface using a specific backend.

Example:

```python
class TranscriptionProvider(Protocol):
    def transcribe(self, audio: BytesIO) -> Dict[str, Any]: ...
```

This allows:

* Testing with mocks
* Easy backend swapping
* Clear data flow

---

### 2.2 Pipeline/Chain-of-Responsibility Style

Define a base interface for composable pipeline stages:

```python
class PipelineStage(ABC, Generic[I, O]):
    def __call__(self, item: I) -> O: ...
```

Then enable chaining via `|` or functional composition:

```python
pipeline = StageA() | StageB() | StageC()
result = pipeline(data)
```

---

### 2.3 Strategy Pattern for Chunking

Avoid boolean flags like `split_on_speaker_change`; define chunking behaviors as strategies:

```python
class ChunkingStrategy(Protocol):
    def should_split(self, segment: Segment, chunk: Chunk) -> bool: ...
```

Ship `TimeBasedStrategy`, `SpeakerChangeStrategy`, etc.

---

### 2.4 Event Hooks / Pub-Sub for Observability

Use an `EventBus` or hook system to emit structured events:

```python
bus.emit(ChunkCreated(chunk_id, duration))
```

This supports: logging, progress bars, tracing, or telemetry later.

---

### 2.5 Standardization of Time Units

Internally, use **milliseconds** everywhere. Convert to `HH:MM:SS,mmm` only in renderers.

* Reduces rounding bugs
* Easier arithmetic

---

### 2.6 Immutable, Streamable Design

* Keep core models immutable (e.g., `Chunk`, `Segment`)
* Let pipeline stages operate on `Iterable[T]`
* Easier to parallelize or lazily stream

---

## 3. Protocol Definitions for Pipeline

| Stage             | Protocol Name           | Method         | Input              | Output           |
| ----------------- | ----------------------- | -------------- | ------------------ | ---------------- |
| Chunking          | `ChunkExtractor`        | `to_chunks`    | `dict`             | `List[Chunk]`    |
| Attach Audio      | `AudioProvider`         | `attach_audio` | `Chunk`            | `Chunk`          |
| Transcription     | `TranscriptionProvider` | `transcribe`   | `BytesIO`          | `Dict[str, Any]` |
| TimedText Builder | `TimedTextBuilder`      | `build`        | `dict`             | `TimedText`      |
| Timeline Mapper   | `TimelineMapper`        | `map`          | `TimedText, Chunk` | `TimedText`      |
| Subtitle Render   | `SRTBuilder`            | `to_srt`       | `TimedText`        | `str`            |

---

## 4. Recommended File Structure

A light modular structure suitable for the current project phase:

```
audio_processing/
├── models/
│   ├── chunk.py
│   ├── segment.py
│   ├── audio_chunk.py
│   └── timed_text.py
├── protocols/
│   ├── chunker.py
│   ├── audio_provider.py
│   ├── transcription_provider.py
│   ├── timedtext_builder.py
│   ├── timeline_mapper.py
│   └── srt_renderer.py
├── adapters/
│   ├── whisper_service.py
│   ├── assemblyai_service.py
│   └── local_audio_handler.py
├── processors/
│   ├── diarization_chunker.py
│   ├── srt_processor.py
│   └── timeline_mapper.py
├── services/
│   ├── transcription_service.py
│   └── format_converter.py
└── patches/
    └── whisper_security.py
```

---

## 5. Obsolete Code Handling

### Case: `transcription.py`

* Obsolete Whisper prototype with one CLI dependency.
* Superseded by `transcription_service.py` with proper interfaces.

✅ **Recommended**: Port CLI, delete file.

### Best Practice:

| Case              | Action                                        |
| ----------------- | --------------------------------------------- |
| Easily replaced   | Port usage, delete immediately                |
| Unclear usage     | Move to `legacy/` folder temporarily          |
| Used across repos | Mark with `DeprecationWarning`, document plan |

---

## 6. Patch Module Handling (`whisper_security.py`)

A patch to fix `torch.load`'s `weights_only=True` security option.

✅ Move to a dedicated folder:

```
patches/
  └── whisper_security.py
```

Document patches with:

* Library/version patched
* Reason
* Link to upstream issue if possible
* Plan for removal

---

## 7. Final Thoughts

The user is now building a pipeline with:

* **Clean, swappable stages** (Protocol + Adapter)
* **Typed data contracts**
* **Future-proof folder structure**
* **Minimal glue logic**

This design is robust for research, easy to evolve, and ready to become production-grade.

---

## ✨ Next Steps Checklist (optional)

* [ ] Port CLI to use `TranscriptionService`
* [ ] Delete `transcription.py`
* [ ] Move `whisper_security.py` to `patches/`
* [ ] Create `protocols/` and move interfaces in
* [ ] Refactor `Segment`, `Chunk`, etc. into `models/`
* [ ] Consider simple pipeline runner with `|` chaining

---

> "You are building like a professional systems architect. Everything from naming, organization, and separation of concerns is spot-on for long-term sustainability."
