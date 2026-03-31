# Web-Based RAG Management System

The current RAG process requires manual file placement and script execution (`ingest_data.py`). I will implement a web-based system to handle the entire lifecycle: **Upload → Process → Manage → Toggle**.

## User Review Required

> [!IMPORTANT]
> **Asynchronous Processing**: File ingestion can take time. I will use FastAPI's `BackgroundTasks` to process files in the background, allowing the UI to remain responsive while showing the "Processing" status.
> 
> **Storage**: Uploaded files will be stored in a new `./uploads` directory. Please ensure the server has enough disk space and appropriate permissions.

## Proposed Changes

### 1. Database Expansion

#### [MODIFY] [database.py](file:///e:/project/chatbot-project/backend/models/database.py)
Add a `RagFile` table to track uploaded files and their processing status. Update `RagDocumentMeta` to link it to a file.

```python
class RagFile(Base):
    __tablename__ = "rag_files"
    file_id = Column(String(100), primary_key=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    status = Column(String(20), default="PENDING") # PENDING, PROCESSING, COMPLETED, ERROR
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

# RagDocumentMeta에 file_id 컬럼 추가 (어느 파일 소속인지 추적)
```

### 2. Backend Services

#### [NEW] [rag_service.py](file:///e:/project/chatbot-project/backend/services/rag_service.py)
A new service to handle:
- **File Ingestion**: Logic moved from `ingest_data.py` (split, embed, save to Chroma/SQL).
- **Cleanup**: Delete vectors and metadata when a file is removed.
- **Filtering**: Synchronize "active" status logic for retrieval.

#### [MODIFY] [retrieval_service.py](file:///e:/project/chatbot-project/backend/services/retrieval_service.py)
Update the searching logic to filter by `file_id` based on the `is_active` flag in SQL.

```python
# retrieve_from_vector_db에서 Chroma의 filter 파라미터 활용
# filter={"file_id": {"$in": active_file_ids}}
```

### 3. API Endpoints

#### [MODIFY] [main.py](file:///e:/project/chatbot-project/backend/main.py)
Add new routes for RAG management:
- `POST /api/rag/upload`: File upload (Multipart/form-data).
- `GET /api/rag/files`: List managed files.
- `PATCH /api/rag/files/{id}`: Toggle `is_active`.
- `DELETE /api/rag/files/{id}`: Remove all data associated with the file.

### 4. Frontend UI (Management Page)

#### [NEW] [RagManager.tsx](file:///e:/project/chatbot-project/frontend/src/pages/RagManager.tsx)
Build a dashboard to:
- Show a table of uploaded files with status indicators.
- Provide an upload modal/button.
- Include toggle switches for "Use in Chat" (is_active).
- Delete buttons for clean removal.

## Additional Recommendations

1. **Chunking Preview**: Show how many chunks were generated per file to give users an idea of the document's "weight" in the AI's mind.
2. **Category/Tagging**: Allow users to categorize files (e.g., "Legal", "Technical", "HR") for even more granular filtering during chat.
3. **Download Original**: Option to download the original file from the management UI.

## Verification Plan

### Automated Tests
- Upload a PDF/TXT via API and verify it reaches `COMPLETED` status.
- Verify `RagFile` and `RagDocumentMeta` records are correctly linked.
- Verify Chroma collection includes the new `file_id` metadata.

### Manual Verification
- Upload a file, set `is_active=False`, and confirm the AI *doesn't* use its information.
- Toggle it back to `True` and confirm the AI *does* use it.
