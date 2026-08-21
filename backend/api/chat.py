"""
POST /chat — main conversational endpoint.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    mode: str | None = Field(None, pattern="^(citizen|researcher)$")
    language: str | None = Field(None, max_length=5)
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    viz: dict[str, Any] | None
    anomaly: dict[str, Any] | None
    explainability: dict[str, Any] | None
    mode_config: dict[str, Any]
    language: str
    row_count: int


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    from services.chat_service import process_chat

    result = process_chat(
        question=req.question,
        mode=req.mode,
        language=req.language,
    )
    return ChatResponse(**result)
