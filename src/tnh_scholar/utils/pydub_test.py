from .tnh_audio_segment import TNHAudioSegment as AudioSegment

a = AudioSegment.silent(duration=1000)
start = 50
end = 100
length = len(a)

assembled = AudioSegment.empty()
interval_audio = a[start:end]
assembled = assembled + interval_audio
offset = 0 + len(interval_audio)