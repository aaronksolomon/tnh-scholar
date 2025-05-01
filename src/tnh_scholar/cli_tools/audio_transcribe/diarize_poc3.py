import json
import re
from collections import defaultdict
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from httpx import InvalidURL
import matplotlib.pyplot as plt
from pydub import AudioSegment

from tnh_scholar.audio_processing.transcription_service import (
    TranscriptionFormatConverter,
    TranscriptionServiceFactory,
)
from tnh_scholar.audio_processing.transcription_service.diarization_chunker import Chunk
from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils.file_utils import write_str_to_file

logger = get_child_logger(__name__)

GAP_THRESHOLD = 2000
SILENCE_SPACING = 1000

# target duration for speaker chunks
TARGET_DURATION = 5 * 60 * 1000 # 5 mins

@dataclass
class DiarizationSegment:
    """Represents a single speaker segment from diarization."""
    speaker: str
    start_ms: int  # Start time in milliseconds
    end_ms: int    # End time in milliseconds
    
    @property
    def duration_ms(self) -> int:
        """Get segment duration in milliseconds."""
        return self.end_ms - self.start_ms
    
    @property
    def start_sec(self) -> float:
        """Get start time in seconds (for display)."""
        return self.start_ms / 1000.0
    
    @property
    def end_sec(self) -> float:
        """Get end time in seconds (for display)."""
        return self.end_ms / 1000.0
    
    @property
    def duration_sec(self) -> float:
        """Get duration in seconds (for display)."""
        return self.duration_ms / 1000.0


def load_diarization_result(file_path=None):
    """Load diarization result from JSON file or sample data."""
    if not file_path:
        raise ValueError("Either file_path or sample_data must be provided")

    with open(file_path, 'r') as f:
        data = json.load(f)

    return data
        
    # segments = []
    # for segment_data in data["output"]["diarization"]:
    #     # Convert seconds to milliseconds
    #     start_ms = int(float(segment_data["start"]) * 1000)
    #     end_ms = int(float(segment_data["end"]) * 1000)

    #     segments.append(
    #         DiarizationSegment(
    #             speaker=segment_data["speaker"],
    #             start_ms=start_ms,
    #             end_ms=end_ms,
    #         )
    #     )
    # logger.info(f"Loaded {len(segments)} segments from diarization result")
    # return segments


def process_diarization(segments):
    """
    Process diarization segments sequentially, extending each segment to the 
    start of the next one (regardless of speaker).
    
    Returns:
        Dictionary where:
        - Keys are speaker IDs
        - Values are lists of (start_ms, end_ms) tuples for speaker blocks
    """
    # Ensure segments are sorted by start time
    sorted_segments = segments
    
    # Initialize
    speaker_blocks = {}
    current_speaker = None
    current_start_ms = None
    current_end_ms = None
    
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
                speaker_blocks[current_speaker].append(
                    (current_start_ms, current_end_ms)
                    )
            
            # Start a new block for this speaker
            current_speaker = segment.speaker
            current_start_ms = segment.start_ms
            current_end_ms = segment.end_ms
        
        # If next segment exists, extend current end to next segment's start
        if next_segment:
            current_end_ms = next_segment.start_ms
        
    # Add the final block
    if current_speaker is not None:
        if current_speaker not in speaker_blocks:
            speaker_blocks[current_speaker] = []
        speaker_blocks[current_speaker].append((current_start_ms, current_end_ms))
    
    return speaker_blocks


def merge_speaker_segments(
    segments: List[DiarizationSegment]
    ) -> Dict[str, List[Tuple[int, int]]]:
    """
    Given a list of diarization segments in (speaker, start_ms, end_ms) form:
      1) Sort them by start_ms.
      2) Merge consecutive or overlapping segments if they share the same speaker.
      3) As soon as a different speaker appears, finalize the current speaker's block
         and start a new block for the new speaker.

    Returns a dictionary of { speaker: [(start_ms, end_ms), (start_ms, end_ms), ...] }.
    Note that each speaker may appear multiple times, non-consecutively, so you may
    have multiple blocks for that speaker in the final dictionary.
    """
    # 1) Sort input by start_ms
    segments = sorted(segments, key=lambda seg: seg.start_ms)

    speaker_blocks = defaultdict(list)

    # We'll track the "current" speaker block as we iterate
    current_speaker = None
    current_start = None
    current_end = 0

    for seg in segments:
        if seg.speaker != current_speaker:
            # A different speaker has begun,
            # so finalize the old block if there was one
            if current_speaker is not None:
                speaker_blocks[current_speaker].append((current_start, current_end))

            # Start a fresh block for the new speaker
            current_speaker = seg.speaker
            current_start = seg.start_ms
            current_end = seg.end_ms

        elif seg.start_ms <= current_end + GAP_THRESHOLD:
            current_end = max(current_end, seg.end_ms)
        else:
            # There's a gap in the timeline for the same speaker.
            # Finalize the old block and start a new block for the same speaker
            speaker_blocks[current_speaker].append((current_start, current_end))
            current_start = seg.start_ms
            current_end = seg.end_ms

    # Don't forget to finalize the last block
    if current_speaker is not None:
        speaker_blocks[current_speaker].append((current_start, current_end))

    return dict(speaker_blocks)


def extract_audio_segments(
    original_audio_path: Path,
    speaker_chunks: Dict[str, List[Chunk]],
    add_padding: bool = True,
    padding_ms: int = SILENCE_SPACING
) -> Tuple[Dict[str, List[BytesIO]], Dict[str, List[List[Tuple[int, int, int]]]], Dict[str, List[int]]]:
    
    # Set audio_format
    audio_format = original_audio_path.suffix[1:]
    print(f"Using audio format: {audio_format}")
    
    # Load original audio
    print(f"Loading original audio from {original_audio_path}")
    original_audio = AudioSegment.from_file(str(original_audio_path))

    # Generate silence for padding if needed
    silence = AudioSegment.silent(duration=padding_ms) if add_padding else None

    # Track output paths and timing maps
    speaker_mapped_blocks = {}

    # Accumulation list for all speaker audio results
    speaker_audio_files = {}
    
    # Acumulation list for offset times 
    # (the time that chunked audio files start in original file)
    speaker_offset_times = {}
    
    # Process each speaker
    for speaker, chunk_list in speaker_chunks.items():
        print(f"Processing {len(chunk_list)} segments for {speaker}")

        # Initialize empty audio for this speaker
        speaker_audio = AudioSegment.empty()

        # Create a new list for the mapped blocks (with export timeline position)
        mapped_blocks = []

        # Initialize speaker_audio_files
        speaker_audio_files[speaker] = []
        
        # Initialize speaker_mapped_blocks
        speaker_mapped_blocks[speaker] = []
        
        # Initialize speaker_offset_times
        speaker_offset_times[speaker] = []
        
        # Track absolute speaker export time
        abs_export_pos = 0
        
        # For each speaker block
        segment_counter = 0
        current_export_pos = 0  # Position in the exported audio (in milliseconds)
        for i, chunk in enumerate(chunk_list):
            start_ms = chunk.start_time
            end_ms = chunk.end_time
            
            # Extract segment
            segment_audio = original_audio[start_ms:end_ms]

            # Add padding if not the first segment
            if segment_counter > 0 and add_padding:
                speaker_audio += silence
                current_export_pos += padding_ms

            # Store mapping (original_start_ms, original_end_ms, export_start_ms)
            mapped_blocks.append((start_ms, end_ms, current_export_pos))
            print(f"  Added segment {i+1}: {start_ms/1000:.3f}s - {end_ms/1000:.3f}s "
                  f"(export pos: {current_export_pos/1000:.3f}s)"
                  )

            # Add to speaker audio
            speaker_audio += segment_audio

            # Update current position in exported audio and counter
            current_export_pos = current_export_pos + (end_ms - start_ms)
            segment_counter += 1
            
            # Check for export threshold
            if current_export_pos >= TARGET_DURATION:
                print(f"-> creating export audio file object at chunk: {i+1}\n"
                      f"    -> current export position: {current_export_pos}, absolute export position: {abs_export_pos}")
                speaker_audio_files[speaker].append(
                    _create_export_audio_file_obj(speaker, speaker_audio, audio_format)
                )
                speaker_mapped_blocks[speaker].append(mapped_blocks)
                speaker_offset_times[speaker].append(abs_export_pos)
                
                # Update state
                abs_export_pos += current_export_pos # store absolute export position
                current_export_pos = 0
                mapped_blocks = []
                speaker_audio = AudioSegment.empty()
                segment_counter = 0
                
        # finalize remaining blocks
        if mapped_blocks:
            print(f"-> creating final export audio file object.\n"
                      f"     current export position: {current_export_pos}")
            speaker_audio_files[speaker].append(
                    _create_export_audio_file_obj(speaker, speaker_audio, audio_format)
                )
            speaker_mapped_blocks[speaker].append(mapped_blocks)
            abs_export_pos += current_export_pos
            speaker_offset_times[speaker] = abs_export_pos
            
    return speaker_audio_files, speaker_mapped_blocks, speaker_offset_times

def _create_export_audio_file_obj(speaker, speaker_audio, audio_format):
    # Export speaker audio
    speaker_file_obj = BytesIO()
    speaker_audio.export(speaker_file_obj, format=audio_format)
    speaker_file_obj.seek(0)  # Reset file pointer to beginning
    # Add a filename for whisper to recognize
    speaker_file_obj.name = f"{speaker}.{audio_format}"
    return speaker_file_obj

def srt_time_to_ms(timestamp: str) -> int:
    """Convert SRT timestamp (HH:MM:SS,mmm) to milliseconds."""
    pattern = r"(\d+):(\d+):(\d+),(\d+)"
    match = re.match(pattern, timestamp)
    if not match:
        raise ValueError(f"Invalid timestamp format: {timestamp}")
    
    hours, minutes, seconds, milliseconds = map(int, match.groups())
    return hours * 3600000 + minutes * 60000 + seconds * 1000 + milliseconds

def ms_to_srt_time(milliseconds: int) -> str:
    """Convert milliseconds to SRT timestamp format (HH:MM:SS,mmm)."""
    hours, remainder = divmod(milliseconds, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def build_offset_intervals(speaker_blocks):
    """
    Convert a list of (orig_start, orig_end, offset_start)
    into a list of 4-tuples:
      (orig_start_ms, orig_end_ms, off_start_ms, off_end_ms)
    by pairing each offset_start with the next offset_start as off_end.
    """
    intervals = []
    n = len(speaker_blocks)
    for i in range(n):
        orig_start, orig_end, off_start = speaker_blocks[i]
        # if not the last block, the 'end' of the offset interval
        if i < n - 1:
            _, _, next_off_start = speaker_blocks[i + 1]
            off_end = next_off_start
        else:
            # last one extends to a large sentinel or the end of the file
            off_end = 999999999  # or some suitably large number
        intervals.append((orig_start, orig_end, off_start, off_end))
    return intervals

def transform_srt_by_best_overlap(srt_entries, speaker_blocks):
    """
    srt_entries: [(start_time_str, end_time_str, text), ...] in the *offset* domain
    speaker_blocks: [(orig_start_ms, orig_end_ms, offset_start_ms), ...]

    1) Build piecewise offset intervals from 'speaker_blocks'.
    2) For each SRT entry, find which interval it overlaps the most.
    3) Map the SRT times into the original domain via a simple linear shift:
         original_time = interval_orig_start + (offset_time - interval_off_start).
    """

    intervals = build_offset_intervals(speaker_blocks)
    transformed = []

    for (index, start_str, end_str, text) in srt_entries:
        srt_start = srt_time_to_ms(start_str)
        srt_end   = srt_time_to_ms(end_str)

        best_overlap = 0
        best_interval = None

        # Find the interval with the greatest overlap
        for (orig_start, orig_end, off_start, off_end) in intervals:
            overlap = max(0, min(srt_end, off_end) - max(srt_start, off_start))
            if overlap > best_overlap:
                best_overlap = overlap
                best_interval = (orig_start, orig_end, off_start, off_end)

        if not best_interval:
            # no overlap at all, optionally skip or map it in some default way
            transformed.append((index, start_str, end_str, text))
            print("Error: No best interval found.")
            continue

        # We have an interval that matches best. 
        # Map the entire SRT entry to original domain
        (i_orig_start, i_orig_end, i_off_start, i_off_end) = best_interval

        # Shift times from offset domain => original domain
        new_start_ms = i_orig_start + (srt_start - i_off_start)
        new_end_ms   = i_orig_start + (srt_end   - i_off_start)

        # Re-format as SRT
        new_start_str = ms_to_srt_time(new_start_ms)
        new_end_str   = ms_to_srt_time(new_end_ms)

        transformed.append((index, new_start_str, new_end_str, text))

    return transformed

def transform_srt(
    srt_data: str,
    mapped_blocks: List[Tuple[int, int, int]],
) -> str:
    """
    Transform SRT timestamps from speaker timeline to original timeline.
    
    Args:
        srt_data: SRT string with for speaker timeline
        mapped_blocks: Mapping information: (original_start, original_end, export_start) tuples
        output_path: Optional path to save the transformed SRT
        
    Returns:
        Transformed SRT content as string
    """
    # Parse the SRT content (simple regex-based approach)
    pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n((?:.+\n)+)"
    entries = re.findall(pattern, srt_data, re.MULTILINE)


    logger.info(f"SRT entries parsed {entries}")
    transformed_entries = []

    transformed_data = transform_srt_by_best_overlap(entries, mapped_blocks)

    transformed_entries.extend(
        f"{index}\n{new_start_str} --> {new_end_str}\n{text.strip()}\n"
        for index, new_start_str, new_end_str, text in transformed_data
    )
    return "\n".join(transformed_entries)

def gen_srt(audio_file_obj, 
            provider="whisper", 
            language=None, 
            local_convert=False, 
            include_speaker=True):
    """
    generate srt
    """
    format_type = "srt"
    # Create the transcription service
    service = TranscriptionServiceFactory.create_service(provider=provider)

    # Print some info
    print(f"Running {format_type.upper()} generation with {provider} service...")
    print(f"Audio file: {audio_file_obj}")

    transcription_options = {"language": language} if language else None
    
    # Generate the formatted transcription
    # use the local format converter if specified
    if local_convert:
        convert_options = {"include_speaker": include_speaker}
        converter = TranscriptionFormatConverter()
        transcript = service.transcribe(audio_file_obj, options=transcription_options)
        
        return converter.convert(transcript, format_options=convert_options)
        
    return service.transcribe_to_format(
        audio_file_obj, 
        format_type=format_type,
        transcription_options=transcription_options
    )

def visualize_results(segments, speaker_blocks):
    """
    Redesign of visualize_results. Produces two subplots:
      Top: the original diarization segments
      Bottom: the processed (extended) speaker blocks, sorted by start_ms
    """

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # ---------------------------
    # 1) Plot original segments
    # ---------------------------
    # Sort by start_ms
    sorted_segments = sorted(segments, key=lambda s: s.start_ms)

    # Collect all speakers for color assignment
    all_speakers = sorted({seg.speaker for seg in sorted_segments} 
                          | set(speaker_blocks.keys()))
    # Use a discrete colormap
    colors = plt.cm.tab10(range(len(all_speakers)))
    speaker_colors = dict(zip(all_speakers, colors))

    # Plot each original segment as a bar
    for seg in sorted_segments:
        duration_sec = seg.duration_sec
        ax1.barh(
            y=seg.speaker,
            width=duration_sec,
            left=seg.start_sec,
            height=0.6,
            color=speaker_colors[seg.speaker],
            alpha=0.6
        )

    ax1.set_title("Original Diarization Segments")
    ax1.set_ylabel("Speaker")
    ax1.grid(True, axis='x', linestyle='--', alpha=0.3)

    # ----------------------------------------
    # 2) Plot processed/extended speaker blocks
    # ----------------------------------------
    # Flatten everything into (start_ms, end_ms, speaker)
    all_blocks = []
    for speaker, blocks in speaker_blocks.items():
        for (start_ms, end_ms) in blocks:
            all_blocks.append((start_ms, end_ms, speaker))

    # Sort by start_ms
    all_blocks.sort(key=lambda x: x[0])

    # Plot each block
    for start_ms, end_ms, speaker in all_blocks:
        start_sec = start_ms / 1000.0
        end_sec = end_ms / 1000.0
        ax2.barh(
            y=speaker,
            width=(end_sec - start_sec),
            left=start_sec,
            height=0.6,
            color=speaker_colors[speaker]
        )

    ax2.set_title("Extended Speaker Blocks (Chronologically Sorted)")
    ax2.set_xlabel("Time (seconds)")
    ax2.set_ylabel("Speaker")
    ax2.grid(True, axis='x', linestyle='--', alpha=0.3)

    # ----------------------------------------
    # 3) Optional legend for clarity
    # ----------------------------------------
    # Build handles/labels from all_speakers
    handles = []
    labels = []
    for sp in all_speakers:
        handles.append(plt.Rectangle((0, 0), 1, 1, color=speaker_colors[sp]))
        labels.append(sp)
    ax2.legend(
        handles,
        labels,
        loc='upper center',
        bbox_to_anchor=(0.5, -0.15),
        ncol=min(len(all_speakers), 5)
    )

    plt.tight_layout()
    return fig


def visualize_merged_timeline(speaker_blocks):
    """
    Create a single timeline visualization with 
    different colored blocks for each speaker.
    
    Args:
        speaker_blocks: Dictionary mapping speaker IDs 
        to lists of (start_ms, end_ms) tuples
        
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
        all_blocks.extend((start_ms, end_ms, speaker) for start_ms, end_ms in blocks)
    # Sort blocks by start time
    all_blocks.sort(key=lambda x: x[0])

    # Plot each block with appropriate color
    for start_ms, end_ms, speaker in all_blocks:
        start_sec = start_ms / 1000.0
        end_sec = end_ms / 1000.0
        ax.barh(y_pos, end_sec - start_sec, left=start_sec, height=0.8, 
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

# def transform_srt(
#     srt_path: Path,
#     mapped_blocks: List[Tuple[int, int, int]],
#     output_path: Optional[Path] = None
# ) -> str:
#     """
#     Transform SRT timestamps from speaker timeline to original timeline.
    
#     Args:
#         srt_path: Path to the SRT file with speaker timeline
#         mapped_blocks: Mapping information: (original_start, original_end, export_start) tuples
#         output_path: Optional path to save the transformed SRT
        
#     Returns:
#         Transformed SRT content as string
#     """
#     # Read the SRT file
#     with open(srt_path, "r", encoding="utf-8") as f:
#         content = f.read()

#     # Parse the SRT content (simple regex-based approach)
#     pattern = r"(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n((?:.+\n)+)"
#     entries = re.findall(pattern, content, re.MULTILINE)

#     print(entries)
#     transformed_entries = []

#     transformed_data = transform_srt_by_best_overlap(entries, mapped_blocks)

#     transformed_entries.extend(
#         f"{index}\n{new_start_str} --> {new_end_str}\n{text.strip()}\n"
#         for index, new_start_str, new_end_str, text in transformed_data
#     )
#     # Join entries with a blank line
#     transformed_content = "\n".join(transformed_entries)

#     # Save to output file if specified
#     if output_path:
#         write_str_to_file(output_path, transformed_content, overwrite=True)
#         print(f"Transformed SRT saved to {output_path}")

#     return transformed_content