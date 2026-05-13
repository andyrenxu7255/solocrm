from pathlib import Path

import requests

from app.config import get_settings


class SpeechTranscriptionError(RuntimeError):
    pass


def transcribe_audio(file_path: str | Path) -> dict:
    settings = get_settings()
    if not settings.asr_api_key:
        raise SpeechTranscriptionError("ASR_API_KEY is not configured")

    audio_path = Path(file_path)
    if not audio_path.exists():
        raise SpeechTranscriptionError(f"Audio file not found: {audio_path}")

    with audio_path.open("rb") as audio_file:
        response = requests.post(
            settings.asr_api_base,
            headers={"Authorization": f"Bearer {settings.asr_api_key}"},
            files={"file": (audio_path.name, audio_file)},
            data={"model": settings.asr_model},
            timeout=300,
        )

    if not response.ok:
        raise SpeechTranscriptionError(
            f"ASR request failed with {response.status_code}: {response.text}"
        )

    return response.json()
