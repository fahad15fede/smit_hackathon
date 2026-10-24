from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    text: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=500)
    history: list[ChatTurn] = Field(default_factory=list, max_length=10)


class ChatResponse(BaseModel):
    answer: str
    ai_generated: bool
    # "ai": written by the model; "quick_reply": small talk/help/navigation answered locally;
    # "fallback": the model was unavailable.
    source: Literal["ai", "quick_reply", "fallback"]
    tools_used: list[str] = []


class SummaryResponse(BaseModel):
    bullets: list[str]
    ai_generated: bool
    message: str | None = None


class LeaveDraftRequest(BaseModel):
    text: str = Field(min_length=3, max_length=300)


class LeaveDraft(BaseModel):
    leave_type_id: int
    leave_type_name: str
    start_date: date
    end_date: date
    reason: str


class LeaveDraftResponse(BaseModel):
    draft: LeaveDraft | None
    ai_generated: bool
    message: str | None = None
