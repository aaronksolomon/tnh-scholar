# audio_models.py

from io import BytesIO
from typing import Optional

from pydantic import BaseModel


class AudioChunk(BaseModel):
    data: BytesIO
    start_ms: int
    end_ms: int
    sample_rate: int = 16000
    channels: int = 1
    format: Optional[str] = None