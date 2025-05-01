from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from pydub import AudioSegment

from tnh_scholar.logging_config import get_child_logger
from tnh_scholar.utils.file_utils import ensure_directory_exists

# Import existing models
from .diarize import SpeakerChunk

logger = get_child_logger(__name__)

@dataclass
class ConsolidatorConfig:
    """Configuration for audio consolidation."""
    contiguous_gap: float = 0.15
    non_contiguous_gap: float = 1.0
    output_format: str = "mp3"


class SpeakerTrack:
    """Represents a consolidated audio track for a single speaker."""
    
    def __init__(self, speaker: str):
        """
        Initialize a speaker track.
        
        Args:
            speaker: Speaker identifier
        """
        self.speaker = speaker
        self.audio = AudioSegment.empty()
        self.segments: List[SpeakerChunk] = []
        self.current_position = 0.0  # Current position in seconds
    
    def add_segment(
        self, 
        chunk: SpeakerChunk, 
        original_audio: AudioSegment,
        gap: float = 0.0
    ) -> None:
        """
        Add a segment to this speaker track with optional gap.
        
        Args:
            chunk: Speaker chunk to add
            original_audio: Original audio to extract segment from
            gap: Gap to add before this segment (seconds)
        """
        # Extract segment from original audio
        start_ms = int(chunk.start * 1000)
        end_ms = int(chunk.end * 1000)
        segment_audio = original_audio[start_ms:end_ms]
        
        # Add gap if needed
        if gap > 0 and len(self.audio) > 0:
            gap_ms = int(gap * 1000)
            self.audio += AudioSegment.silent(duration=gap_ms)
            self.current_position += gap
        
        # Add audio and update position
        self.audio += segment_audio
        self.current_position += (chunk.end - chunk.start)
        self.segments.append(chunk)
    
    def export(self, output_path: Path, format: str = "mp3") -> Path:
        """
        Export audio to file.
        
        Args:
            output_path: Path to save audio file
            format: Audio format to use
            
        Returns:
            Path to exported file
        """
        ensure_directory_exists(output_path.parent)
        self.audio.export(output_path, format=format)
        logger.info(f"Exported speaker track for {self.speaker} to {output_path}")
        return output_path


class ConsolidatedResult:
    """Results of speaker audio consolidation."""
    
    def __init__(self):
        """Initialize empty consolidated result."""
        self.speaker_tracks: Dict[str, SpeakerTrack] = {}
    
    def add_track(self, track: SpeakerTrack) -> None:
        """
        Add a speaker track to the results.
        
        Args:
            track: Speaker track to add
        """
        self.speaker_tracks[track.speaker] = track
    
    def export_all(
        self, 
        output_dir: Path, 
        format: str = "mp3"
    ) -> Dict[str, Path]:
        """
        Export all speaker tracks to files.
        
        Args:
            output_dir: Directory to save files
            format: Audio format to use
            
        Returns:
            Dictionary mapping speaker IDs to file paths
        """
        ensure_directory_exists(output_dir)
        
        results = {}
        for speaker, track in self.speaker_tracks.items():
            output_path = output_dir / f"{speaker}.{format}"
            track.export(output_path, format)
            results[speaker] = output_path
        
        return results


class SpeakerAudioConsolidator:
    """Consolidates audio segments by speaker with appropriate gaps."""
    
    def __init__(self, config: Optional[ConsolidatorConfig] = None):
        """
        Initialize consolidator with configuration.
        
        Args:
            config: Configuration options, or None for defaults
        """
        self.config = config or ConsolidatorConfig()
    
    def consolidate(
        self, 
        chunks: List[SpeakerChunk], 
        audio_file: Path
    ) -> ConsolidatedResult:
        """
        Consolidate speaker chunks into continuous audio tracks.
        
        Args:
            chunks: List of speaker chunks to consolidate
            audio_file: Path to original audio file
            
        Returns:
            Consolidated result with speaker tracks
        """
        logger.info(f"Consolidating {len(chunks)} speaker chunks from {audio_file}")
        
        # Load the original audio
        original_audio = AudioSegment.from_file(audio_file)
        
        # Group chunks by speaker
        speaker_chunks = self._group_by_speaker(chunks)
        
        # Create the result container
        result = ConsolidatedResult()
        
        # Process each speaker
        for speaker, speaker_chunks in speaker_chunks.items():
            logger.info(f"Processing {len(speaker_chunks)} chunks for speaker {speaker}")
            track = self._create_speaker_track(speaker, speaker_chunks, original_audio)
            result.add_track(track)
        
        return result
    
    def _group_by_speaker(
        self, 
        chunks: List[SpeakerChunk]
    ) -> Dict[str, List[SpeakerChunk]]:
        """
        Group chunks by speaker.
        
        Args:
            chunks: List of speaker chunks
            
        Returns:
            Dictionary mapping speaker IDs to lists of chunks
        """
        speakers: Dict[str, List[SpeakerChunk]] = {}
        
        for chunk in chunks:
            if chunk.speaker not in speakers:
                speakers[chunk.speaker] = []
            speakers[chunk.speaker].append(chunk)
        
        # Sort each speaker's chunks by start time
        for speaker in speakers:
            speakers[speaker].sort(key=lambda c: c.start)
        
        return speakers
    
    def _create_speaker_track(
        self,
        speaker: str,
        chunks: List[SpeakerChunk],
        original_audio: AudioSegment
    ) -> SpeakerTrack:
        """
        Create a continuous audio track for a speaker.
        
        Args:
            speaker: Speaker identifier
            chunks: List of speaker chunks, sorted by start time
            original_audio: Original audio to extract segments from
            
        Returns:
            Speaker track with consolidated audio
        """
        track = SpeakerTrack(speaker)
        
        for i, chunk in enumerate(chunks):
            # Determine the appropriate gap
            gap = 0.0
            if i > 0:
                prev_chunk = chunks[i-1]
                gap = self._calculate_gap(prev_chunk, chunk)
            
            # Add the segment
            track.add_segment(chunk, original_audio, gap)
        
        logger.info(
            f"Created speaker track for {speaker} with "
            f"{len(chunks)} segments"
        )
        
        return track
    
    def _calculate_gap(
        self, 
        prev_chunk: SpeakerChunk, 
        curr_chunk: SpeakerChunk
    ) -> float:
        """
        Calculate appropriate gap between chunks.
        
        Args:
            prev_chunk: Previous chunk
            curr_chunk: Current chunk
            
        Returns:
            Gap duration in seconds
        """
        # Calculate time between chunks in original audio
        time_diff = curr_chunk.start - prev_chunk.end
        
        # Determine if this is contiguous or not
        # If the chunks are close enough, use contiguous gap
        if time_diff <= self.config.contiguous_gap * 2:
            return self.config.contiguous_gap
        else:
            return self.config.non_contiguous_gap