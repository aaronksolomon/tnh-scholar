# audio_models.py

from io import BytesIO
from typing import Optional

from pydantic import BaseModel


class AudioChunk(BaseModel):
    data: BytesIO
    start_ms: int
    end_ms: int
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    format: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True