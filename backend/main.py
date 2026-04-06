from fastapi import FastAPI, BackgroundTasks, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from models.schemas import ChatRequest, ChatResponse
from services.agent_service import ChatbotAgent
from services.rag_service import RagService
from models.database import SessionLocal, ChatMessage, ChatSession, LearningTutorRecord, Base, engine

# [1. 데이터베이스 초기화]
# 서버가 시작될 때, 미리 정의한 데이터베이스 Table들이 없으면 자동으로 생성해줍니다.
Base.metadata.create_all(bind=engine)

# [2. FastAPI 앱 설정]
# 프로젝트의 메인 '앱' 객체를 생성합니다.
app = FastAPI(title="LMS AI Chatbot API")

# [3. CORS(Cross-Origin Resource Sharing) 설정]
# 보안상의 이유로 브라우저는 다른 주소(도메인)의 서버에 데이터를 요청하는 것을 막습니다.
# 프론트엔드(React)가 백엔드(Python)와 자유롭게 통신할 수 있도록 허용하는 목록을 작성합니다.
# CORS 설정 (*.alpaedu.co.kr 및 로컬 테스트 주소 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], # 내 컴퓨터 테스트용
    allow_origin_regex=r"https?://(.*\.)?alpaedu\.co\.kr|https://.*\.ngrok-free\.app|https://.*\.ngrok\.io", # 실제 서비스 주소 + ngrok 터널 주소
    allow_credentials=True, # 쿠키 등 인증 정보 허용
    allow_methods=["*"], # 모든 HTTP 메소드(GET, POST, PUT, DELETE 등) 허용
    allow_headers=["*"], # 모든 HTTP 헤더 허용
)

# AI 답변을 생성해주는 핵심 '에이전트' 객체를 미리 만들어둡니다.
agent = ChatbotAgent()

# [4. 백그라운드 작업: 대화 로그 저장]
# 답변이 이미 유저에게 전달된 '뒤에' 천천히 데이터베이스에 저장해도 되는 작업들을 처리합니다.
# 이렇게 하면 사용자는 저장될 때까지 기다릴 필요가 없어 속도가 빠릅니다.
async def log_chat_message(session_id: str, user_id: str, user_msg: str, bot_msg: str, intent: str):
  """
  대화 내역, 세션 정보, 학습 이력을 데이터베이스에 저장하는 함수입니다.
  """
  db = SessionLocal()
  try:
    # 1. 세션 정보 관리: 이 대화가 처음인지 확인하고 정보를 등록합니다.
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
      session = ChatSession(session_id=session_id, user_id=user_id)
      db.add(session)
      db.flush() # 세션을 먼저 DB에 반영하여 외래키 제약조건 위반 방지
      print(f"--- [DEBUG] New ChatSession created: {session_id}")
    
    # 2. 메시지 저장: 유저가 보낸 말과 AI가 대답한 말을 각각 저장합니다.
    db.add(ChatMessage(session_id=session_id, role="USER", content=user_msg))
    db.add(ChatMessage(session_id=session_id, role="ASSISTANT", content=bot_msg))
    
    # 3. 학습 이력 기록: 질문이 '학습'과 관련이 있다면 별도의 이력 카드에 기록합니다.
    # (의도가 TUTOR일 경우)
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
      # 세션 요약 업데이트 (임시로 마지막 답변의 일부 저장) - 답변 요약본 보관
      record.session_summary = bot_msg[:500]

    # 실제 DB에 최종 반영  
    db.commit()
  except Exception as e:
    # 오류 발생 시 작업을 되돌립니다.
    db.rollback()
    print(f"로그 저장 실패: {e}")
  finally:
    # DB 연결 종료
    db.close()

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest, background_tasks: BackgroundTasks):
  """
  사용자의 질문에 대해 실시간 스트리밍(SSE) 방식으로 응답합니다.
  """
  
  # AI 답변이 모두 끝난 뒤에 실행할 콜백 함수입니다.
  #  스트리밍이 완료된 후 실행할 작업(DB 저장)을 정의합니다.
  async def on_complete(full_response: str, intent: str):
    # 이제 필요한 모든 정보를 넘겨줍니다. (DB 저장을 백그라운드 작업으로 등록)
    background_tasks.add_task(
      log_chat_message, 
      req.session_id, 
      req.user_id, 
      req.message, 
      full_response, 
      intent
    )

  # StreamingResponse를 통해 한 글자씩 프론트엔드로 전달합니다.
  # 생성되는 글자 조각들을 프론트엔드로 즉시즉시 보내주는 방식입니다.
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
# [6. RAG 관리 API: 지식 문서 관리 도구]
# ------------------------------------------------------------------------------

@app.post("/api/rag/upload")
async def upload_rag_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """PDF나 TXT 파일을 업로드하고, 내부 내용을 조각내어 검색 데이터베이스(Vector DB)에 저장합니다."""
    db = SessionLocal()
    rag_service = RagService(db)
    try:
        # [수정] 1. 파일을 먼저 동기적으로 저장합니다. (파일 핸들 소멸 방지)
        # 이 과정에서 DB에 'PROCESSING' 상태로 초기 레코드가 생성됩니다.
        file_info = rag_service.save_file_sync(file)
        
        # [수정] 2. 실제 분석(인덱싱) 작업만 백그라운드로 넘깁니다. 
        # 이때 별도의 DB 세션을 사용하도록 설계된 static method를 호출합니다.
        background_tasks.add_task(
            RagService.process_indexing_task, 
            file_info["file_id"], 
            file_info["save_path"], 
            file_info["file_name"]
        )
        
        return {"message": f"'{file.filename}' 업로드 요청을 완료했습니다. 백그라운드에서 분석이 시작됩니다."}
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


