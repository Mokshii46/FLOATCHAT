"""
Unified LLM Client supporting Groq, Anthropic, and 100% Offline fallback.
"""

from __future__ import annotations

import httpx
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def _get_api_key() -> tuple[str, str]:
    """
    Returns (provider, api_key).
    Provider: 'groq' | 'anthropic' | 'none'
    """
    g_key = settings.groq_api_key or (settings.llm_api_key if settings.llm_api_key.startswith("gsk_") else "")
    a_key = settings.llm_api_key if settings.llm_api_key.startswith("sk-ant") else ""

    if g_key:
        return "groq", g_key
    if a_key:
        return "anthropic", a_key
    if settings.llm_api_key and not settings.llm_api_key.startswith("your_"):
        # Assume groq if provider is groq, else anthropic
        if settings.llm_provider.lower() == "groq":
            return "groq", settings.llm_api_key
        return "anthropic", settings.llm_api_key

    return "none", ""


def complete_prompt(system_prompt: str, user_prompt: str, max_tokens: int = 1024) -> str | None:
    """
    Sends a prompt to the configured LLM (Groq or Anthropic).
    Returns the string response, or None if no API key or call fails (triggering offline mode).
    """
    provider, api_key = _get_api_key()
    if provider == "none" or not api_key:
        logger.info("No LLM API key configured — using 100%% offline mode.")
        return None

    if provider == "groq":
        return _call_groq(system_prompt, user_prompt, api_key, max_tokens)
    elif provider == "anthropic":
        return _call_anthropic(system_prompt, user_prompt, api_key, max_tokens)

    return None


def _call_groq(system_prompt: str, user_prompt: str, api_key: str, max_tokens: int) -> str | None:
    """Call Groq API using HTTPX (zero extra heavy dependencies required)."""
    model = settings.llm_model if settings.llm_model.startswith("llama") or "/" in settings.llm_model or "mixtral" in settings.llm_model else "llama-3.3-70b-versatile"
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.1,
    }

    try:
        logger.debug("Calling Groq API model=%s ...", model)
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            return content
    except Exception as exc:
        logger.warning("Groq API call failed: %s. Falling back to offline mode.", exc)
        return None


def _call_anthropic(system_prompt: str, user_prompt: str, api_key: str, max_tokens: int) -> str | None:
    """Call Anthropic API."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        model = settings.llm_model if "claude" in settings.llm_model else "claude-3-5-sonnet-20241022"
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        if response.content:
            return response.content[0].text.strip()
    except Exception as exc:
        logger.warning("Anthropic API call failed: %s. Falling back to offline mode.", exc)
    return None
