import os
import uuid
import shutil
from typing import List
from sqlalchemy.orm import Session
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from core.llm_factory import LLMFactory
from models.database import RagFile, RagDocumentMeta

class RagService:
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = "./uploads"
        self.collection_name = "lms_knowledge"
        self.chroma_dir = os.environ.get("CHROMA_DIR", "./chroma_db")
        
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    def get_all_files(self) -> List[RagFile]:
        """모든 RAG 관리 파일 목록을 반환합니다."""
        return self.db.query(RagFile).order_by(RagFile.created_at.desc()).all()

    def delete_file(self, file_id: str):
        """파일과 관련된 모든 데이터를 삭제합니다 (로컬 파일, SQL, Vector DB)."""
        rag_file = self.db.query(RagFile).filter(RagFile.file_id == file_id).first()
        if not rag_file:
            return

        # 1. 로컬 파일 삭제
        if os.path.exists(rag_file.file_path):
            os.remove(rag_file.file_path)

        # 2. Vector DB (Chroma) 데이터 삭제
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
        """특정 파일의 RAG 검색 사용 여부를 토글합니다."""
        rag_file = self.db.query(RagFile).filter(RagFile.file_id == file_id).first()
        if rag_file:
            rag_file.is_active = is_active
            # 연관된 모든 청크의 상태도 동기화합니다 (검색 시 SQL 조인을 피하기 위함)
            self.db.query(RagDocumentMeta).filter(RagDocumentMeta.file_id == file_id).update({"is_active": is_active})
            self.db.commit()
            return rag_file
        return None

    async def save_and_process_file(self, file_name: str, file_content: bytes):
        """파일을 저장하고 백그라운드에서 인덱싱 프로세스를 시작합니다."""
        file_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file_name)[1].lower()
        if file_ext not in ['.pdf', '.txt']:
            raise ValueError("Unsupported file format. Only PDF and TXT are allowed.")

        save_path = os.path.join(self.upload_dir, f"{file_id}{file_ext}")
        
        with open(save_path, "wb") as buffer:
            buffer.write(file_content)

        # 1. DB에 초기 레코드 생성
        new_file = RagFile(
            file_id=file_id,
            filename=file_name,
            file_path=save_path,
            status="PROCESSING"
        )
        self.db.add(new_file)
        self.db.commit()

        # 2. 인덱싱 프로세스 시작
        try:
            await self._process_indexing(file_id, save_path, file_name)
            new_file.status = "COMPLETED"
        except Exception as e:
            print(f"Indexing Error for {file_name}: {e}")
            new_file.status = "ERROR"
        
        self.db.commit()

    async def _process_indexing(self, file_id: str, file_path: str, original_name: str):
        """문서 로드 -> 분할 -> 임베딩 -> 저장을 담당합니다."""
        # 1. 로더 선택
        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding='utf-8')

        docs = loader.load()

        # 2. 텍스트 분할
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(docs)

        # 3. 메타데이터 추가 및 저장 준비
        embeddings = LLMFactory.get_embeddings()
        vector_store = Chroma(
            persist_directory=self.chroma_dir,
            embedding_function=embeddings,
            collection_name=self.collection_name
        )

        sql_records = []
        docs_to_add = []
        ids_to_add = []

        for chunk in chunks:
            doc_id = str(uuid.uuid4())
            chunk.metadata['file_id'] = file_id
            chunk.metadata['doc_id'] = doc_id
            
            docs_to_add.append(chunk)
            ids_to_add.append(doc_id)

            sql_records.append(RagDocumentMeta(
                doc_id=doc_id,
                file_id=file_id,
                title=f"{original_name} 발췌",
                source_type="INTERNAL_DOC",
                is_active=True
            ))

        # 4. 저장 (Chroma 및 SQL)
        vector_store.add_documents(documents=docs_to_add, ids=ids_to_add)
        self.db.add_all(sql_records)
