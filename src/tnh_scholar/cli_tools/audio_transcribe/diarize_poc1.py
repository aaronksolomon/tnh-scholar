import json
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import List


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
        
@dataclass
class TimeMapInterval:
    """Maps a segment from original timeline to transformed timeline."""
    original_start: Decimal  # Start time in original audio (seconds)
    original_end: Decimal    # End time in original audio (seconds) 
    transformed_start: Decimal  # Start time in consolidated audio (seconds)
    
    @property
    def duration(self) -> Decimal:
        """Duration of the interval (same in both timelines)."""
        return self.original_end - self.original_start
    
    @property
    def transformed_end(self) -> Decimal:
        """End time in the transformed timeline."""
        return self.transformed_start + self.duration

@dataclass
class TimeMap:
    """Maps time points between original and transformed timelines for a speaker."""
    speaker_id: str
    intervals: List[TimeMapInterval] = field(default_factory=list)
    
    def add_interval(self, original_start: Decimal, original_end: Decimal, 
                    transformed_start: Decimal) -> None:
        """Add a new mapping interval."""
        interval = TimeMapInterval(
            original_start=original_start,
            original_end=original_end,
            transformed_start=transformed_start
        )
        self.intervals.append(interval)
    
    def map_time(self, original_time: Decimal) -> Decimal:
        """Map a time from original timeline to transformed timeline."""
        def new_time(interval):
            return Decimal(
                interval.transformed_start + (original_time - interval.original_start)
                )
        return next(
            (
                new_time(interval)
                for interval in self.intervals
                if interval.original_start
                <= original_time
                <= interval.original_end
            ),
            -1,
        )
    
    def reverse_map_time(self, transformed_time: Decimal) -> Decimal:
        """Map a time from transformed timeline back to original timeline."""
        # Find the interval containing this time
        for interval in self.intervals:
            trans_end = interval.transformed_start + interval.duration
            if interval.transformed_start <= transformed_time <= trans_end:
                # Calculate relative position within interval
                relative_pos = transformed_time - interval.transformed_start
                return interval.original_start + relative_pos
        return -1  # Indicates time not found in any interval
    
    def save_to_json(self, output_path: Path) -> None:
        """Save time map to JSON file."""
        data = {
            "speaker_id": self.speaker_id,
            "intervals": [
                {
                    "original_start": interval.original_start,
                    "original_end": interval.original_end,
                    "transformed_start": interval.transformed_start,
                    "duration": interval.duration,
                    "transformed_end": interval.transformed_end
                }
                for interval in self.intervals
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load_from_json(cls, file_path: Path) -> 'TimeMap':
        """Load time map from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        time_map = cls(speaker_id=data["speaker_id"])
        for interval_data in data["intervals"]:
            time_map.add_interval(
                original_start=interval_data["original_start"],
                original_end=interval_data["original_end"],
                transformed_start=interval_data["transformed_start"]
            )
        return time_map

def process_diarization_with_timemap(segments):
    """
    Process diarization segments sequentially, extending each segment to the 
    start of the next one (regardless of speaker). Also generates time maps.
    
    Returns:
        Tuple containing:
        - Dictionary where keys are speaker IDs and values are lists of (start, end) tuples
        - Dictionary where keys are speaker IDs and values are TimeMap objects
    """
    # Ensure segments are sorted by start time
    sorted_segments = sorted(segments, key=lambda s: s.start)

    # Initialize
    speaker_blocks = {}
    time_maps = {}
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
        current_end = next_segment.start if next_segment else segment.end
    # Add the final block
    if current_speaker is not None:
        if current_speaker not in speaker_blocks:
            speaker_blocks[current_speaker] = []
        speaker_blocks[current_speaker].append((current_start, current_end))

    # Generate time maps for each speaker
    for speaker, blocks in speaker_blocks.items():
        time_map = TimeMap(speaker_id=speaker)
        transformed_start = 0.0  # Track position in consolidated audio

        for original_start, original_end in blocks:
            # Add interval to time map
            time_map.add_interval(
                original_start=original_start,
                original_end=original_end,
                transformed_start=transformed_start
            )

            # Update position in consolidated audio
            transformed_start += (original_end - original_start)

        time_maps[speaker] = time_map

    return speaker_blocks, time_maps

def export_audio_with_timemap(original_audio, speaker_blocks, time_maps, output_dir):
    """
    Example code showing how audio would be extracted with time mapping.
    
    Args:
        original_audio: The original audio file (e.g., AudioSegment)
        speaker_blocks: Dictionary mapping speakers to their blocks
        time_maps: Dictionary mapping speakers to their TimeMap objects
        output_dir: Directory to save exported files
    
    Returns:
        Dictionary mapping speakers to their exported audio file paths
    """
    output_paths = {}
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # For each speaker
    for speaker, blocks in speaker_blocks.items():
        print(f"Processing audio for {speaker}")
        
        # Get time map
        time_map = time_maps[speaker]
        
        # Create empty audio for this speaker
        speaker_audio = original_audio.__class__.empty()  # Placeholder for empty audio segment
        
        # For each block
        for start, end in blocks:
            # Convert to milliseconds for audio processing
            start_ms = Decimal(start * 1000)
            end_ms = Decimal(end * 1000)
            
            # Extract segment (placeholder for actual audio extraction)
            segment_audio = original_audio[start_ms:end_ms]
            
            # Add to speaker audio
            speaker_audio += segment_audio
        
        # Export speaker audio
        output_path = output_dir / f"speaker_{speaker}.mp3"
        # speaker_audio.export(output_path, format="mp3")  # Commented out as this is just a PoC
        output_paths[speaker] = output_path
        
        # Save time map
        time_map_path = output_dir / f"speaker_{speaker}_timemap.json"
        time_map.save_to_json(time_map_path)
        print(f"Saved time map to {time_map_path}")
    
    return output_paths

def time_mapping_trial():
    """Demonstrate time mapping functionality with example data."""
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

    # Load and process segments
    segments = []
    segments.extend(
        DiarizationSegment(
            speaker=segment_data["speaker"],
            start=segment_data["start"],
            end=segment_data["end"],
        )
        for segment_data in sample_data["output"]["diarization"]
    )
    # Process with time mapping
    speaker_blocks, time_maps = process_diarization_with_timemap(segments)

    # Display results
    print("\nSpeaker blocks with time mapping:")
    for speaker, blocks in speaker_blocks.items():
        print(f"\n{speaker}:")
        for i, (start, end) in enumerate(blocks):
            print(f"  Block {i+1}: {start:.3f}s - {end:.3f}s ({end-start:.3f}s)")

    # Test time mapping
    print("\nTime mapping examples:")
    for speaker, time_map in time_maps.items():
        print(f"\n{speaker} mapping:")
        for interval in time_map.intervals:
            print(f"  Original: {interval.original_start:.3f}s-{interval.original_end:.3f}s → "
                  f"Transformed: {interval.transformed_start:.3f}s-{interval.transformed_end:.3f}s")

        # Test specific timestamps
        if time_map.intervals:
            # Test middle of first interval
            first = time_map.intervals[0]
            test_time = (first.original_start + first.original_end) / 2
            mapped_time = time_map.map_time(test_time)
            reverse_mapped = time_map.reverse_map_time(mapped_time)

            print(f"\n  Test: Original {test_time:.3f}s → "
                  f"Transformed {mapped_time:.3f}s → "
                  f"Reverse mapped {reverse_mapped:.3f}s")

    return speaker_blocks, time_maps

if __name__ == "__main__":

    time_mapping_trial()