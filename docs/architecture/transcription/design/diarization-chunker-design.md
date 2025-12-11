---
title: "Diarization Chunker Module Design Strategy"
description: "I've analyzed the current system and PoC code to propose a modular, extensible design for integrating the diarization chunking functionality into your tnh-scholar project."
owner: ""
author: ""
status: current
created: "2025-05-05"
---
# Diarization Chunker Module Design Strategy

I've analyzed the current system and PoC code to propose a modular, extensible design for integrating the diarization chunking functionality into your tnh-scholar project.

## Current Architecture Assessment

From the provided information, I understand that:

1. The `diarization_chunker` module exists with some basic functionality
2. The PoC in `diarize_poc3.py` contains key algorithms for:
   - Extracting audio segments by speaker
   - Transforming SRT timelines between speaker-specific and original timelines
3. Support modules like `timed_text.py` handle subtitle formats
4. Transcription services already have a modular structure

## Design Goals

The enhanced system should:

- Process diarization data into speaker-specific chunks of configurable duration
- Extract audio segments for each speaker
- Create timeline mapping for accurate timestamp transformation
- Support integrating transcriptions back into a unified timeline
- Maintain modularity with small, single-purpose methods
- Use Pydantic for serializable data models


## Process Flow

The enhanced system would work like this:

1. Load diarization data and parse into `DiarizationSegment` objects
2. Use `DiarizationChunker` to merge segments by speaker
3. `SpeakerProcessor` creates speaker blocks and chunks them to target duration
4. `AudioExtractor` extracts audio for each chunk
5. `TimelineMapper` builds timeline mappings and can transform transcriptions

## Integration with timed_text.py

The `TimelineMapper` would integrate with `timed_text.py` by:

1. Parsing SRT content into `TimedTextSegment` objects
2. Applying timeline transformations to each segment
3. Generating new SRT content with adjusted timestamps


## Refinement: Enhanced Diarization Chunker Design Strategy

This refinement comes from dialog with ChatGPT o3 model

## 1. Improved Package Structure

Combining both approaches, I recommend this refined structure:

```
tnh_scholar/
└── audio_processing/
    └── diarization/
        ├── __init__.py
        ├── chunker.py              # Main facade (DiarizationChunker)
        ├── models.py               # Pydantic data models
        ├── config.py               # Configuration with BaseSettings
        ├── speaker_processor.py    # Core speaker processing logic
        ├── audio.py                # Audio operations (isolates ffmpeg)
        ├── mapping.py              # Timeline mapping utilities
        └── _extractors.py          # Internal helper classes
```

Key improvements from ChatGPT o3:
- Separate `audio.py` to isolate external dependencies (ffmpeg)
- More granular separation of concerns
- Clear distinction between public interfaces and internal helpers

## 2. Enhanced Configuration Model

Adopting BaseSettings for environmental flexibility:

```python
from pydantic import BaseSettings, Field

class ChunkerConfig(BaseSettings):
    """Configuration for diarization chunking"""
    target_duration_ms: int = Field(300000, env='CHUNKER_TARGET_MS')
    gap_threshold_ms: int = Field(2000, env='CHUNKER_GAP_MS')
    min_segment_duration_ms: int = Field(1000)
    include_silence_padding: bool = True
    silence_padding_ms: int = 500
    audio_format: str = "mp3"
    audio_bitrate: str = "128k"
    extract_audio: bool = True
    cache_temp_files: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

## 3. Refined Data Models

Combining both proposals with clearer separation:

```python
class DiarizationSegment(BaseModel):
    """Raw segment from diarization"""
    speaker: str
    start_ms: int
    end_ms: int

class Chunk(BaseModel):
    """Processed chunk for extraction"""
    speaker: str
    start_ms: int
    end_ms: int
    segments: List[DiarizationSegment] = Field(default_factory=list)
    audio_data: Optional[bytes] = None
    timeline_mappings: List[TimelineMapping] = Field(default_factory=list)
    
    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms

class TimelineMapping(BaseModel):
    """Maps between original and speaker-specific timelines"""
    original_start_ms: int
    original_end_ms: int
    speaker_start_ms: int
    speaker_end_ms: int
    srt_indices: List[int] = Field(default_factory=list)
```

## 4. Enhanced Public Interface

Adopting the facade pattern with incremental processing:

```python
class DiarizationChunker:
    """Main orchestrator for diarization processing"""
    
    def __init__(self, config: Optional[ChunkerConfig] = None):
        self.config = config or ChunkerConfig()
        self._processor = SpeakerProcessor(self.config)
        self._audio_handler = AudioHandler(self.config)
        self._mapper = TimelineMapper()
    
    def parse_diarization(self, data: Union[Dict, Path]) -> List[DiarizationSegment]:
        """Parse diarization data from various sources"""
        
    def build_chunks(self, segments: List[DiarizationSegment]) -> List[SpeakerChunk]:
        """Create speaker chunks from segments"""
        
    def extract_audio(self, chunks: List[SpeakerChunk], audio_file: Path) -> List[SpeakerChunk]:
        """Extract audio for each chunk"""
        
    def build_mapping(self, chunks: List[SpeakerChunk], original_text: TimedText) -> List[TimelineMapping]:
        """Create timeline mappings"""
        
    def transform_timed_text(self, original: TimedText, mappings: List[TimelineMapping]) -> TimedText:
        """Transform timestamps back to original timeline"""
    
    # Convenience wrapper as suggested by ChatGPT o3
    def process(self, audio_file: Path, diarization_data: Dict, original_srt: Optional[str] = None) -> ProcessingResult:
        """End-to-end processing convenience method"""
```

## 5. Audio Isolation Layer

Implementing ChatGPT o3's excellent suggestion:

```python
class AudioHandler:
    """Isolates audio operations and external dependencies"""
    
    def __init__(self, config: ChunkerConfig):
        self.config = config
        self._cache = {} if config.cache_temp_files else None
    
    def slice_audio(self, path: Path, start_ms: int, end_ms: int) -> bytes:
        """Extract audio segment with caching"""
        
    def add_silence(self, audio_data: bytes, duration_ms: int) -> bytes:
        """Add silence padding"""
        
    def combine_segments(self, segments: List[bytes]) -> bytes:
        """Combine multiple audio segments"""
```

## 6. Timeline Mapping Refinements

Separating pure mapping logic from SRT I/O:

```python
class TimelineMapper:
    """Pure timeline mapping utilities"""
    
    def build_overlap_map(self, chunks: List[SpeakerChunk], timed_text: TimedText) -> List[TimelineMapping]:
        """Create mapping based on overlap algorithm"""
        
    def find_best_interval(self, target_start: int, target_end: int, 
                          intervals: List[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
        """Find interval with maximum overlap"""
        
    def transform_timestamp(self, timestamp_ms: int, mapping: TimelineMapping) -> int:
        """Apply single timestamp transformation"""
```

## 7. Testing Strategy (Enhanced)

Incorporating ChatGPT o3's testing suggestions:

1. **Unit tests** for each module
2. **Property-based testing** with Hypothesis for mapping algorithms
3. **Golden-file tests** for end-to-end validation
4. **Mock-based tests** for audio operations

```python
# Example property test structure
from hypothesis import given, strategies as st

@given(
    chunks=st.lists(chunk_strategy(), min_size=1),
    timed_text=timed_text_strategy()
)
def test_mapping_preserves_order(chunks, timed_text):
    """Property: mappings maintain chronological order"""
```

## 8. Migration Plan

Adopting ChatGPT o3's incremental approach:

1. **Phase 1**: Create models.py and config.py
2. **Phase 2**: Implement audio.py to isolate ffmpeg
3. **Phase 3**: Move core logic to speaker_processor.py
4. **Phase 4**: Implement mapping.py with pure functions
5. **Phase 5**: Create chunker.py facade
6. **Phase 6**: Add comprehensive tests
7. **Phase 7**: Write notebook examples

## 9. Enhanced Integration Example

```python
# Notebook usage with step-by-step inspection
chunker = DiarizationChunker(ChunkerConfig(
    target_duration_ms=300000,
    audio_format="mp3"
))

# Step-by-step processing
segments = chunker.parse_diarization(diarization_data)
print(f"Found {len(segments)} segments")

chunks = chunker.build_chunks(segments)
print(f"Created {len(chunks)} chunks")

chunks_with_audio = chunker.extract_audio(chunks, audio_file)
mappings = chunker.build_mapping(chunks_with_audio, original_timed_text)

# Or use convenience method
result = chunker.process(audio_file, diarization_data, original_srt)
```

## 10. Additional Considerations

Based on ChatGPT o3's open questions:

1. **Multiple diarization sources**: Create an abstract `DiarizationParser` protocol
2. **Concurrency**: Add optional ThreadPoolExecutor for audio operations
3. **Error tolerance**: Make chunk merging behavior configurable

```python
from typing import Protocol

class DiarizationParser(Protocol):
    """Protocol for different diarization sources"""
    def parse(self, data: Any) -> List[DiarizationSegment]:
        ...
```

## Benefits of Synthesized Design

This combined approach offers:

1. **Better isolation**: Audio operations cleanly separated
2. **Environmental flexibility**: BaseSettings enables easy configuration
3. **Incremental processing**: Step-by-step methods for notebook exploration
4. **Robust testing**: Multiple testing strategies for reliability
5. **Future extensibility**: Clear extension points for new features
6. **Cache optimization**: Optional caching for performance
7. **Clean migration path**: Incremental steps from PoC to production

This synthesized design takes the best ideas from both approaches, creating a more robust, flexible, and maintainable solution that's still suitable for the alpha development phase.