from pydantic import BaseModel, Field
from typing import Literal


class TTSRequest(BaseModel):
    text: str = Field(..., description="Input text to synthesize")
    speed: Literal["normal", "fast", "slow", "very_fast"] = Field(
        "normal", description="Speech speed"
    )


class TTSResponse(BaseModel):
    hash: str
    text: str
    speed: str
    audio_url: str