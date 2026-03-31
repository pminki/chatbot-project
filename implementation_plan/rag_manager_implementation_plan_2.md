# RAG Management Enhancements Implementation Plan

This plan outlines the steps to enhance the Web-Based RAG Management system with search functionality, detailed file statistics (chunk counts), and a "Knowledge Preview" tool for testing retrieval accuracy.

## Proposed Changes

### Backend Enhancements

#### [MODIFY] [rag_service.py](file:///e:/project/chatbot-project/backend/services/rag_service.py)
- Update `get_all_files` to join with `RagDocumentMeta` and return the count of chunks per file.
- Add a helper method to count chunks.

#### [MODIFY] [main.py](file:///e:/project/chatbot-project/backend/main.py)
- Add a new endpoint `POST /api/rag/preview`:
    - Takes a query string.
    - Uses `RetrievalService` to fetch the context.
    - Returns the retrieved text chunks for manual verification.

---

### Frontend Enhancements

#### [MODIFY] [api.ts](file:///e:/project/chatbot-project/frontend/src/services/api.ts)
- Add `getRagPreview(query: string)` method to call the new backend endpoint.

#### [MODIFY] [RagManager.tsx](file:///e:/project/chatbot-project/frontend/src/pages/RagManager.tsx)
- **File List Stats**: Add a "Chunks" column to show the number of document fragments generated for each file.
- **Search Bar**: Add an input field to filter the file list by filename.
- **Knowledge Preview Section**: 
    - Add a new tab or section below the file table.
    - Input for searching knowledge.
    - Display area for retrieved chunks to verify if the RAG system is picking up the right information.
- **Styling**: Improve visual hierarchy with better spacing and contrast.

## Verification Plan

### Automated Tests
- Test `/api/rag/preview` with various queries to ensure it returns content only from `active` files.
- Verify chunk counts update correctly after a new file completes processing.

### Manual Verification
1. Upload a file and wait for completion.
2. Confirm the chunk count is displayed correctly (e.g., 5 chunks for a 1000-word doc).
3. Use the "Search" bar to find the file.
4. Use the "Knowledge Preview" tool to ask a question related to the uploaded file and verify the retrieved context matches the expected parts of the document.
5. Toggle the file to 'Inactive' and verify the "Knowledge Preview" no longer returns its content.
