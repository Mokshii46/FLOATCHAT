"""
Translation service — USP 2 (with Groq API support + 100% offline fallback).

Translates non-English user queries to English before NL2SQL processing,
and translates the final summary back to the user's language.

Supports: English, Hindi, Tamil, Bengali, Telugu, Kannada, Malayalam.
"""

from __future__ import annotations

from config import settings
from utils.llm_client import complete_prompt
from utils.logger import get_logger

logger = get_logger(__name__)

SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "bn": "Bengali",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
}


def detect_language(text: str) -> str:
    """
    Returns an ISO 639-1 language code for the input text.
    Falls back to Unicode script-range matching when offline.
    """
    # Quick offline Unicode script range check first
    for ch in text:
        code = ord(ch)
        if 0x0900 <= code <= 0x097F:
            return "hi"  # Devanagari / Hindi
        if 0x0B80 <= code <= 0x0BFF:
            return "ta"  # Tamil
        if 0x0980 <= code <= 0x09FF:
            return "bn"  # Bengali
        if 0x0C00 <= code <= 0x0C7F:
            return "te"  # Telugu
        if 0x0C80 <= code <= 0x0CFF:
            return "kn"  # Kannada
        if 0x0D00 <= code <= 0x0D7F:
            return "ml"  # Malayalam

    # LLM language detection if online
    system = "Detect the language of the following text and respond with ONLY the ISO 639-1 two-letter code (e.g. en, hi, ta, bn). No other text."
    res = complete_prompt(system_prompt=system, user_prompt=text, max_tokens=10)
    if res:
        code = res.strip().lower()[:2]
        if code in SUPPORTED_LANGUAGES:
            return code

    return "en"


def translate_to_english(text: str, source_lang: str) -> str:
    """Translate text from source_lang to English."""
    if source_lang == "en":
        return text

    lang_name = SUPPORTED_LANGUAGES.get(source_lang, source_lang)
    system = f"Translate the following {lang_name} text to English. Output only the translation."
    res = complete_prompt(system_prompt=system, user_prompt=text, max_tokens=512)
    return res.strip() if res else text


def translate_from_english(text: str, target_lang: str) -> str:
    """Translate text from English to target_lang."""
    if target_lang == "en":
        return text

    lang_name = SUPPORTED_LANGUAGES.get(target_lang, target_lang)
    system = f"Translate the following English text to {lang_name}. Output only the translation."
    res = complete_prompt(system_prompt=system, user_prompt=text, max_tokens=1024)
    return res.strip() if res else text
