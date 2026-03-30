import os
from sqlalchemy import create_engine, Column, BigInteger, String, Text, DateTime, func, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. 데이터베이스 연결 주소(URL) 설정
# 환경 변수 "DATABASE_URL"이 있으면 사용하고, 없으면 기본 MySQL 접속 정보를 사용합니다.
DB_URL = os.getenv("DATABASE_URL", "mysql+pymysql://chatbot_user:chatbot_password@localhost:3306/ai_chatbot_db?charset=utf8mb4")

# 2. 데이터베이스 엔진 생성
# 'pool_recycle'은 연결 유지를 위한 설정입니다.
engine = create_engine(DB_URL, pool_recycle=3600)

# 3. 데이터베이스 세션(통로) 생성 도구
# 실제로 데이터에 접근하고 수정을 요청할 때 'SessionLocal'을 사용합니다.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. 모델들의 기본 클래스(Base)
# 이 클래스를 상속받아 파이썬 클래스를 만들면, SQLAlchemy가 이를 테이블로 인식합니다.
Base = declarative_base()

# [테이블 1: LearningTutorRecord] 
# 사용자가 튜터와 대화하며 학습한 이력을 저장하는 표입니다.
class LearningTutorRecord(Base):
  __tablename__ = "learning_tutor_records"
  record_id = Column(BigInteger, primary_key=True, autoincrement=True) # 고유 기록 번호
  session_id = Column(String(100), nullable=False, index=True)         # 대화 방 번호
  user_id = Column(String(50), nullable=False, index=True)            # 사용자 ID
  learning_topic = Column(String(200), nullable=False)                # 학습한 주제
  understanding_level = Column(String(50))                            # 이해도 등급
  session_summary = Column(Text)                                      # 이번 대화의 요약본
  recommended_next_step = Column(Text)                                # 다음에 공부할 내용 추천
  created_at = Column(DateTime, default=func.now())                   # 기록 생성 시간
  updated_at = Column(DateTime, default=func.now(), onupdate=func.now()) # 기록 수정 시간

# [테이블 2: RagDocumentMeta]
# AI가 참고하는 지식 문서(RAG용)의 메타데이터(정보)를 저장합니다.
class RagDocumentMeta(Base):
  __tablename__ = "rag_documents_meta"
  doc_id = Column(String(100), primary_key=True)                      # 문서 조각의 고유 ID
  title = Column(String(255), nullable=False)                         # 문서 제목(또는 발췌 제목)
  source_type = Column(String(50), nullable=False)                    # 출처 (예: INTERNAL_DOC)
  legacy_ref_id = Column(String(100))                                 # 이전 시스템 참조 ID
  category = Column(String(100))                                      # 문서 분류(카테고리)
  is_active = Column(Boolean, default=True)                           # 현재 사용 중인지 여부

# [테이블 3: ChatMessage]
# 모든 채팅 메시지 실시간 로그를 보관합니다.
class ChatMessage(Base):
  __tablename__ = "chat_messages"
  message_id = Column(BigInteger, primary_key=True, autoincrement=True) # 메시지 고유 번호
  session_id = Column(String(100), nullable=False, index=True)         # 어느 대화 방인지
  role = Column(String(20), nullable=False) # 보낸 사람의 역할 ('USER', 'ASSISTANT', 'SYSTEM')
  content = Column(Text, nullable=False)     # 메시지 실제 내용
  tokens_used = Column(BigInteger, default=0) # 이 답변을 만들 때 사용된 AI 토큰 양
  created_at = Column(DateTime, default=func.now())                    # 메시지가 생성된 시각
