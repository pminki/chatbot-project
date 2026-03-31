from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from models.schemas import ChatRequest, ChatResponse
from services.agent_service import ChatbotAgent
from models.database import SessionLocal, ChatMessage

app = FastAPI(title="LMS AI Chatbot API")

# CORS 설정 (*.alpaedu.co.kr 서브도메인 접속 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(.*\.)?alpaedu\.co\.kr",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



agent = ChatbotAgent()

async def log_chat_message(session_id: str, user_msg: str, bot_msg: str):
  """
  대화 내역을 비동기적으로 데이터베이스에 저장합니다.
  """
  db = SessionLocal()
  try:
    db.add(ChatMessage(session_id=session_id, role="USER", content=user_msg))
    db.add(ChatMessage(session_id=session_id, role="ASSISTANT", content=bot_msg))
    db.commit()
  except Exception as e:
    db.rollback()
    print(f"로그 저장 실패: {e}")
  finally:
    db.close()

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest, background_tasks: BackgroundTasks):
  """
  사용자의 질문에 대해 실시간 스트리밍(SSE) 방식으로 응답합니다.
  """
  
  # 스트리밍이 완료된 후 실행할 작업(DB 저장)을 정의합니다.
  async def on_complete(full_response: str, intent: str):
    # 답변이 완료되면 백그라운드에서 로그를 저장하도록 예약합니다.
    background_tasks.add_task(log_chat_message, req.session_id, req.message, full_response)

  # StreamingResponse를 통해 한 글자씩 프론트엔드로 전달합니다.
  return StreamingResponse(
    agent.achat_stream(
      session_id=req.session_id,
      user_id=req.user_id,
      message=req.message,
      on_complete=on_complete
    ),
    media_type="text/event-stream"
  )

