from pydantic import BaseModel, Field
from typing import Literal

class ChatRequest(BaseModel):
    session_id: str
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    intent: str

class IntentClassification(BaseModel):
    intent: Literal["TUTOR", "CS"] = Field(description="학습 보조(TUTOR) 또는 시스템오류/고객지원(CS)")
    reason: str = Field(description="분류 이유")