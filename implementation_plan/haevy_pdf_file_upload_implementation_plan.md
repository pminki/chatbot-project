# RAG 대용량 파일 인덱싱 API 제한(250건) 해결 계획

12MB 이상의 대용량 파일을 인덱싱할 때, 생성된 텍스트 조각(Chunk)의 수가 Google Vertex AI API의 단일 요청 제한(250개)을 초과하여 발생하는 오류를 해결합니다.

## Proposed Changes

### [Backend]

#### [MODIFY] [llm_factory.py](file:///e:/project/chatbot-project/backend/core/llm_factory.py)
- `VertexAIEmbeddings` 인스턴스 생성 시 `batch_size=250` (또는 더 안전한 값인 100)을 설정합니다.

#### [MODIFY] [rag_service.py](file:///e:/project/chatbot-project/backend/services/rag_service.py)
- `_process_indexing` 메소드에서 `vector_store.add_documents`를 호출할 때, 전체 조각 리스트를 일정한 크기(예: 100개)로 나누어 루프를 돌며 저장하도록 수정합니다. (이중 안전장치)

---

## Verification Plan

### Automated Tests
- 대용량 텍스트(최소 500개 이상의 조각이 생성될 분량)를 포함한 테스트 파일을 업로드하여 인덱싱이 끊기지 않고 완료되는지 확인합니다.
- 백엔드 로그에서 `Adding X documents to Vector DB...` 로그가 여러 번 출력되는지 확인합니다.

### Manual Verification
- 에러가 발생했던 `JavaScript.Cookbook...` 파일을 다시 업로드하여 상태가 "완료"로 정상 변경되는지 확인합니다.
