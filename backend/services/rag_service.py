import os
import uuid
import shutil
from typing import List
from sqlalchemy.orm import Session
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from core.llm_factory import LLMFactory
from models.database import RagFile, RagDocumentMeta    # 데이터베이스 모델

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

    async def save_and_process_file(self, file_name: str, file_content: bytes):
        """사용자가 업로드한 파일을 저장하고, AI가 읽을 수 있도록 분석(인덱싱)을 시작합니다."""
        file_id = str(uuid.uuid4())     # 파일마다 고유한 아이디를 부여합니다.
        file_ext = os.path.splitext(file_name)[1].lower() # 파일 확장자를 추출합니다.

        # 지원하지 않는 파일 형식인지 확인합니다.
        if file_ext not in ['.pdf', '.txt']:
            raise ValueError("Unsupported file format. Only PDF and TXT are allowed.")

        # 파일을 서버의 uploads 폴더에 저장합니다.
        save_path = os.path.join(self.upload_dir, f"{file_id}{file_ext}")        
        with open(save_path, "wb") as buffer:
            buffer.write(file_content)

        # 1. DB에 초기 레코드 생성
        # 파일이 성공적으로 저장되었으므로, DB에도 '처리 중(PROCESSING)' 상태로 기록합니다.
        new_file = RagFile(
            file_id=file_id,
            filename=file_name,
            file_path=save_path,
            status="PROCESSING"
        )
        self.db.add(new_file)
        self.db.commit()

        # 2. 인덱싱 프로세스 시작
        # 실제 분석 로직을 수행합니다. 성공/실패 여부에 따라 상태를 업데이트합니다.
        try:
            await self._process_indexing(file_id, save_path, file_name)
            new_file.status = "COMPLETED"
        except Exception as e:
            print(f"Indexing Error for {file_name}: {e}")
            new_file.status = "ERROR"
        
        self.db.commit()

    async def _process_indexing(self, file_id: str, file_path: str, original_name: str):
        """
        [핵심 로직] 문서를 읽어서 작은 조각으로 나누고 벡터 데이터베이스에 저장합니다.
        문서 로드 -> 분할 -> 임베딩 -> 저장을 담당합니다.
        """
        # 1. 로더 선택
        # 파일 종류에 맞춰 텍스트를 읽어오는 '로더'를 선택합니다.
        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding='utf-8')

        docs = loader.load()

        # 2. 텍스트 분할
        # 긴 문장을 AI가 이해하기 쉬운 크기(1000자)로 쪼갭니다. (Chunking)
        # 문맥이 끊기지 않게 200자 정도는 앞뒤 조각과 겹치게 만듭니다 (overlap).
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(docs)

        # 3. 메타데이터 추가 및 저장 준비
        # 텍스트를 숫자로 변환(Embedding)해주는 도구를 준비합니다.
        embeddings = LLMFactory.get_embeddings()
        vector_store = Chroma(
            persist_directory=self.chroma_dir,
            embedding_function=embeddings,
            collection_name=self.collection_name
        )

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
        # 최종적으로 벡터 DB와 MySQL에 분석 결과를 한꺼번에 저장합니다.
        vector_store.add_documents(documents=docs_to_add, ids=ids_to_add)
        self.db.add_all(sql_records)
