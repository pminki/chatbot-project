from fastapi import FastAPI, BackgroundTasks, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from models.schemas import ChatRequest, ChatResponse
from services.agent_service import ChatbotAgent
from services.rag_service import RagService
from models.database import SessionLocal, ChatMessage, ChatSession, LearningTutorRecord, Base, engine

# 서버 시작 시 데이터베이스 테이블을 자동으로 생성합니다.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LMS AI Chatbot API")

# CORS 설정 (*.alpaedu.co.kr 및 로컬 테스트 주소 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_origin_regex=r"https?://(.*\.)?alpaedu\.co\.kr",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = ChatbotAgent()

async def log_chat_message(session_id: str, user_id: str, user_msg: str, bot_msg: str, intent: str):
  """
  대화 내역, 세션 정보, 학습 이력을 데이터베이스에 저장합니다.
  """
  db = SessionLocal()
  try:
    # 1. 세션 정보 관리
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
      session = ChatSession(session_id=session_id, user_id=user_id)
      db.add(session)
    
    # 2. 개별 메시지 저장
    db.add(ChatMessage(session_id=session_id, role="USER", content=user_msg))
    db.add(ChatMessage(session_id=session_id, role="ASSISTANT", content=bot_msg))
    
    # 3. 학습 이력 기록 (의도가 TUTOR일 경우)
    if intent == "TUTOR":
      record = db.query(LearningTutorRecord).filter(
        LearningTutorRecord.session_id == session_id
      ).first()
      if not record:
        record = LearningTutorRecord(
          session_id=session_id, 
          user_id=user_id, 
          learning_topic="RAG 지식 학습"
        )
        db.add(record)
      # 세션 요약 업데이트 (임시로 마지막 답변의 일부 저장)
      record.session_summary = bot_msg[:500]
      
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
    # 이제 필요한 모든 정보를 넘겨줍니다.
    background_tasks.add_task(
      log_chat_message, 
      req.session_id, 
      req.user_id, 
      req.message, 
      full_response, 
      intent
    )

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

# ------------------------------------------------------------------------------
# RAG 관리 API
# ------------------------------------------------------------------------------

@app.post("/api/rag/upload")
async def upload_rag_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """새로운 지식 파일을 업로드하고 인덱싱을 시작합니다."""
    db = SessionLocal()
    rag_service = RagService(db)
    try:
        content = await file.read()
        background_tasks.add_task(rag_service.save_and_process_file, file.filename, content)
        return {"message": f"'{file.filename}' 업로드 완료. 백그라운드에서 인덱싱이 시작됩니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.get("/api/rag/files")
async def get_rag_files():
    """모든 RAG 관리 파일 목록을 가져옵니다."""
    db = SessionLocal()
    rag_service = RagService(db)
    try:
        return rag_service.get_all_files()
    finally:
        db.close()

@app.patch("/api/rag/files/{file_id}")
async def toggle_rag_file(file_id: str, is_active: bool):
    """파일의 활성화 상태를 변경합니다."""
    db = SessionLocal()
    rag_service = RagService(db)
    try:
        updated = rag_service.toggle_file_active(file_id, is_active)
        if not updated:
            raise HTTPException(status_code=404, detail="File not found")
        return updated
    finally:
        db.close()

@app.delete("/api/rag/files/{file_id}")
async def delete_rag_file(file_id: str):
    """파일과 관련된 모든 RAG 데이터를 삭제합니다."""
    db = SessionLocal()
    rag_service = RagService(db)
    try:
        rag_service.delete_file(file_id)
        return {"message": "정상적으로 삭제되었습니다."}
    finally:
        db.close()


