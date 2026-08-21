"""
POST /voice/transcribe — upload audio, get text back
POST /voice/speak      — send text, get base64 MP3 back
"""

from __future__ import annotations

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel

router = APIRouter()


class TranscribeResponse(BaseModel):
    text: str


class SpeakRequest(BaseModel):
    text: str
    lang: str = "en"


class SpeakResponse(BaseModel):
    audio_base64: str   # base64-encoded MP3


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    audio: UploadFile = File(..., description="Audio file (webm/wav/mp3)"),
):
    from services.voice_service import transcribe as stt_transcribe

    content = await audio.read()
    suffix = audio.filename.rsplit(".", 1)[-1] if audio.filename else "webm"
    try:
        text = stt_transcribe(content, audio_format=suffix)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return TranscribeResponse(text=text)


@router.post("/speak", response_model=SpeakResponse)
def speak(req: SpeakRequest):
    from services.voice_service import speak as tts_speak

    try:
        audio_b64 = tts_speak(req.text, lang=req.lang)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return SpeakResponse(audio_base64=audio_b64)
