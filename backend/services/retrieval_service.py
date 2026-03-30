import os
from core.llm_factory import LLMFactory
from langchain_chroma import Chroma
from sqlalchemy.orm import Session
from models.database import SessionLocal, LearningTutorRecord

class RetrievalService:
    def __init__(self):
      # 팩토리를 통해 임베딩 모델을 동적으로 주입
      self.embeddings = LLMFactory.get_embeddings()
      
      self.vector_store = Chroma(
        persist_directory=os.environ.get("CHROMA_DIR", "./chroma_db"),
        embedding_function=self.embeddings,
        collection_name="lms_knowledge"
      )

    def retrieve_from_vector_db(self, query: str, k: int = 3):
        try:
          results = self.vector_store.similarity_search(query, k=k)
          return "\n\n".join([doc.page_content for doc in results])
        except:
          return ""

    def retrieve_from_sql_db(self, user_id: str, topic: str):
        db: Session = SessionLocal()
        try:
          record = db.query(LearningTutorRecord).filter(
            LearningTutorRecord.user_id == user_id,
            LearningTutorRecord.learning_topic == topic
          ).order_by(LearningTutorRecord.created_at.desc()).first()
          if record and record.session_summary:
              return f"[{topic} 이전 학습 요약]: {record.session_summary}"
          return ""
        except:
          return ""
        finally:
          db.close()

    def get_combined_context(self, user_id: str, query: str, intent: str):
      combined = ""
      v_context = self.retrieve_from_vector_db(query)
      if v_context:
        combined += f"[참고 자료]\n{v_context}\n\n"
      if intent == "TUTOR":
        s_context = self.retrieve_from_sql_db(user_id, topic="RAG") # 임시 주제
        if s_context:
          combined += f"[학습자 이전 상태]\n{s_context}\n"
          
      return combined