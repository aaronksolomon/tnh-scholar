import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
from pydub import AudioSegment


@dataclass
class DiarizationSegment:
    """Represents a single speaker segment from diarization."""
    speaker: str
    start: Decimal
    end: Decimal
    
    @property
    def duration(self) -> Decimal:
        """Get segment duration in seconds."""
        return self.end - self.start

def load_diarization_result(file_path=None, sample_data=None):
    """Load diarization result from JSON file or sample data."""
    if file_path:
        with open(file_path, 'r') as f:
            data = json.load(f)
    elif sample_data:
        data = sample_data
    else:
        raise ValueError("Either file_path or sample_data must be provided")

    segments = []
    segments.extend(
        DiarizationSegment(
            speaker=segment_data["speaker"],
            start=segment_data["start"],
            end=segment_data["end"],
        )
        for segment_data in data["output"]["diarization"]
    )
    print(f"Loaded {len(segments)} segments from diarization result")
    return segments

def process_diarization(segments):
    """
    Process diarization segments sequentially, extending each segment to the 
    start of the next one (regardless of speaker).
    
    Returns:
        Dictionary where:
        - Keys are speaker IDs
        - Values are lists of (start_time, end_time) tuples for speaker blocks
    """
    # Ensure segments are sorted by start time
    sorted_segments = sorted(segments, key=lambda s: s.start)
    
    # Initialize
    speaker_blocks = {}
    current_speaker = None
    current_start = None
    current_end = None
    
    # Process each segment sequentially
    for i, segment in enumerate(sorted_segments):
        # Get next segment for gap handling (if available)
        next_segment = sorted_segments[i+1] if i < len(sorted_segments) - 1 else None
        
        # If current segment is from a different speaker than current_speaker
        if segment.speaker != current_speaker:
            # Save the current block if it exists
            if current_speaker is not None:
                if current_speaker not in speaker_blocks:
                    speaker_blocks[current_speaker] = []
                speaker_blocks[current_speaker].append((current_start, current_end))
            
            # Start a new block for this speaker
            current_speaker = segment.speaker
            current_start = segment.start
            current_end = segment.end
        
        # If next segment exists, extend current end to next segment's start
        if next_segment:
            current_end = next_segment.start
        
    # Add the final block
    if current_speaker is not None:
        if current_speaker not in speaker_blocks:
            speaker_blocks[current_speaker] = []
        speaker_blocks[current_speaker].append((current_start, current_end))
    
    return speaker_blocks

def visualize_results(segments, speaker_blocks):
    """Visualize original segments and processed blocks."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # Get all speakers
    speakers = sorted({segment.speaker for segment in segments})
    colors = plt.cm.tab10(range(len(speakers)))
    speaker_colors = dict(zip(speakers, colors))

    # Plot original segments
    for segment in sorted(segments, key=lambda s: s.start):
        ax1.barh(segment.speaker, segment.duration, left=segment.start, 
                height=0.6, color=speaker_colors[segment.speaker], alpha=0.6)

    # Plot processed blocks
    for speaker, blocks in speaker_blocks.items():
        for start, end in blocks:
            ax2.barh(speaker, end - start, left=start,
                   height=0.6, color=speaker_colors[speaker])

    # Set titles and labels
    ax1.set_title("Original Diarization Segments")
    ax2.set_title("Extended Speaker Blocks")
    ax2.set_xlabel("Time (seconds)")

    # Add grid lines
    ax1.grid(True, axis='x', linestyle='--', alpha=0.3)
    ax2.grid(True, axis='x', linestyle='--', alpha=0.3)

    plt.tight_layout()
    return fig

def visualize_merged_timeline(speaker_blocks):
    """
    Create a single timeline visualization with 
    different colored blocks for each speaker.
    
    Args:
        speaker_blocks: Dictionary mapping speaker IDs to lists of (start, end) tuples
        
    Returns:
        Matplotlib figure
    """
    fig, ax = plt.subplots(figsize=(12, 4))

    # Get all speakers and assign colors
    speakers = sorted(speaker_blocks.keys())
    colors = plt.cm.tab10(range(len(speakers)))
    speaker_colors = dict(zip(speakers, colors))

    # Create a single y-position for all blocks
    y_pos = 1

    # Gather all blocks with speaker info
    all_blocks = []
    for speaker, blocks in speaker_blocks.items():
        all_blocks.extend((start, end, speaker) for start, end in blocks)
    # Sort blocks by start time
    all_blocks.sort(key=lambda x: x[0])

    # Plot each block with appropriate color
    for start, end, speaker in all_blocks:
        ax.barh(y_pos, end - start, left=start, height=0.8, 
                color=speaker_colors[speaker], label=speaker)

    # Create legend (with unique labels)
    handles, labels = [], []
    for speaker in speakers:
        handles.append(plt.Rectangle((0, 0), 1, 1, color=speaker_colors[speaker]))
        labels.append(speaker)
    ax.legend(handles, labels, loc='upper center', 
              bbox_to_anchor=(0.5, -0.1), ncol=len(speakers))

    # Remove y-axis ticks and labels
    ax.set_yticks([])
    ax.set_yticklabels([])

    # Set title and labels
    ax.set_title("Merged Speaker Timeline")
    ax.set_xlabel("Time (seconds)")

    # Add grid lines
    ax.grid(True, axis='x', linestyle='--', alpha=0.3)

    plt.tight_layout()
    return fig

def extract_audio_segments(
    original_audio_path: Path,
    speaker_blocks: Dict[str, List[Tuple[Decimal, Decimal]]],
    output_dir: Path,
    add_padding: bool = True,
    padding_ms: int = 1000
) -> Dict[str, Tuple[Path, Dict[str, List[Tuple[Decimal, Decimal, Decimal]]]]]:
    
    # Load original audio
    print(f"Loading original audio from {original_audio_path}")
    original_audio = AudioSegment.from_file(str(original_audio_path))

    # Generate silence for padding if needed
    silence = AudioSegment.silent(duration=padding_ms) if add_padding else None
    padding_sec = Decimal(padding_ms / 1000) if add_padding else Decimal(0)

    # Track output paths and timing maps
    output_results = {}

    # Process each speaker
    for speaker, blocks in speaker_blocks.items():
        print(f"Processing {len(blocks)} segments for {speaker}")

        # Create empty audio for this speaker
        speaker_audio = AudioSegment.empty()

        # Create a new list for the mapped blocks (with export timeline position)
        mapped_blocks = []

        # For each block
        current_export_pos = Decimal(0.000)  # Position in the exported audio (in seconds)

        for i, (start, end) in enumerate(blocks):
            # Convert to milliseconds for pydub
            start_ms = Decimal(start * 1000)
            end_ms = Decimal(end * 1000)

            # Extract segment
            segment_audio = original_audio[float(start_ms):float(end_ms)]

            # Add padding if not the first segment
            if i > 0 and add_padding:
                speaker_audio += silence
                current_export_pos += padding_sec

            # Store mapping (original_start, original_end, export_start)
            mapped_blocks.append((start, end, current_export_pos))
            print(f"  Added segment {i+1}: {start}s - {end}s "
                  f"(export pos: {current_export_pos}s)"
                  )

            # Add to speaker audio
            speaker_audio += segment_audio

            # Update current position in exported audio
            current_export_pos = current_export_pos + Decimal(end - start)

        # Export speaker audio
        output_path = output_dir / f"{speaker}.mp3"
        speaker_audio.export(str(output_path), format="mp3")
        print(f"Exported {output_path} ({len(speaker_audio)/1000}s)")

        # Save path and mapping for return
        output_results[speaker] = (output_path, mapped_blocks)

    return {speaker: blocks for speaker, (_, blocks) in output_results.items()}


sample_data = {
  "status": "succeeded",
  "output": {
    "diarization": [
      {"speaker": "SPEAKER_01", "start": 0.005, "end": 0.645},
      {"speaker": "SPEAKER_01", "start": 1.225, "end": 4.325},
      {"speaker": "SPEAKER_01", "start": 6.365, "end": 7.865},
      {"speaker": "SPEAKER_00", "start": 10.125, "end": 10.745},
      {"speaker": "SPEAKER_00", "start": 13.165, "end": 15.485},
      {"speaker": "SPEAKER_00", "start": 15.865, "end": 17.985},
      {"speaker": "SPEAKER_01", "start": 18.500, "end": 21.250},
      {"speaker": "SPEAKER_01", "start": 21.500, "end": 22.750},
      {"speaker": "SPEAKER_00", "start": 23.100, "end": 25.400}
    ]
  }
}

