from datetime import datetime

from pydantic import BaseModel, Field

from .common import ORMModel


class AuditActor(ORMModel):
    id: int
    email: str


class AuditLogOut(ORMModel):
    id: int
    action: str
    detail: str
    created_at: datetime
    actor: AuditActor | None


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)


class AskResponse(BaseModel):
    answer: str
    source: str
