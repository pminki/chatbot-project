import os
import uuid
import shutil
from typing import List
from sqlalchemy.orm import Session
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from core.llm_factory import LLMFactory
from models.database import RagFile, RagDocumentMeta, SessionLocal    # 데이터베이스 모델

# [입문자 가이드: RAG란?]
# RAG(Retrieval-Augmented Generation)는 AI가 학습하지 않은 최신 데이터나 
# 내부 문서(PDF 등)를 검색해서 그 내용을 바탕으로 답변하게 만드는 기술입니다.
class RagService:
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = "./uploads"   # 원본 파일이 저장될 폴더
        self.collection_name = "lms_knowledge" # 벡터 DB의 컬렉션 이름
        self.chroma_dir = os.environ.get("CHROMA_DIR", "./chroma_db") #  분석된 벡터 데이터가 저장될 폴더
        
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    def get_all_files(self) -> List[RagFile]:
        """현재 서버에 등록된 모든 RAG 관리 파일 목록을 반환합니다."""
        return self.db.query(RagFile).order_by(RagFile.created_at.desc()).all()

    def delete_file(self, file_id: str):
        """파일과 관련된 모든 데이터를 3곳(로컬 파일, 벡터 DB, MySQL)에서 삭제합니다."""
        rag_file = self.db.query(RagFile).filter(RagFile.file_id == file_id).first()
        if not rag_file:
            return

        # 1. 실제 서버 컴퓨터에 저장된 원본 파일 삭제
        if os.path.exists(rag_file.file_path):
            os.remove(rag_file.file_path)

        # 2. 벡터 데이터베이스(Chroma)에 저장된 분석 데이터 삭제
        embeddings = LLMFactory.get_embeddings()
        vector_store = Chroma(
            persist_directory=self.chroma_dir,
            embedding_function=embeddings,
            collection_name=self.collection_name
        )
        
        # 해당 file_id가 포함된 모든 chunk들을 찾아서 삭제합니다.
        # Chroma는 metadata 필터링을 통한 삭제를 지원합니다.
        vector_store.delete(where={"file_id": file_id})

        # 3. SQL 데이터 삭제 (RagDocumentMeta -> RagFile 순서)
        self.db.query(RagDocumentMeta).filter(RagDocumentMeta.file_id == file_id).delete()
        self.db.delete(rag_file)
        self.db.commit()

    def toggle_file_active(self, file_id: str, is_active: bool):
        """특정 문서를 챗봇이 읽게 할지 말지 결정하는 스위치 기능을 처리합니다."""
        rag_file = self.db.query(RagFile).filter(RagFile.file_id == file_id).first()

        if rag_file:
            rag_file.is_active = is_active
            # 연관된 모든 청크의 상태도 동기화합니다 (검색 시 SQL 조인을 피하기 위함)
            self.db.query(RagDocumentMeta).filter(RagDocumentMeta.file_id == file_id).update({"is_active": is_active})
            self.db.commit()
            return rag_file

        return None

    def save_file_sync(self, file: "UploadFile") -> dict:
        """[수정] 파일을 즉시 저장하고 DB에 초기 레코드를 생성합니다. 
        백그라운드 작업 시작 전에 호출되어야 파일 소멸을 방지할 수 있습니다."""
        file_name = file.filename
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file_name)[1].lower()

        if file_ext not in ['.pdf', '.txt']:
            raise ValueError("Unsupported file format. Only PDF and TXT are allowed.")

        save_path = os.path.join(self.upload_dir, f"{file_id}{file_ext}")        
        # 파일을 즉시 저장 (백그라운드가 아닌 메인 스레드에서 처리)
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # DB에 'PROCESSING' 상태로 즉시 기록
        new_file = RagFile(
            file_id=file_id,
            filename=file_name,
            file_path=save_path,
            status="PROCESSING"
        )
        self.db.add(new_file)
        self.db.commit()
        
        return {
            "file_id": file_id,
            "save_path": save_path,
            "file_name": file_name
        }

    @staticmethod
    def process_indexing_task(file_id: str, file_path: str, original_name: str):
        """[수정] 백그라운드 분석을 동기 메소드로 변경하여 스레드 풀에서 실행되도록 합니다.
        이렇게 하면 비동기 이벤트 루프를 방해하지 않고 독립적으로 작업을 끝낼 수 있습니다."""
        print(f"--- Indexing Task Started for {original_name} (ID: {file_id}) ---")
        db = SessionLocal()
        try:
            service = RagService(db)
            # await 없이 직접 호출 (동기 메소드이므로)
            service._process_indexing(file_id, file_path, original_name)
            
            print(f"Updating status to COMPLETED for {file_id}")
            rag_file = db.query(RagFile).filter(RagFile.file_id == file_id).first()
            if rag_file:
                rag_file.status = "COMPLETED"
                db.commit()
                print(f"Status successfully updated to COMPLETED for {file_id}")
            else:
                print(f"Warning: RagFile record not found for {file_id}")
        except Exception as e:
            import traceback
            print(f"Indexing Error for {original_name}: {e}")
            traceback.print_exc()
            rag_file = db.query(RagFile).filter(RagFile.file_id == file_id).first()
            if rag_file:
                rag_file.status = "ERROR"
                db.commit()
        finally:
            db.close()
            print(f"--- Indexing Task Finished for {original_name} ---")

    def _process_indexing(self, file_id: str, file_path: str, original_name: str):
        """
        [수정] 동기 메소드로 변경했습니다.
        문서 로드 -> 분할 -> 임베딩 -> 저장을 담당합니다.
        """
        # 1. 로더 선택
        print(f"Loading document from {file_path}")
        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding='utf-8')

        docs = loader.load()
        print(f"Document loaded. Total chunks expected from splitter...")

        # 2. 텍스트 분할
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(docs)
        print(f"Split completed. Created {len(chunks)} chunks.")

        # 3. 메타데이터 추가 및 저장 준비
        embeddings = LLMFactory.get_embeddings()
        vector_store = Chroma(
            persist_directory=self.chroma_dir,
            embedding_function=embeddings,
            collection_name=self.collection_name
        )
        print(f"Vector store initialized (Chroma).")

        sql_records = []
        docs_to_add = []
        ids_to_add = []

        # 4. 각 조각마다 메타데이터(출처 정보)를 달아줍니다.
        for chunk in chunks:
            doc_id = str(uuid.uuid4())
            chunk.metadata['file_id'] = file_id # 어떤 파일에서 온 조각인지 기록
            chunk.metadata['doc_id'] = doc_id
            
            docs_to_add.append(chunk)
            ids_to_add.append(doc_id)

            # DB 조회를 위한 정보도 따로 저장합니다.
            sql_records.append(RagDocumentMeta(
                doc_id=doc_id,
                file_id=file_id,
                title=f"{original_name} 발췌",
                source_type="INTERNAL_DOC",
                is_active=True
            ))

        # 5. 저장 (Chroma 및 SQL)
        # [수정] 임베딩 모델의 단일 요청 최대 토큰 한도(20,000)를 초과하지 않도록
        # 배치 크기를 50개로 설정합니다. (100개 기준 ~20,703 토큰으로 한도 초과 확인됨)
        batch_size = 50
        total_batches = (len(docs_to_add) + batch_size - 1) // batch_size
        print(f"Adding {len(docs_to_add)} documents to Vector DB in {total_batches} batches...")
        
        for i in range(0, len(docs_to_add), batch_size):
            batch_docs = docs_to_add[i : i + batch_size]
            batch_ids = ids_to_add[i : i + batch_size]
            print(f"  Uploading batch {i//batch_size + 1}/{total_batches} ({len(batch_docs)} docs)...")
            vector_store.add_documents(documents=batch_docs, ids=batch_ids)
            
        print(f"Finished adding all documents to Vector DB.")
        
        print(f"Adding metadata records to SQL DB...")
        self.db.add_all(sql_records)
        print(f"SQL metadata records added to session.")
