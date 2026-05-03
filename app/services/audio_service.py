import os
import tempfile
import requests

from fastapi import HTTPException


def get_audio_suffix(audio_url: str, content_type: str) -> str:
    audio_url = audio_url.lower()

    if "mpeg" in content_type or audio_url.endswith(".mp3"):
        return ".mp3"
    if "wav" in content_type or audio_url.endswith(".wav"):
        return ".wav"
    if "ogg" in content_type or audio_url.endswith(".ogg"):
        return ".ogg"
    if "webm" in content_type or audio_url.endswith(".webm"):
        return ".webm"
    if "m4a" in content_type or audio_url.endswith(".m4a"):
        return ".m4a"

    return ".wav"


def download_audio(audio_url: str) -> str:
    try:
        response = requests.get(audio_url, timeout=60)
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to download audio: {str(e)}"
        )

    content_type = response.headers.get("content-type", "")
    suffix = get_audio_suffix(audio_url, content_type)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_file.write(response.content)
    temp_file.close()

    return temp_file.name


def remove_temp_file(file_path: str | None):
    if file_path and os.path.exists(file_path):
        os.remove(file_path)