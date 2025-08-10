from typing import Dict, List

from tnh_scholar.utils import TimeMs

from .config import DiarizationConfig
from .models import DiarizedSegment
from .protocols import SegmentAdapter
from .types import PyannoteEntry


class PyannoteAdapter(SegmentAdapter):
    def __init__(self, config: DiarizationConfig = DiarizationConfig()):
        self.config = config
    
    def to_segments(
        self, 
        data: Dict[str, List['PyannoteEntry']]
        ) -> List[DiarizedSegment]:
        """
        Convert a pyannoteai diarization result dict to list of DiarizationSegment objects.

        Args:
            pyannote_data: Dictionary containing diarization results.
                Expected format:                    : 
                            {
                                'diarization': [
                                    {"speaker": str, "start": float (seconds), "end": float (seconds)},
                                    ...
                                ]
                            }


        Returns:
            List of DiarizationSegment objects with times converted to milliseconds.
        """

        default_speaker = self.config.speaker.default_speaker_label
        single_speaker = self.config.speaker.single_speaker

        segments = []

        
        data_entries: List[PyannoteEntry] = data.get('diarization', [])
        for entry in data_entries:
            self._entry_validate(entry)
            segment = DiarizedSegment(
                speaker=default_speaker if single_speaker else entry['speaker'],
                start=TimeMs.from_seconds(entry['start']),
                end=TimeMs.from_seconds(entry['end']),
                audio_map_start=None,
                gap_before=None,
                spacing_time=None,
            )
            segments.append(segment)

        return self._sort_and_normalize_segments(segments)

    def _entry_validate(self, entry: PyannoteEntry):
        for key in ('start', 'end', 'speaker'):
            if key not in entry:
                raise KeyError(f"Entry {entry} missing required key '{key}'.")
        if not isinstance(entry['start'], (int, float)):
            raise TypeError(f"Entry 'start' expected to be int or float. Got {type(entry['start'])}")
        if not isinstance(entry['end'], (int, float)):
            raise TypeError(f"Entry 'end' expected to be int or float. Got {type(entry['end'])}")
        if not isinstance(entry['speaker'], str):
            raise TypeError(f"Entry 'speaker' expected to be str. Got {type(entry['speaker'])}")
        
    def _sort_and_normalize_segments(
        self, segments: List[DiarizedSegment]
        ) -> List[DiarizedSegment]:
        """
        Validate and normalize segments by sorting and ensuring nonzero duration.
        ** Sort modifies Segment list in place **
        
        Args:
            segments: List of diarization segments
            
        Returns:
            List of sorted and normalized segments
        """
        self._sort_by_start(segments)
        for segment in segments:
            segment.normalize()
        return segments
    
    def _sort_by_start(self, segments: List[DiarizedSegment]) -> None:
        """Sort segments by start time."""
        segments.sort(key=lambda segment: segment.start)