from typing import Annotated

from fastapi import APIRouter, Depends

from ...ai.llm import LLM, get_llm
from ...schemas.ai import ChatRequest, ChatResponse, LeaveDraftRequest, LeaveDraftResponse, SummaryResponse
from ...services import ai as ai_service
from ..deps import CurrentUser, Db, ManagerUser

router = APIRouter(prefix="/ai", tags=["ai"])

Llm = Annotated[LLM | None, Depends(get_llm)]


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Db, llm: Llm, user: CurrentUser):
    return ai_service.chat(db, llm, user, payload.message, payload.history)


@router.post("/summary", response_model=SummaryResponse)
def summarize_dashboard(db: Db, llm: Llm, user: ManagerUser):
    return ai_service.summarize_dashboard(db, llm, user)


@router.post("/leave-draft", response_model=LeaveDraftResponse)
def draft_leave(payload: LeaveDraftRequest, db: Db, llm: Llm, user: CurrentUser):
    return ai_service.draft_leave(db, llm, user, payload.text)
