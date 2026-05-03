from typing import Optional
from pydantic import BaseModel


class AudioUrlRequest(BaseModel):
    audio_url: str
    max_new_tokens: Optional[int] = None


class JobSubmitResponse(BaseModel):
    success: bool
    job_id: str
    status: str
    message: str
    queue_size: int


class JobStatusResponse(BaseModel):
    success: bool
    job_id: str
    status: str
    queue_size: int
    error: Optional[str] = None


class JobResultResponse(BaseModel):
    success: bool
    job_id: str
    status: str
    result: Optional[str] = None
    error: Optional[str] = None