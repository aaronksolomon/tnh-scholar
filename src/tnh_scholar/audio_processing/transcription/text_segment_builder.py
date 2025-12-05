"""
SegmentBuilder for creating phrase-level segments from word-level TimedText.

This module builds higher-level segments from a TimedText object containing 
word-level units, based on configurable criteria like duration, character count, 
punctuation, pauses, and speaker changes.
"""
from typing import List, Optional

from ..timed_object.timed_text import Granularity, TimedText, TimedTextUnit

COMMON_ABBREVIATIONS = frozenset({
    "adj.", "adm.", "adv.", "al.", "anon.", "apr.", "arc.", "aug.", "ave.",
    "brig.", "bros.", "capt.", "cmdr.", "col.", "comdr.", "con.", "corp.",
    "cpl.", "dr.", "drs.", "ed.", "enc.", "etc.", "ex.", "feb.", "gen.",
    "gov.", "hon.", "hosp.", "hr.", "inc.", "jan.", "jr.", "maj.", "mar.",
    "messrs.", "mlle.", "mm.", "mme.", "mr.", "mrs.", "ms.", "msgr.", "nov.",
    "oct.", "op.", "ord.", "ph.d.", "prof.", "pvt.", "rep.", "reps.", "res.",
    "rev.", "rt.", "sen.", "sens.", "sep.", "sfc.", "sgt.", "sr.", "st.", "supt.",
    "surg.", "u.s.", "v.p.", "vs."
})

class TextSegmentBuilder:
    def __init__(
        self,
        *,
        max_duration_ms: Optional[int] = None, # milliseconds
        target_characters: Optional[int] = None,
        avoid_orphans: bool = True,
        max_gap_duration_ms: Optional[int] = None, # milliseconds
        ignore_speaker: bool = True,
    ):
        self.max_duration = max_duration_ms
        self.target_characters = target_characters
        self.avoid_orphans = avoid_orphans
        self.max_gap_duration = max_gap_duration_ms
        self.ignore_speaker = ignore_speaker

        self.segments: List[TimedTextUnit] = []
        self.current_words: List[TimedTextUnit] = []
        self.current_characters = 0

    def create_segments(self, timed_text: TimedText) -> TimedText:
        # Validate
        if not timed_text.words:
            raise ValueError(
                "TimedText object must have word-level units to build segments."
                )

        for unit in timed_text.words:
            if unit.granularity != Granularity.WORD:
                raise ValueError(f"Expected WORD units, got {unit.granularity}")

        # Process
        for word in timed_text.words:
            if self._should_start_new_segment(word):
                self._flush_current_words()
            self._add_word(word)

        self._flush_current_words()  # Final flush
        return TimedText(segments=self.segments, granularity=Granularity.SEGMENT)
    
    def _add_word(self, word: TimedTextUnit):
        if self.current_words:
            self.current_characters += 1  # space before the new word
        self.current_characters += len(word.text)
        self.current_words.append(word)
        

    def _should_start_new_segment(self, word: TimedTextUnit) -> bool:
        if not self.current_words:
            return False

        # Speaker change
        last_word = self.current_words[-1]
        if not self.ignore_speaker and (word.speaker != last_word.speaker):
            return True

        # Significant pause
        if self.max_gap_duration is not None:
            pause = word.start_ms - last_word.end_ms
            if pause > self.max_gap_duration:
                return True

        # End punctuation
        if last_word.text and self._is_punctuation_word(last_word.text):
            return True

        # Max duration
        if self.max_duration is not None:
            duration = word.end_ms - self.current_words[0].start_ms
            if duration > self.max_duration:
                return True

        # Target character count
        if self.target_characters is not None:
            total_chars = self.current_characters + len(word.text) + 1
            if total_chars > self.target_characters:
                return True

        return False

    def _flush_current_words(self):
        if not self.current_words:
            return

        segment_text = " ".join(word.text for word in self.current_words)
        segment = TimedTextUnit(
            text=segment_text,
            start_ms=self.current_words[0].start_ms,
            end_ms=self.current_words[-1].end_ms,
            granularity=Granularity.SEGMENT,
            speaker=None if self.ignore_speaker else self._find_speaker(),
            confidence=None,
            index=None,
        )
        self.segments.append(segment)
        self.current_words = []
        self.current_characters = 0
        
    def _find_speaker(self) -> Optional[str]:
        """
        Only called when ignore_speakers is False; 
        in this case we always split on speaker. 
        So only one speaker is expected. 
        """
        speakers = {word.speaker for word in self.current_words}
        assert len(speakers) == 1, "Inconsistent speakers in segment"
        return speakers.pop()

    def _is_punctuation_word(self, word_text: str) -> bool:
        """
        Check if a word ending in punctuation should trigger a new segment,
        excluding common abbreviations.
        """
        if not word_text:
            return False
        return word_text[-1] in ".!?" and word_text.lower() not in COMMON_ABBREVIATIONS
    
    
    def build_segments(
        self,
        *,
        target_duration: Optional[int] = None,
        target_characters: Optional[int] = None,
        avoid_orphans: Optional[bool] = True,
        max_gap_duration: Optional[int] = None,
        ignore_speaker: bool = False,
    ) -> None:
        """
        Build or rebuild `segments` from the contents of `words`.

        Args:
            target_duration: Maximum desired segment duration in milliseconds.
            target_characters: Maximum desired character length of a segment.
            avoid_orphans: If True, prevent extremely short trailing segments.

        Note:
            This is a stub.  Concrete algorithms will be implemented later.

        Raises:
            NotImplementedError: Always, until implemented.
        """
        raise NotImplementedError("build_segments is not yet implemented.")
