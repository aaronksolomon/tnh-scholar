# Speaker Diarization and Time-Mapped Transcription System Design

## 1. Overview

This document outlines a design for enhancing the existing diarization system to support speaker-specific transcription with accurate time mapping. The system will consolidate audio segments by speaker while preserving timing information, generate transcriptions for each speaker's track, and remap the transcription timings back to the original audio timeline.

## 2. Design Goals

- **Minimal Changes**: Extend existing functionality with minimal modifications to current code
- **Accurate Timing**: Maintain precise timing relationships throughout the pipeline
- **Conceptual Simplicity**: Use clear, minimalist data structures that map directly to the problem domain
- **Single-Action Functions**: Each function or method should perform a single, well-defined action; for sequences, each element should be implemented as a single-action function
- **Modularity**: Create well-defined components with clear responsibilities
- **Code Reuse**: Maximize reuse of data structures and helper functions across components
- **Extensibility**: Support future enhancements like language detection
- **Usability**: Integrate with existing CLI interfaces

## 3. System Architecture

### 3.1 Core Components

```mermaid
graph TD
    A[Audio File] --> B[Diarization Processor]
    B --> |DiarizationSegments| C[Speaker Track Generator]
    C --> D1[Speaker Track 1]
    C --> D2[Speaker Track 2]
    C --> D3[Speaker Track n]
    D1 --> E1[Transcription Engine]
    D2 --> E2[Transcription Engine]
    D3 --> E3[Transcription Engine]
    E1 --> F1[Speaker SRT 1]
    E2 --> F2[Speaker SRT 2]
    E3 --> F3[Speaker SRT n]
    F1 --> G[Timing Remapper]
    F2 --> G
    F3 --> G
    G --> H[Final SRT Files]
    
    subgraph "Existing Components"
        A
        B
    end
    
    subgraph "New Components"
        C
        G
    end
    
    subgraph "Per-Speaker Processing"
        D1
        D2
        D3
        E1
        E2
        E3
        F1
        F2
        F3
    end
```

### 3.2 Data Flow Architecture

```mermaid
flowchart TB
    subgraph InputProcess["Input Processing"]
        direction TB
        RawAudio["Raw Audio File"]
        DiarizeJob["Pyannote Diarization"]
        SpeakerSegments["Speaker Segments"]
        
        RawAudio --> DiarizeJob
        DiarizeJob --> SpeakerSegments
    end
    
    subgraph ConsolidationProcess["Track Consolidation"]
        direction TB
        SpeakerChunks["Speaker Chunks<br>(From Diarization)"]
        GroupSegments["Group Segments<br>By Speaker"]
        SpeakerTracks["Speaker Tracks"]
        ConsolidatedTracks["Consolidated Audio Tracks<br>(Per Speaker)"]
        TimeMaps["Time Mapping Tables"]
        
        SpeakerChunks --> GroupSegments
        GroupSegments --> SpeakerTracks
        SpeakerTracks --> ConsolidatedTracks
        SpeakerTracks --> TimeMaps
    end
    
    subgraph TranscriptionProcess["Transcription"]
        direction TB
        Speaker1Track["Speaker 1 Track"]
        Speaker2Track["Speaker 2 Track"]
        SpeakerNTrack["Speaker N Track"]
        Speaker1SRT["Speaker 1 SRT"]
        Speaker2SRT["Speaker 2 SRT"]
        SpeakerNSRT["Speaker N SRT"]
        
        Speaker1Track --> Speaker1SRT
        Speaker2Track --> Speaker2SRT
        SpeakerNTrack --> SpeakerNSRT
    end
    
    subgraph RemappingProcess["Time Remapping"]
        direction TB
        RawSRTs["Speaker SRTs<br>(Transformed Timeline)"]
        ParseSRT["Parse SRT Files"]
        RemapOperation["Remap Timestamps"]
        WriteSRT["Write Remapped SRTs"]
        MappedSRTs["Remapped SRTs<br>(Original Timeline)"]
        FinalOutput["Final SRT Files"]
        
        RawSRTs --> ParseSRT
        ParseSRT --> RemapOperation
        TimeMaps --> RemapOperation
        RemapOperation --> WriteSRT
        WriteSRT --> MappedSRTs
        MappedSRTs --> FinalOutput
    end
    
    InputProcess --> ConsolidationProcess
    ConsolidationProcess --> TranscriptionProcess
    TranscriptionProcess --> RemappingProcess
```

## 3.3 Error Handling Strategy

For the prototype phase, error handling will be minimal, allowing failures to surface immediately for debugging.

### 3.3.1 Core Approach

- Focus on logging rather than error handling for most operations
- Handle only critical expected errors (file access, format errors)
- Allow other exceptions to propagate and terminate execution for easier debugging
- Use descriptive log messages for error contexts

### 3.3.2 Implementation Examples

Only handle errors where they commonly occur and are expected:

```python
def load_audio_file(file_path):
    """Load audio file or raise appropriate error."""
    if not file_path.exists():
        logger.error(f"Audio file not found: {file_path}")
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    
    # Let any other exceptions propagate up
    return AudioSegment.from_file(file_path)
```

In all other cases, log the operation and let exceptions propagate:

```python
def process_speaker_track(track, audio_file):
    """Process a speaker track."""
    logger.info(f"Processing track for speaker {track.speaker_id}")
    return track.consolidate_audio(audio_file)
```

This minimal approach is appropriate for the prototype phase, with comprehensive error handling to be implemented later.

## 4. Component Specifications

### 4.1 Speaker Track Generator

**Purpose**: Consolidate speaker segments into continuous audio tracks while maintaining timing relationships

```mermaid
classDiagram
    class SpeakerTrackGenerator {
        +generate_speaker_tracks(diarization_segments: List[DiarizationSegment], gap_duration: float) List[SpeakerTrack]
        +group_by_speaker(diarization_segments: List[DiarizationSegment]) Dict[str, List[DiarizationSegment]]
        +create_track(speaker_id: str, segments: List[DiarizationSegment], gap_duration: float) SpeakerTrack
        +export_time_maps(tracks: List[SpeakerTrack], output_dir: Path)
    }
    
    class SpeakerTrack {
        +speaker_id: str
        +segments: List[DiarizationSegment]
        +time_map: TimeMap
        +consolidated_path: Path
        +add_segment(segment: DiarizationSegment, transformed_start: float)
        +consolidate_audio(original_audio: AudioSegment)
        +save_audio(output_dir: Path) Path
    }
    
    class TimeMap {
        +speaker_id: str
        +intervals: List[TimeMapInterval]
        +add_interval(original_start: float, original_end: float, transformed_start: float)
        +map_time(original_time: float) float
        +reverse_map_time(transformed_time: float) float
        +export_to_json(file_path: Path)
        +import_from_json(file_path: Path) TimeMap
    }
    
    class TimeMapInterval {
        +original_start: float
        +original_end: float
        +transformed_start: float
        +duration() float
        +transformed_end() float
    }
    
    class DiarizationSegment {
        +speaker: str
        +start: float
        +end: float
        +duration() float
    }
    
    SpeakerTrackGenerator --> SpeakerTrack
    SpeakerTrack --> TimeMap
    TimeMap --> TimeMapInterval
    SpeakerTrackGenerator --> DiarizationSegment
    SpeakerTrack --> DiarizationSegment
```

### 4.2 Time Mapping System

**Purpose**: Track time relationships between original and consolidated audio

```mermaid
graph TB
    subgraph "Original Timeline (Mixed Speakers)"
        OT1[Speaker 1 <br> 0:00-0:30]
        OT2[Speaker 2 <br> 0:30-1:15]
        OT3[Speaker 3 <br> 1:15-2:00]
        OT4[Speaker 1 <br> 2:00-2:45]
        OT5[Speaker 2 <br> 2:45-3:10]
        OT6[Speaker 3 <br> 3:10-3:45]
        OT7[Speaker 1 <br> 3:45-4:20]
        OT8[Speaker 3 <br> 4:20-5:00]
        OT9[Speaker 2 <br> 5:00-5:30]
    end
    
    subgraph "Consolidated Timeline (Speaker 1)"
        CT1_1[0:00-0:30]
        CT1_2[0:31-1:16]
        CT1_3[1:17-1:52]
    end
    
    subgraph "Consolidated Timeline (Speaker 2)"
        CT2_1[0:00-0:45]
        CT2_2[0:46-1:11]
        CT2_3[1:12-1:42]
    end
    
    subgraph "Consolidated Timeline (Speaker 3)"
        CT3_1[0:00-0:45]
        CT3_2[0:46-1:21]
        CT3_3[1:22-2:02]
    end
    
    OT1 -- map --> CT1_1
    OT4 -- map --> CT1_2
    OT7 -- map --> CT1_3
    
    OT2 -- map --> CT2_1
    OT5 -- map --> CT2_2
    OT9 -- map --> CT2_3
    
    OT3 -- map --> CT3_1
    OT6 -- map --> CT3_2
    OT8 -- map --> CT3_3
    
    style OT1 fill:#f9f,stroke:#333,stroke-width:2px
    style OT4 fill:#f9f,stroke:#333,stroke-width:2px
    style OT7 fill:#f9f,stroke:#333,stroke-width:2px
    
    style OT2 fill:#bbf,stroke:#333,stroke-width:2px
    style OT5 fill:#bbf,stroke:#333,stroke-width:2px
    style OT9 fill:#bbf,stroke:#333,stroke-width:2px
    
    style OT3 fill:#bfb,stroke:#333,stroke-width:2px
    style OT6 fill:#bfb,stroke:#333,stroke-width:2px
    style OT8 fill:#bfb,stroke:#333,stroke-width:2px
    
    style CT1_1 fill:#f9f,stroke:#333,stroke-width:2px
    style CT1_2 fill:#f9f,stroke:#333,stroke-width:2px
    style CT1_3 fill:#f9f,stroke:#333,stroke-width:2px
    
    style CT2_1 fill:#bbf,stroke:#333,stroke-width:2px
    style CT2_2 fill:#bbf,stroke:#333,stroke-width:2px
    style CT2_3 fill:#bbf,stroke:#333,stroke-width:2px
    
    style CT3_1 fill:#bfb,stroke:#333,stroke-width:2px
    style CT3_2 fill:#bfb,stroke:#333,stroke-width:2px
    style CT3_3 fill:#bfb,stroke:#333,stroke-width:2px
```

### 4.3 Timing Remapper

**Purpose**: Convert SRT timings from consolidated tracks to original timeline

```mermaid
classDiagram
    class TimingRemapper {
        +remap_srt(srt_path: Path, time_map: TimeMap, output_path: Path) Path
        +parse_srt_file(srt_path: Path) List[SubtitleEntry]
        +remap_timestamp(timestamp: float, time_map: TimeMap) float
        +remap_entries(entries: List[SubtitleEntry], time_map: TimeMap) List[SubtitleEntry]
        +write_srt_file(entries: List[SubtitleEntry], output_path: Path)
    }
    
    class SubtitleEntry {
        +index: int
        +start_time: str
        +end_time: str
        +text: str
        +start_seconds: float
        +end_seconds: float
        +parse_timestamp(timestamp: str) float
        +format_timestamp(seconds: float) str
        +set_times(start_seconds: float, end_seconds: float)
        +format_srt() str
        +clone() SubtitleEntry
    }
    
    class SRTUtils {
        +<<static>> parse_timestamp(timestamp: str) float
        +<<static>> format_timestamp(seconds: float) str
        +<<static>> read_srt_file(srt_path: Path) List[SubtitleEntry]
        +<<static>> write_srt_file(entries: List[SubtitleEntry], output_path: Path)
    }
    
    TimingRemapper --> SubtitleEntry
    TimingRemapper --> SRTUtils
    SubtitleEntry --> SRTUtils: uses
```

### 4.4 CLI Integration

**Purpose**: Extend existing CLI interface to support the new functionality

```mermaid
classDiagram
    class AudioTranscribeCLI {
        +diarize_option: bool
        +speaker_gap: float
        +srt_output: bool
        +handle_diarize()
        +handle_speaker_tracks()
        +handle_transcribe_tracks()
        +handle_remap_timings()
    }
    
    class AudioPipeline {
        +run()
        +execute_stage(stage_name: str)
        +get_stage_result(stage_name: str) Any
    }
    
    class PipelineStage {
        <<interface>>
        +execute(context: Dict[str, Any]) Dict[str, Any]
        +validate(context: Dict[str, Any]) bool
    }
    
    class DiarizationStage {
        +execute(context: Dict[str, Any]) Dict[str, Any]
        +validate(context: Dict[str, Any]) bool
    }
    
    class SpeakerTrackStage {
        +execute(context: Dict[str, Any]) Dict[str, Any]
        +validate(context: Dict[str, Any]) bool
    }
    
    class TranscriptionStage {
        +execute(context: Dict[str, Any]) Dict[str, Any]
        +validate(context: Dict[str, Any]) bool
    }
    
    class RemappingStage {
        +execute(context: Dict[str, Any]) Dict[str, Any]
        +validate(context: Dict[str, Any]) bool
    }
    
    AudioTranscribeCLI --> AudioPipeline
    AudioPipeline --> PipelineStage
    PipelineStage <|-- DiarizationStage
    PipelineStage <|-- SpeakerTrackStage
    PipelineStage <|-- TranscriptionStage
    PipelineStage <|-- RemappingStage
```

## 5. Algorithm Approaches

### 5.1 Time Mapping Approach

The core time mapping functionality can be broken down into simple steps:

```mermaid
flowchart TD
    A[Original Timestamp] --> B{In a segment?}
    B -->|Yes| C[Calculate relative position in segment]
    B -->|No| D[Find surrounding segments]
    C --> E[Map to position in transformed segment]
    D --> F[Determine if in a gap]
    F -->|Yes| G[Proportional mapping across gap]
    F -->|No| H[Handle edge case]
    G --> I[Return mapped timestamp]
    E --> I
    H --> I
```

For implementation, each step should be a simple function:

1. Find containing segment for a timestamp
2. Calculate relative position within segment
3. Map timestamp from segment to transformed timeline
4. Handle gap mapping with simple proportional scaling

### 5.2 Audio Consolidation Approach

Audio consolidation can be simplified into these discrete steps:

```mermaid
flowchart TD
    A[Speaker Segments] --> B[Sort by original time]
    B --> C[Create empty output]
    C --> D[For each segment]
    D --> E[Extract segment audio]
    E --> F[Record time mapping]
    F --> G[Add to output]
    G --> H[Add silence gap if needed]
    H --> D
    D -->|Done| I[Return consolidated audio]
```

Implementation approach:
1. Extract each segment as a separate function
2. Add segments to output sequentially
3. Track current position for time mapping
4. Insert silence between non-contiguous segments

### 5.3 SRT Remapping Approach

The SRT remapping process follows these simple steps:

```mermaid
flowchart TD
    A[Input SRT File] --> B[Parse SRT]
    B --> C[For each subtitle]
    C --> D[Remap start time]
    D --> E[Remap end time]
    E --> F[Create new subtitle entry]
    F --> C
    C -->|Done| G[Sort by start time]
    G --> H[Renumber entries]
    H --> I[Write output SRT]
```

Each step should be implemented as a separate single-purpose function:
1. Parse SRT entries
2. Remap individual timestamps
3. Create new entries with remapped times
4. Sort and renumber entries
5. Write formatted SRT output

## 6. Resource Management

### 6.1 Temporary File Handling

For the prototype phase, a minimalist approach to file management:

1. **Simple Directory Structure**
   - Create timestamped parent directory for each processing run
   - Create subdirectory for each speaker
   - Log all created paths for potential manual cleanup

2. **File Naming Convention**
   - Use consistent prefixes for file types: `speaker_<id>_track.mp3`
   - Include start/end timestamps in filenames
   - Keep critical metadata in filenames for manual inspection

3. **Minimal Cleanup Logic**
   ```python
   # Simple list of temporary files
   temp_files = []
   
   # Register temporary file
   def register_temp_file(file_path):
       temp_files.append(file_path)
       logger.debug(f"Registered temporary file: {file_path}")
   
   # Basic cleanup function - call manually when needed
   def cleanup_temp_files():
       for file_path in temp_files:
           if file_path.exists():
               file_path.unlink()
               logger.debug(f"Removed: {file_path}")
   ```

4. **Development Strategy**
   - In prototype phase, prefer leaving files for inspection
   - Add command-line flag for cleanup (`--clean-temp`) 
   - Document created files for manual cleanup when needed

## 7. Data Structures

### 7.1 TimeMap

The TimeMap structure is crucial for maintaining timing relationships:

```python
class TimeMapInterval:
    """Maps a segment of the original timeline to the transformed timeline."""
    original_start: float  # Start time in original audio (seconds)
    original_end: float    # End time in original audio (seconds)
    transformed_start: float  # Start time in transformed audio (seconds)
    
    @property
    def duration(self) -> float:
        """Duration of the interval (same in both timelines)."""
        return self.original_end - self.original_start
    
    @property
    def transformed_end(self) -> float:
        """End time in the transformed timeline."""
        return self.transformed_start + self.duration
```

```python
class TimeMap:
    """Maps time points between original and transformed timelines."""
    speaker_id: str
    intervals: List[TimeMapInterval]  # Ordered list of intervals
    
    def add_interval(self, original_start: float, original_end: float, 
                    transformed_start: float) -> None:
        """Add a new mapping interval."""
    
    def map_time(self, original_time: float) -> float:
        """Map a time from original timeline to transformed timeline."""
        
    def reverse_map_time(self, transformed_time: float) -> float:
        """Map a time from transformed timeline back to original timeline."""
        
    def export_to_json(self, file_path: Path) -> None:
        """Export the time map to a JSON file."""
        
    @classmethod
    def import_from_json(cls, file_path: Path) -> 'TimeMap':
        """Import a time map from a JSON file."""
```

### 7.2 SpeakerTrack

```python
class SpeakerTrack:
    """Represents a consolidated audio track for a single speaker."""
    speaker_id: str
    segments: List[DiarizationSegment]  # Original segments from diarization
    consolidated_path: Optional[Path]  # Path to consolidated audio file
    time_map: TimeMap  # Mapping between original and transformed timelines
    
    def add_segment(self, segment: DiarizationSegment, transformed_start: float) -> None:
        """Add a segment to the track with its position in the transformed timeline."""
    
    def consolidate_audio(self, original_audio: AudioSegment) -> AudioSegment:
        """Extract and concatenate all segments to create a continuous audio track."""
    
    def save_audio(self, output_dir: Path) -> Path:
        """Save the consolidated audio to a file."""
```

### 7.3 SubtitleEntry

```python
class SubtitleEntry:
    """Represents a single subtitle entry in an SRT file."""
    index: int
    start_time: str  # SRT format time (HH:MM:SS,mmm)
    end_time: str    # SRT format time (HH:MM:SS,mmm)
    text: str
    start_seconds: float  # Time in seconds for calculations
    end_seconds: float    # Time in seconds for calculations
    
    @staticmethod
    def parse_timestamp(timestamp: str) -> float:
        """Convert SRT timestamp to seconds."""
    
    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """Convert seconds to SRT timestamp."""
    
    def set_times(self, start_seconds: float, end_seconds: float) -> None:
        """Set both timestamps from seconds values."""
    
    def format_srt(self) -> str:
        """Format entry as SRT text."""
    
    def clone(self) -> 'SubtitleEntry':
        """Create a copy of this entry."""
```

## 8. Process Flow

### 8.1 Speaker Track Generation

```mermaid
sequenceDiagram
    participant AP as AudioPipeline
    participant DP as DiarizationProcessor
    participant SG as SpeakerTrackGenerator
    participant ST as SpeakerTrack
    participant TM as TimeMap
    
    AP->>DP: process_audio()
    DP->>AP: diarization_segments
    AP->>SG: generate_speaker_tracks(diarization_segments, gap_duration)
    
    SG->>SG: group_by_speaker(diarization_segments)
    Note over SG: Organize segments by speaker ID
    
    loop For each speaker
        SG->>ST: create_track(speaker_id)
        ST->>TM: create_time_map()
        
        loop For each segment
            ST->>ST: add_segment(segment, gap_duration)
            Note over ST: Calculate transformed time position
            ST->>TM: add_interval(original_start, original_end, transformed_start)
            Note over TM: Map original segment to transformed timeline
        end
    end
    
    SG->>AP: speaker_tracks
```

### 8.2 Audio Consolidation and Transcription

```mermaid
sequenceDiagram
    participant AP as AudioPipeline
    participant ST as SpeakerTrack
    participant AS as AudioSegment
    participant TR as TranscriptionEngine
    participant TM as TimeMap
    
    AP->>AP: load_original_audio()
    
    loop For each speaker_track
        AP->>ST: consolidate_audio(original_audio)
        
        ST->>AS: create_empty()
        
        loop For each segment
            ST->>AS: extract_segment(original_audio, segment)
            AS->>AS: append(segment_audio)
        end
        
        ST->>ST: save_audio(output_dir)
        ST->>TM: export_to_json(output_dir)
        
        AP->>TR: transcribe_audio(track.consolidated_path)
        TR->>AP: srt_path
    end
```

### 8.3 Timing Remapping

```mermaid
sequenceDiagram
    participant AP as AudioPipeline
    participant TR as TimingRemapper
    participant SE as SubtitleEntry
    participant TM as TimeMap
    
    loop For each speaker_srt
        AP->>TR: remap_srt(srt_path, time_map)
        
        TR->>TR: parse_srt_file(srt_path)
        
        loop For each subtitle_entry
            TR->>SE: clone()
            TR->>TM: reverse_map_time(entry.start_seconds)
            TR->>TM: reverse_map_time(entry.end_seconds)
            TR->>SE: set_times(original_start, original_end)
        end
        
        TR->>TR: write_srt_file(remapped_entries, output_path)
        TR->>AP: remapped_srt_path
    end
```

### 8.4 Complete Pipeline Flow

```mermaid
stateDiagram-v2
    [*] --> InitializeContext
    InitializeContext --> LoadAudio
    LoadAudio --> Diarization
    Diarization --> SpeakerSegmentation
    
    SpeakerSegmentation --> TrackGeneration
    TrackGeneration --> AudioConsolidation
    AudioConsolidation --> Transcription
    Transcription --> TimingRemapping
    
    TimingRemapping --> GenerateMasterSRT
    GenerateMasterSRT --> [*]
    
    state TrackGeneration {
        [*] --> GroupBySpeaker
        GroupBySpeaker --> SortSegments
        SortSegments --> BuildTracks
        BuildTracks --> BuildTimeMaps
        BuildTimeMaps --> [*]
    }
    
    state AudioConsolidation {
        [*] --> ProcessSegments
        ProcessSegments --> SaveTracks
        SaveTracks --> [*]
    }
    
    state TimingRemapping {
        [*] --> LoadSRTs
        LoadSRTs --> ParseSRTFiles
        ParseSRTFiles --> RemapTimestamps
        RemapTimestamps --> WriteRemappedSRTs
        WriteRemappedSRTs --> [*]
    }
    
    state GenerateMasterSRT {
        [*] --> MergeSpeakerSRTs
        MergeSpeakerSRTs --> SortByTimestamp
        SortByTimestamp --> FormatOutput
        FormatOutput --> [*]
    }
```

## 9. Integration Strategy

### 9.1 Modular Single-Action Functions

To adhere to the single-action principle, functions in the implementation are designed with the following characteristics:

1. **Focused Responsibility**: Each function has one clear purpose
2. **Limited Side Effects**: Functions minimize state changes
3. **Clear Input/Output Boundaries**: Well-defined parameters and return values
4. **Single Level of Abstraction**: Operations within a function are at the same conceptual level

Examples of single-action functions:

```python
# Time mapping
def map_timestamp(timestamp: float, time_map: TimeMap) -> float:
    """Map a single timestamp from one timeline to another."""
    
# SRT processing
def parse_srt_timestamp(timestamp: str) -> float:
    """Parse SRT timestamp format to seconds."""
    
# Audio processing
def extract_audio_segment(audio: AudioSegment, start: float, end: float) -> AudioSegment:
    """Extract a segment of audio between specified times."""
```

### 9.2 Simplified Core Concepts

The design centers around three key concepts:

1. **SpeakerTrack**: Contains segments for a single speaker throughout the recording
2. **TimeMapInterval**: Maps an interval of time from the original timeline to the transformed timeline
3. **TimeMap**: Collection of intervals that collectively define the complete timeline transformation

This minimalist approach makes the design:
- More intuitive to understand
- Easier to implement and maintain
- Directly mapped to real-world entities

### 9.3 Modifications to Existing Code

1. **DiarizationProcessor**:
   - No changes needed - already produces required data format

2. **audio_transcribe.py**:
   - Extend CLI options for diarization and SRT generation
   - Add pipeline stage for track generation and remapping

3. **Pyannote Client**:
   - No changes needed

## 10. Extensibility for Language Detection

The design supports future language detection with minimal changes:

```mermaid
graph TD
    A[Audio File] --> B[Diarization]
    B --> C[Speaker Segmentation]
    C --> D[Language Detection]
    D --> E1[Speaker 1 + Language A]
    D --> E2[Speaker 1 + Language B]
    D --> E3[Speaker 2 + Language A]
    E1 --> F1[Transcription Engine A]
    E2 --> F2[Transcription Engine B]
    E3 --> F3[Transcription Engine A]
    F1 --> G[Time Remapping]
    F2 --> G
    F3 --> G
```

The speaker track abstraction already accommodates this extension through:

1. **Composable Track Generator**:
   - Language detection can be added as a stage between speaker segmentation and track generation
   - Results can feed into extended version of SpeakerTrack

2. **Extended TimeMap Structure**:
   - TimeMap structure can accommodate additional metadata like language
   - Segments can be tagged with language information

3. **Specialized Transcription Engines**:
   - SpeakerTrack can be extended with language information
   - Transcription pipeline can select appropriate engine based on language

## 11. Implementation Plan

1. **Phase 1: Core Infrastructure**
   - Implement TimeMap and related utilities
   - Create SpeakerTrack data structures
   - Build SRT parsing/writing utilities

2. **Phase 2: Audio Processing**
   - Implement track consolidation
   - Add gap insertion logic
   - Build audio segment extraction

3. **Phase 3: Integration**
   - Extend AudioPipeline with new stages
   - Create CLI integration
   - Add configuration options

4. **Phase 4: Testing and Refinement**
   - Test with various speaker patterns
   - Fine-tune timing accuracy
   - Optimize performance

## 12. Configuration Options

The design supports the following configuration options:

1. **Speaker Gap Duration**: Time gap (in seconds) to insert between non-contiguous segments
2. **Minimum Segment Duration**: Threshold for including a speaker segment
3. **Maximum Audio Processing Chunk**: Size limit for audio processing to manage memory usage
4. **Audio Export Format**: Format options for speaker tracks (MP3, WAV, etc.)
5. **SRT Output Options**: Character encoding, line formatting, etc.
6. **Timeline Tolerance**: Precision threshold for timestamp mapping operations

## 13. Future Development Needs

### 13.1 Testing Strategy

A comprehensive testing strategy will need to be developed for the production version. This should include unit tests for core algorithms, integration tests for component interactions, and end-to-end tests with real audio samples. Performance benchmarks and accuracy measurements will be essential for validating the system.

### 13.2 Performance Optimization

While the prototype implementation focuses on correctness, the production version will require performance optimization. This includes memory management for large audio files, potentially implementing streaming processing for segments, and parallelizing independent operations like speaker track processing.

### 13.3 Integration Details

Detailed integration specifications with existing TNH Scholar components will be required. This includes formal API definitions, compatibility requirements, and version management strategies to ensure smooth integration with the broader system.

### 13.4 Validation Metrics

A formal set of validation metrics needs to be established. This should include measures of diarization accuracy (speaker identification precision/recall), timing accuracy (temporal alignment of speech segments), and overall quality metrics for the final output.

## 14. Conclusion

This design provides an elegant and streamlined approach to speaker-specific transcription with accurate time mapping. By focusing on essential concepts and removing unnecessary complexity, the implementation will be both intuitive and maintainable.

The core of the design is the simplified TimeMapInterval concept, which maps sections of the original audio timeline to the transformed timeline with minimal complexity. This approach elegantly handles the complex interleaved speaker patterns common in real conversations.

The system requires minimal changes to existing code while providing a powerful new capability. By adhering to the single-action function principle and applying Occam's razor to remove unnecessary components, this design achieves conceptual clarity without sacrificing functionality.

This streamlined architecture will be easier to implement, test, and extend in the future, providing a solid foundation for enhancements such as language detection.
