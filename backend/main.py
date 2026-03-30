from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.schemas import ChatRequest, ChatResponse
from services.agent_service import ChatbotAgent

app = FastAPI(title="LMS AI Chatbot API")

# 개발 환경 프론트엔드 연동을 위한 CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = ChatbotAgent()

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    result = agent.chat(
        session_id=req.session_id,
        user_id=req.user_id,
        message=req.message
    )
    return ChatResponse(
        response=result["response"],
        intent=result["intent"]
    )