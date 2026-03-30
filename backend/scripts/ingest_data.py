import os
import sys
import uuid
from glob import glob
from dotenv import load_dotenv

# 스크립트 단독 실행 시 프로젝트 최상단의 .env 파일을 읽어오기 위한 설정
load_dotenv()

# 프로젝트 내 다른 모듈 임포트를 위한 경로 설정 (backend 폴더를 path에 추가)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

# [수정됨] OpenAI 고정 임베딩 대신 LLMFactory 임포트
from core.llm_factory import LLMFactory
from models.database import SessionLocal, RagDocumentMeta

DATA_DIR = "./data"
# .env에 CHROMA_DIR이 설정되어 있으면 가져오고, 없으면 기본값 사용
CHROMA_PERSIST_DIR = os.environ.get("CHROMA_DIR", "./chroma_db")
COLLECTION_NAME = "lms_knowledge"

def ingest_to_db():
  if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    print(f"📂 '{DATA_DIR}' 폴더가 생성되었습니다. 학습할 문서를 넣고 다시 실행해주세요.")
    return

  docs = []
  # PDF 및 TXT 로드
  for f in glob(os.path.join(DATA_DIR, "*.pdf")): 
    print(f"📄 PDF 로딩 중: {f}")
    docs.extend(PyPDFLoader(f).load())
  for f in glob(os.path.join(DATA_DIR, "*.txt")): 
    print(f"📝 TXT 로딩 중: {f}")
    docs.extend(TextLoader(f, encoding='utf-8').load())
  
  if not docs: 
    print("⚠️ 학습할 문서가 없습니다.")
    return
  
  print("✂️ 문서 분할(Chunking) 중...")
  text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
  chunked_docs = text_splitter.split_documents(docs)
  
  # [수정됨] LLMFactory를 통해 현재 설정된 제공자(OpenAI/VertexAI)의 임베딩 모델 호출
  embeddings = LLMFactory.get_embeddings()
  print(f"🔗 사용 중인 임베딩 모델: {type(embeddings).__name__}")
  
  vector_store = Chroma(
    persist_directory=CHROMA_PERSIST_DIR,
    embedding_function=embeddings,
    collection_name=COLLECTION_NAME
  )

  # MariaDB 세션 오픈
  db = SessionLocal()
  
  try:
    print(f"🧠 총 {len(chunked_docs)}개의 문서 조각을 임베딩하여 저장합니다...")
    
    for doc in chunked_docs:
      doc_id = str(uuid.uuid4())
      source_file = os.path.basename(doc.metadata.get('source', 'unknown'))
      doc.metadata['doc_id'] = doc_id
      
      # A. ChromaDB에 벡터 저장 (이때 VertexAI 또는 OpenAI의 API가 호출됨)
      vector_store.add_documents(documents=[doc], ids=[doc_id])
      
      # B. MariaDB에 메타데이터 동기화
      db.add(RagDocumentMeta(
        doc_id=doc_id,
        title=f"{source_file} 발췌",
        source_type="INTERNAL_DOC",
        category="사내매뉴얼",
        is_active=True
      ))
        
    db.commit()
    print("✅ 성공적으로 Vector DB와 MariaDB에 데이터가 적재되었습니다!")

  except Exception as e:
    db.rollback()
    print(f"❌ 데이터 적재 중 오류 발생: {e}")
  finally:
      db.close()

if __name__ == "__main__":
    ingest_to_db()