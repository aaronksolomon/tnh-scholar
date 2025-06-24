from pydantic_settings import BaseSettings


class ChunkerConfig(BaseSettings):
    """Simple configuration for audio chunking algorithm."""
    
    # Target duration for each chunk in milliseconds (default: 5 minutes = 300,000ms)
    target_time: int = 300_000

    # Minimum duration for final chunk (in ms); shorter chunks are merged
    min_chunk_time: int = 30_000 # 30 seconds
    
    # If set to true, all speakers are set to default speaker label
    single_speaker: bool = False
    
    # Maximum allowed gap between segments for audio processing
    gap_threshold: int = 4000
    
    # Spacing used between segments that are greater than gap threshold ms apart
    gap_spacing_time: int = 1000 
    
    default_speaker_label: str = "SPEAKER_00"