"""
Voice service — USP 4.

STT: Groq Whisper API (fast cloud STT) or local Whisper model.
TTS: gTTS (text-to-speech, returns audio bytes as base64).
"""

from __future__ import annotations

import base64
import io
import tempfile
from pathlib import Path

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


# ── Speech-to-Text ────────────────────────────────────────────────

def transcribe(audio_bytes: bytes, audio_format: str = "webm") -> str:
    """
    Transcribe audio bytes to text.

    Parameters
    ----------
    audio_bytes  : raw audio data (WebM, WAV, MP3, MP4, OGG)
    audio_format : "webm" | "wav" | "mp3" | "mp4" | "m4a" | "ogg"

    Returns
    -------
    Transcribed text string.
    """
    api_key = settings.groq_api_key or settings.llm_api_key
    if api_key:
        try:
            text = _groq_transcribe(audio_bytes, audio_format, api_key)
            if text:
                return text
        except Exception as exc:
            logger.warning("Groq STT failed, falling back to local whisper: %s", exc)

    return _whisper_transcribe(audio_bytes, audio_format)


def _groq_transcribe(audio_bytes: bytes, audio_format: str, api_key: str) -> str:
    """Use Groq API (whisper-large-v3-turbo) for ultra-fast audio transcription."""
    import httpx

    mime_map = {
        "webm": "audio/webm",
        "mp4": "audio/mp4",
        "m4a": "audio/m4a",
        "wav": "audio/wav",
        "mp3": "audio/mp3",
        "ogg": "audio/ogg",
    }
    fmt = audio_format.lower().strip()
    mime_type = mime_map.get(fmt, "audio/webm")
    filename = f"recording.{fmt}"

    headers = {"Authorization": f"Bearer {api_key}"}
    files = {"file": (filename, audio_bytes, mime_type)}
    data = {"model": "whisper-large-v3-turbo"}

    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            headers=headers,
            files=files,
            data=data,
        )
        if resp.status_code == 200:
            result = resp.json()
            text = result.get("text", "").strip()
            logger.info("Groq STT transcribed: %s", text[:80])
            return text
        else:
            logger.error("Groq STT returned status %d: %s", resp.status_code, resp.text)
            raise RuntimeError(f"Groq STT error: status {resp.status_code}")


def _whisper_transcribe(audio_bytes: bytes, audio_format: str) -> str:
    """Fallback to local whisper python package if installed."""
    try:
        import whisper  # type: ignore

        fmt = audio_format.lower().strip()
        with tempfile.NamedTemporaryFile(suffix=f".{fmt}", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        model = whisper.load_model("base")
        result = model.transcribe(tmp_path)
        Path(tmp_path).unlink(missing_ok=True)
        text = result.get("text", "").strip()
        logger.info("Local Whisper transcribed: %s", text[:80])
        return text
    except ImportError:
        logger.warning("Whisper not installed and Groq STT unavailable — returning empty transcription.")
        return ""
    except Exception as exc:
        logger.error("Local Whisper transcription failed: %s", exc)
        return ""


# ── Text-to-Speech ────────────────────────────────────────────────

def speak(text: str, lang: str = "en") -> str:
    """
    Convert text to speech and return base64-encoded MP3 bytes.

    Returns empty string if TTS is disabled.
    """
    provider = settings.tts_provider.lower()
    if provider == "none":
        return ""

    if provider == "gtts":
        return _gtts_speak(text, lang)

    raise NotImplementedError(f"TTS provider '{provider}' not supported.")


def _gtts_speak(text: str, lang: str = "en") -> str:
    """Use gTTS to synthesise speech. Returns base64-encoded MP3."""
    try:
        from gtts import gTTS  # type: ignore

        buf = io.BytesIO()
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.write_to_fp(buf)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")
    except ImportError:
        logger.warning("gTTS not installed — TTS disabled.")
        return ""
    except Exception as exc:
        logger.error("gTTS failed: %s", exc)
        return ""
