from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.schemas import ChatRequest, ChatResponse
from services.agent_service import ChatbotAgent
from models.database import SessionLocal, ChatMessage # [수정] 데이터베이스 세션과 메시지 모델 임포트 추가

# 1. FastAPI 애플리케이션 객체 생성 (API의 전체 관리자 역할)
app = FastAPI(title="LMS AI Chatbot API")

# 2. CORS(Cross-Origin Resource Sharing) 설정
# 다른 도메인(예: React 프론트엔드)에서 이 API에 안전하게 접근할 수 있도록 허용합니다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 모든 도메인에서의 접근을 허용 (실제 서비스에서는 보안을 위해 도메인 제한 필요)
    allow_credentials=True,
    allow_methods=["*"], # GET, POST 등 모든 방식의 요청 허용
    allow_headers=["*"], # 모든 헤더 정보 허용
)

# 3. 챗봇의 핵심 두뇌 역할을 하는 에이전트 객체 생성
agent = ChatbotAgent()

# 4. 채팅 엔드포인트 정의 (사용자의 요청이 들어오는 길목)
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
  """
  사용자가 보낸 메시지를 처리하고 AI의 답변을 반환하는 메인 함수입니다.
  """
  
  # [진행 단계 1] LangGraph 에이전트를 호출하여 분석 및 답변 생성
  # 사용자의 ID, 세션 ID 성격에 맞춰 맞춤형 대화를 수행합니다.
  result = agent.chat(
    session_id=req.session_id,
    user_id=req.user_id,
    message=req.message
  )

  # [진행 단계 2] 대화 내용을 데이터베이스(DB)에 기록 (메시지 로깅)
  # (참고: 실제 운영 환경에서는 응답 속도 향상을 위해 이 부분을 비동기 백그라운드로 처리하는 것이 좋습니다.)
  db = SessionLocal() # DB 연결 세션 생성
  try:
    # 사용자(USER) 발화 내용 저장
    db.add(ChatMessage(
        session_id=req.session_id, 
        role="USER", 
        content=req.message
    ))
    # AI(ASSISTANT) 응답 내용 저장
    db.add(ChatMessage(
        session_id=req.session_id, 
        role="ASSISTANT", 
        content=result["response"]
    ))
    # 모든 변경 사항을 DB에 최종 반영(저장)
    db.commit()
  except Exception as e:
    # 데이터 저장 중 오류 발생 시, 중단된 작업을 취소하고 원래대로 되돌립니다.
    db.rollback()
    print(f"채팅 로그 저장 중 오류 발생: {e}")
  finally:
    # 작업이 끝나면 반드시 DB 연결 통로를 닫아줍니다. (메모리 누수 방지)
    db.close()

  # [진행 단계 3] 프론트엔드(FE)로 최종 답변과 분석된 의도 전달
  return ChatResponse(
    response=result["response"],
    intent=result["intent"]
  )
