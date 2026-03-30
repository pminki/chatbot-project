import os
import uuid
import sys
from glob import glob
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.database import SessionLocal, RagDocumentMeta

DATA_DIR = "./data"
CHROMA_PERSIST_DIR = "./chroma_db"

def ingest_to_db():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print("data 폴더 생성됨. 문서(pdf/txt)를 넣으세요.")
        return

    docs = []
    for f in glob(os.path.join(DATA_DIR, "*.pdf")): docs.extend(PyPDFLoader(f).load())
    for f in glob(os.path.join(DATA_DIR, "*.txt")): docs.extend(TextLoader(f, encoding='utf-8').load())
    
    if not docs: return
    
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunked = splitter.split_documents(docs)
    
    vector_store = Chroma(persist_directory=CHROMA_PERSIST_DIR, embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"), collection_name="lms_knowledge")
    db = SessionLocal()
    
    try:
        for doc in chunked:
            doc_id = str(uuid.uuid4())
            doc.metadata['doc_id'] = doc_id
            vector_store.add_documents(documents=[doc], ids=[doc_id])
            
            db.add(RagDocumentMeta(
                doc_id=doc_id, title=f"{os.path.basename(doc.metadata.get('source',''))} 발췌",
                source_type="INTERNAL_DOC", category="매뉴얼"
            ))
        db.commit()
        print("✅ 데이터 적재 성공")
    except Exception as e:
        db.rollback()
        print(f"오류: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    ingest_to_db()