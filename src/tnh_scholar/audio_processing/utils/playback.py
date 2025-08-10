# tnh_scholar/audio_processing/utils/playback.py


from io import BytesIO
from pathlib import Path

from pydub.playback import play

from tnh_scholar.audio_processing.diarization.models import DiarizedSegment
from tnh_scholar.utils import TNHAudioSegment as AudioSegment


def play_diarization_segment(segment: DiarizedSegment, audio: AudioSegment):
    play_audio_segment(audio[segment.start:segment.end]) 
    
def get_segment_audio(segment: DiarizedSegment, audio: AudioSegment):
    return audio[segment.start:segment.end]

def play_audio_segment(audio: AudioSegment):
    play(audio)

def get_audio_from_file(audio_file: Path) -> AudioSegment:
    audio_format_ext = audio_file.suffix.lstrip(".").lower()
    return AudioSegment.from_file(audio_file, format=audio_format_ext)

def play_from_file(path: Path):
    audio = AudioSegment.from_file(path)
    play(audio)

def play_bytes(data: BytesIO, format: str = "wav"):
    audio = AudioSegment.from_file(data, format=format)
    play(audio)
    
