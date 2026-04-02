# RAG 파일 업로드 상태 "처리 중..." 고정 문제 해결 계획

파일 업로드 후 상태가 "처리 중..."에서 멈추는 문제는 크게 두 가지 원인으로 파악됩니다.
1. **DB 세션 종료 문제**: 백그라운드 작업이 시작되기 전에 메인 API 스레드에서 DB 세션을 닫아버려, 백그라운드 작업이 상태 업데이트를 기록하지 못하고 실패합니다.
2. **파일 핸들 종료 문제**: FastAPI의 `UploadFile` 객체는 API 응답이 나가면 자동으로 닫힙니다. 백그라운드 작업에서 이 파일의 내용을 읽으려 하면 이미 닫힌 파일이라 오류가 발생합니다.

## User Review Required

> [!IMPORTANT]
> 백그라운드 작업 방식이 변경됩니다. 기존에는 파일 저장부터 분석까지 모두 백그라운드에서 처리했으나, 안정성을 위해 **파일 저장은 API 요청 스레드에서 즉시 처리**하고, **분석(인덱싱) 작업만 백그라운드**로 넘기도록 수정합니다.

## Proposed Changes

### [Backend]

#### [MODIFY] [rag_service.py](file:///e:/project/chatbot-project/backend/services/rag_service.py)
- `save_and_process_file` 메소드를 두 단계로 분리하거나 세션 관리를 직접 하도록 수정합니다.
- 백그라운드에서 실행될 `process_indexing_task` (가칭)가 별도의 DB 세션을 생성하여 사용하도록 합니다.

#### [MODIFY] [main.py](file:///e:/project/chatbot-project/backend/main.py)
- `upload_rag_file` 엔드포인트에서 파일을 먼저 디스크에 저장하고 DB에 초기 레코드를 생성합니다.
- 이후 분석 작업만 백그라운드 태스크로 등록합니다.

---

## Open Questions

- 현재 파일 업로드 크기 제한이나 타임아웃에 대한 특별한 설정이 필요한가요? (기본값으로 진행합니다.)

## Verification Plan

### Automated Tests
- `POST /api/rag/upload` 요청 후 반환되는 `file_id`를 확인합니다.
- `GET /api/rag/files`를 지속적으로 호출하여 해당 파일의 상태가 `PROCESSING` -> `COMPLETED`로 변경되는지 확인합니다.
- 백엔드 로그에 `Indexing Error`가 발생하는지 모니터링합니다.

### Manual Verification
- 프론트엔드 RAG 관리 페이지에서 실제 PDF/TXT 파일을 업로드하고 상태 뱃지가 '완료'로 바뀌는지 확인합니다.
- 브라우저 개발자 도구의 네트워크 탭에서 무한 반복되는 요청이 멈추거나 정상적인 응답(COMPLETED)을 받는지 확인합니다.
