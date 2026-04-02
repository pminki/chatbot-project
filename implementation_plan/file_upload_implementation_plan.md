# 대용량 PDF 업로드 에러 해결 계획 (ERR_EMPTY_RESPONSE)

12.8MB 크기의 PDF 업로드 시 서버가 응답 없이 연결을 끊는 문제를 해결하기 위한 계획입니다.

## 문제 분석
- **현상**: `net::ERR_EMPTY_RESPONSE` 및 `Failed to fetch`.
- **원인 추정**: 
    - `await file.read()` 호출 시 대용량 파일을 한 번에 메모리에 올리면서 발생하는 부하.
    - 백그라운드 작업(`save_and_process_file`)이 실행되는 동안 메인 이벤트 루프가 차단되어 다른 API(`api/rag/files`) 호출에 응답하지 못함.
    - `PyPDFLoader` 및 `Chroma` 작업의 높은 CPU/IO 부하.

## 제안하는 변경 사항

### 1. [백엔드] 파일 업로드 방식 개선 (`backend/main.py`)
- `await file.read()`를 제거하고, `UploadFile` 객체 자체를 `RagService`에 넘겨서 스트리밍 방식으로 파일 시스템에 직접 기록하게 변경합니다.
- 사용자가 업로드 버튼을 누르면 최대한 빨리 `"업로드 중..."` 응답을 보내어 연결이 끊기지 않게 합니다.

### 2. [백엔드] 블로킹 작업 최적화 (`backend/services/rag_service.py`)
- `PyPDFLoader.load()`와 `vector_store.add_documents()`는 동기적으로 작동하여 메인 루프를 멈출 수 있습니다.
- 이를 별도의 스레드(`run_in_threadpool` 등)에서 실행하도록 보완하거나, 백그라운드 태스크가 확실히 비동기적으로 동작하는지 검증합니다.

### 3. [공통] 타임아웃 및 용량 제한 설정
- Uvicorn 실행 시 타임아웃 설정을 확인합니다.

---

## 상세 수정 계획

### [MODIFY] [main.py](file:///e:/project/chatbot-project/backend/main.py)
- `upload_rag_file` 엔드포인트 수정: 
    - 파일을 메모리에 읽지 않고 `RagService.save_and_process_file`에 `file` 객체를 전달.
    - `RagService` 내부에서 파일을 저장한 후 즉시 응답 반환.

### [MODIFY] [rag_service.py](file:///e:/project/chatbot-project/backend/services/rag_service.py)
- `save_and_process_file` 수정: `bytes` 대신 `UploadFile`을 인자로 받음.
- `shutil.copyfileobj`를 사용하여 파일을 청크 단위로 저장하여 메모리 효율성 극대화.
- 인덱싱 작업(`_process_indexing`) 시작 전에 파일 저장이 완료되었음을 DB에 먼저 반영.

## 확인 계획

### 수동 확인
1. 10MB 이상의 PDF 파일을 업로드하여 `ERR_EMPTY_RESPONSE` 없이 정상적으로 `"업로드 중"` 메시지가 뜨는지 확인.
2. 업로드 진행 중 `api/rag/files` (파일 목록) API를 호출했을 때 서버가 멈추지 않고 응답하는지 확인.
3. `uploads` 폴더에 파일이 정상적으로 생성되는지 확인.
4. 백그라운드 작업 완료 후 상태가 `COMPLETED`로 변경되는지 확인.

## 열린 질문
- 현재 서버 실행 환경(Docker, Local, Nginx 여부)에 따라 Nginx의 `client_max_body_size` 설정이 필요할 수 있습니다. 로컬 테스트 중이신가요?
