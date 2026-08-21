"""
Voice service — USP 4.

STT: Whisper (local) or a hosted API (configurable via settings.stt_provider).
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
    audio_bytes  : raw audio data (WebM from browser MediaRecorder, or WAV)
    audio_format : "webm" | "wav" | "mp3"

    Returns
    -------
    Transcribed text string.
    """
    provider = settings.stt_provider.lower()

    if provider == "whisper":
        return _whisper_transcribe(audio_bytes, audio_format)
    else:
        raise NotImplementedError(f"STT provider '{provider}' not supported.")


def _whisper_transcribe(audio_bytes: bytes, audio_format: str) -> str:
    try:
        import whisper  # type: ignore

        with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        model = whisper.load_model("base")
        result = model.transcribe(tmp_path)
        Path(tmp_path).unlink(missing_ok=True)
        text = result.get("text", "").strip()
        logger.info("Whisper transcribed: %s", text[:80])
        return text
    except ImportError:
        logger.warning("Whisper not installed — returning empty transcription.")
        return ""
    except Exception as exc:
        logger.error("Whisper transcription failed: %s", exc)
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
