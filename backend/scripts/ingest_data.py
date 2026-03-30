import os
import sys
import uuid
from glob import glob
from dotenv import load_dotenv

# 1. 환경 설정 로드: 프로젝트 최상단의 .env 파일에 적힌 설정(API 키 등)을 가져옵니다.
load_dotenv()

# 2. 실행 경로 설정: 이 스크립트가 어느 폴더에 있든 'backend' 폴더 내의 모듈을 찾을 수 있게 해줍니다.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from core.llm_factory import LLMFactory
from models.database import SessionLocal, RagDocumentMeta

# 데이터가 들어있는 폴더와 벡터 DB가 저장될 폴더 경로를 설정합니다.
DATA_DIR = "./data"
CHROMA_PERSIST_DIR = os.environ.get("CHROMA_DIR", "./chroma_db")
COLLECTION_NAME = "lms_knowledge"

def ingest_to_db():
  """
  로컬 폴더의 문서(PDF, TXT)를 읽어와서 AI가 검색할 수 있도록 데이터베이스에 저장하는 메인 함수입니다.
  """
  # 데이터 폴더가 없으면 미리 만들어줍니다.
  if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    print(f"📂 '{DATA_DIR}' 폴더가 생성되었습니다. 학습할 문서를 넣고 다시 실행해주세요.")
    return

  # [단계 1] 문서 파일들 읽어오기
  docs = []
  # PDF 파일들을 찾아와서 텍스트로 읽어들입니다.
  for f in glob(os.path.join(DATA_DIR, "*.pdf")): 
    print(f"📄 PDF 로딩 중: {f}")
    docs.extend(PyPDFLoader(f).load())
  # TXT 파일들을 찾아와서 텍스트로 읽어들입니다.
  for f in glob(os.path.join(DATA_DIR, "*.txt")): 
    print(f"📝 TXT 로딩 중: {f}")
    docs.extend(TextLoader(f, encoding='utf-8').load())
  
  if not docs: 
    print("⚠️ 학습할 문서가 없습니다. './data' 폴더에 파일을 넣어주세요.")
    return
  
  # [단계 2] 문서 쪼개기 (Chunking)
  # AI가 한 번에 읽기 좋게 문서를 적당한 크기(1000자)로 나눕니다.
  # 겹치는 부분(200자)을 두어 맥락이 끊기지 않게 합니다.
  print("✂️ 문서 분할(Chunking) 중...")
  text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
  chunked_docs = text_splitter.split_documents(docs)
  
  # [단계 3] 임베딩 모델 준비
  # LLMFactory를 통해 현재 설정(OpenAI 혹은 Google)에 맞는 임베딩 도구를 가져옵니다.
  embeddings = LLMFactory.get_embeddings()
  print(f"🔗 사용 중인 임베딩 모델: {type(embeddings).__name__}")
  
  # 벡터 데이터베이스(Chroma)에 연결합니다.
  vector_store = Chroma(
    persist_directory=CHROMA_PERSIST_DIR,
    embedding_function=embeddings,
    collection_name=COLLECTION_NAME
  )

  # [단계 4] 데이터베이스 세션 및 저장 준비
  db = SessionLocal() # MariaDB(관계형 DB) 연결
  
  try:
    print(f"🧠 총 {len(chunked_docs)}개의 문서 조각을 처리 중...")
    
    # 성능 최적화를 위해 하나씩 저장하지 않고 한꺼번에(Batch) 저장할 리스트를 준비합니다.
    docs_to_add = []
    ids_to_add = []
    sql_records = []
    
    for doc in chunked_docs:
      # 각 문서 조각마다 고유한 주민번호(ID)를 부여합니다.
      doc_id = str(uuid.uuid4())
      source_file = os.path.basename(doc.metadata.get('source', 'unknown'))
      
      # 메타데이터에 ID 정보 추가
      doc.metadata['doc_id'] = doc_id
      
      # 저장할 목록에 담기
      docs_to_add.append(doc)
      ids_to_add.append(doc_id)
      
      # 관계형 DB(MariaDB)에 저장할 데이터 형식 준비
      sql_records.append(RagDocumentMeta(
        doc_id=doc_id,
        title=f"{source_file} 발췌",
        source_type="INTERNAL_DOC",
        category="사내매뉴얼",
        is_active=True
      ))
    
    # A. 벡터 DB(Chroma)에 한꺼번에 저장 (네트워크 및 디스크 속도 향상)
    print("🚀 Vector DB(Chroma)에 데이터를 저장하는 중...")
    vector_store.add_documents(documents=docs_to_add, ids=ids_to_add)
    
    # B. 관계형 DB(MariaDB)에 메타데이터 한꺼번에 저장 (안전한 기록 보관)
    print("💾 MariaDB(SQL)에 메타데이터를 저장하는 중...")
    db.add_all(sql_records)
    
    # 모든 변경 사항을 한꺼번에 승인(Commit)합니다.
    db.commit()
    print("✅ 성공적으로 모든 데이터가 적재되었습니다!")

  except Exception as e:
    # 저장 중 오류가 나면 지금까지의 작업을 모두 취소하고 원래대로 되돌립니다.
    db.rollback()
    print(f"❌ 데이터 적재 중 오류 발생: {e}")
  finally:
    # 작업이 끝나면 데이터베이스 연결을 닫아줍니다.
    db.close()

if __name__ == "__main__":
    # 이 파일을 직접 실행할 경우 ingest_to_db() 함수가 작동합니다.
    ingest_to_db()
