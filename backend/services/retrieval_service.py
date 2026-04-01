import os
from core.llm_factory import LLMFactory
from langchain_chroma import Chroma
from sqlalchemy.orm import Session
from models.database import SessionLocal, LearningTutorRecord, RagFile

# [입문자 가이드: Retrieval(검색)이란?]
# AI(LLM)는 똑똑하지만 모든 것을 알지는 못합니다. 
# RetrievalService는 사용자의 질문과 관련된 '외부 지식(PDF 등)'과 '과거 대화 내역'을 찾아내어 
# AI에게 전달해줌으로써, AI가 아는 척(환각)하지 않고 정확한 답변을 하게 돕습니다.

# 사용자의 질문과 관련된 정보를 ‘외부 지식 저장소’나 ‘학습 이력’에서 찾아오는 역할을 합니다. (RAG 시스템의 핵심 부품)
class RetrievalService:
    def __init__(self):
      """지식을 효율적으로 검색하기 위한 도구들을 준비합니다."""

      # 1. 임베딩 모델 설정: 텍스트를 숫자로 변환(Embedding)하여 컴퓨터가 의미를 이해하도록 돕는 모델을 가져옵니다.
      # 임베딩 모델 설정: 질문 문장을 수천 개의 숫자로 변환하여 '의미'를 파악하게 합니다.
      self.embeddings = LLMFactory.get_embeddings()
      
      # 2. 벡터 데이터베이스(ChromaDB) 로드: 
      # 미리 저장된 지식들이 들어있는 저장소(chroma_db)에 연결합니다.
      # 분석된 문서 조각들이 저장된 보물창고에 접속합니다.
      self.vector_store = Chroma(
        persist_directory=os.environ.get("CHROMA_DIR", "./chroma_db"), # 데이터 저장 경로
        embedding_function=self.embeddings, # 검색에 사용할 임베딩 방식
        collection_name="lms_knowledge" # 저장소 내의 책장 이름과 같습니다.
      )

    def retrieve_from_vector_db(self, query: str, k: int = 3):
        """
        벡터 DB에서 사용자의 질문 내용과 가장 비슷하며 도움이 될만한 자료를 k개 찾아옵니다.
        이때, 관리자 페이지에서 '활성화(True)'로 설정된 파일들만 검색 대상에 포함합니다.
        
        Args:
            query (str): 사용자의 질문 문장
            k (int): 찾아올 관련 문서의 개수 (기본값 3개)
        """
        db: Session = SessionLocal()
        try:
          # 1. 활성화 상태인 파일 ID 목록을 먼저 가져옵니다.
          #  SQL DB에서 현재 '채팅 사용' 스위치가 켜진 파일들의 ID만 골라냅니다.
          active_files = db.query(RagFile.file_id).filter(RagFile.is_active == True).all()
          active_file_ids = [f.file_id for f in active_files]

          # 활성화된 파일이 없다면 빈 문자열을 반환합니다.
          # 만약 활성화된 파일이 하나도 없다면, 검색할 필요 없이 빈 결과를 반환합니다.
          if not active_file_ids:
            return ""

          # 2. Chroma 검색 시 filter 파라미터를 사용하여 해당 파일들의 조각들만 검색합니다.
          # 유사도 검색(Similarity Search): 질문과 가장 의미가 비슷한 조각을 k개(기본 3개) 찾습니다.
          # filter={"file_id": {"$in": active_file_ids}} 형식을 사용합니다.
          # filter 옵션을 통해 '꺼둔' 문서의 내용은 답변에 포함되지 않게 원천 차단합니다.
          results = self.vector_store.similarity_search(
            query, 
            k=k, 
            filter={"file_id": {"$in": active_file_ids}}
          )

          # 검색된 여러 문서의 내용을 하나로 합쳐서 반환합니다.
          return "\n\n".join([doc.page_content for doc in results])

        except Exception as e:
          # 검색 중에 오류가 나더라도 프로그램이 꺼지지 않게 안전하게 처리합니다.
          print(f"벡터 데이터 검색 중 오류: {e}")
          return ""
        finally:
          db.close()


    def retrieve_from_sql_db(self, user_id: str, topic: str):
        """
        전통적인 SQL DB에서 해당 사용자가 예전에 이 주제로 무엇을 공부했는지(요약본) 가져옵니다.
        사용자가 과거에 이 주제로 공부했던 핵심 요약 내용을 SQL DB에서 가져옵니다.
        지식 검색이 '책'을 뒤지는 거라면, 이건 '학생의 지난 성적표'를 보는 것과 같습니다.
        
        Args:
            user_id (str): 사용자를 식별하는 고유 번호
            topic (str): 학습 주제 이름 (예: RAG, Python 등)
        """
        # 데이터베이스와 대화하기 위한 세션(통로)을 엽니다.
        db: Session = SessionLocal()
        try:
          # 해당 사용자의 특정 주제에 대한 가장 최근 기록 1개를 쿼리(질의)합니다.
          # 가장 최근에 기록된 학습 튜터 기록 1개를 찾습니다.
          record = db.query(LearningTutorRecord).filter(
            LearningTutorRecord.user_id == user_id,
            LearningTutorRecord.learning_topic == topic
          ).order_by(LearningTutorRecord.created_at.desc()).first()
          
          # 기록이 있고, 이전에 공부한 요약 내용이 있다면 반환합니다.
          # 과거 기록이 있다면 답변에 참고할 배경 지식으로 돌려줍니다.
          if record and record.session_summary:
              return f"[{topic} 이전 학습 요약]: {record.session_summary}"
          return ""
        except Exception as e:
          print(f"학습 기록 조회 중 오류: {e}")
          return ""
        finally:
          # DB 사용이 끝나면 통로를 반드시 닫아줘야 메모리 낭비가 없습니다.
          db.close()

    def get_combined_context(self, user_id: str, query: str, intent: str):
      """
      [최종 결과물] 검색한 '지식 조각'과 '사용자 이력'을 하나로 묶어서 AI에게 전달할 최종 참고 자료를 만듭니다.
      벡터 DB의 ‘지식’과 SQL DB의 ‘사용자 상태’를 하나로 합쳐서 AI에게 줄 조리법(Context)을 만듭니다.
      """
      combined = ""
      
      # 1단계: 질문과 직접적으로 관련된 참고 자료(지식; Vector DB)를 찾아옵니다.
      v_context = self.retrieve_from_vector_db(query)
      if v_context:
        combined += f"[참고 자료]\n{v_context}\n\n"
      
      # 2단계: 질문 의도가 'TUTOR(학습 지원)'일 경우에만 사용자의 과거 학습 정보를 가져옵니다. (맞춤형 응대용)
      if intent == "TUTOR":
        # 현재는 'RAG'라는 주제로 가정되어 있으나, 추후 유동적으로 변경 가능합니다.
        # 현재는 'RAG' 주제에 대해서만 관리하고 있지만, 나중에 과목별로 확장 가능합니다.
        s_context = self.retrieve_from_sql_db(user_id, topic="RAG") 
        if s_context:
          combined += f"[사용자의 기존 학습 상태 정보]\n{s_context}\n"
          
      return combined
