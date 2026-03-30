from pydantic import BaseModel, Field
from typing import Literal

# [클래스: ChatRequest] 
# 사용자가 프론트엔드에서 백엔드 API로 "말을 걸 때" 사용하는 데이터 규격입니다.
class ChatRequest(BaseModel):
  session_id: str # 대화의 흐름을 추적하기 위한 고유한 방 번호와 같습니다.
  user_id: str    # 어느 학생이 말하고 있는지 확인하는 고유 ID입니다.
  message: str    # 실제로 사용자가 보낸 질문 내용입니다.

# [클래스: ChatResponse]
# 백엔드가 프론트엔드로 "대답을 줄 때" 이 형식을 맞춰서 보내줍니다.
class ChatResponse(BaseModel):
  response: str   # AI가 생성해낸 친절한 답변 메시지입니다.
  intent: str     # AI가 판단한 사용자의 질문 의도(TUTOR 또는 CS)입니다.

# [클래스: IntentClassification]
# AI가 사용자의 의도를 분석한 뒤, 결과값을 정해진 형식으로 내놓도록 강제하는 도구입니다.
class IntentClassification(BaseModel):
  # 'Literal'은 정해진 글자들 중에서만 골라야 한다는 뜻입니다.
  intent: Literal["TUTOR", "CS"] = Field(description="학습 보조(TUTOR) 또는 시스템오류/고객지원(CS)")
  
  # AI가 왜 그렇게 분류했는지 '이유'를 함께 적도록 하여 답변의 신뢰도를 높입니다.
  reason: str = Field(description="결정적인 분류 이유")
