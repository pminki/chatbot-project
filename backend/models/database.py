import os
from sqlalchemy import create_engine, Column, BigInteger, String, Text, DateTime, func, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base

DB_URL = os.getenv("DATABASE_URL", "mysql+pymysql://chatbot_user:chatbot_password@localhost:3306/ai_chatbot_db?charset=utf8mb4")

engine = create_engine(DB_URL, pool_recycle=3600)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class LearningTutorRecord(Base):
    __tablename__ = "learning_tutor_records"
    record_id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    learning_topic = Column(String(200), nullable=False)
    understanding_level = Column(String(50))
    session_summary = Column(Text)
    recommended_next_step = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class RagDocumentMeta(Base):
    __tablename__ = "rag_documents_meta"
    doc_id = Column(String(100), primary_key=True)
    title = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)
    legacy_ref_id = Column(String(100))
    category = Column(String(100))
    is_active = Column(Boolean, default=True)