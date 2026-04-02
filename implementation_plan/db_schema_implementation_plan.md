# DB 스키마 동기화 및 RAG 상태 업데이트 문제 최종 해결 계획

RAG 파일의 처리 상태가 업데이트되지 않는 근본 원인이 **`init.sql` 파일과 파이썬 코드 간의 DB 스키마 불일치**로 확인되었습니다. `init.sql`에 정의된 테이블 구조에 필수 컬럼(`file_id`)이 누락되어 분석 작업 중 SQL 오류가 발생하고 있었습니다.

## Proposed Changes

### [Database]

#### [MODIFY] [init.sql](file:///e:/project/chatbot-project/database/init.sql)
- `rag_files` 테이블 정의를 추가합니다. (기존 데이터베이스 초기화 시 누락됨)
- `rag_documents_meta` 테이블에 `file_id` 컬럼을 추가하고 인덱스를 설정합니다.
- `chat_messages` 테이블 등 기존 테이블들의 정밀한 컬럼 타입 및 제약 조건을 SQLAlchemy 모델과 일치시킵니다.

---

## Verification Plan

### Automated Tests
1. `docker compose down -v` 실행 (기존 데이터 및 잘못된 스키마 완전 삭제)
2. `docker compose up -d --build` 실행 (수정된 `init.sql`로 새 데이터베이스 인스턴스 생성)
3. 파일 업로드 API 호출 및 DB 쿼리를 통해 `rag_documents_meta` 테이블에 `file_id` 컬럼이 존재하는지 확인.

### Manual Verification
1. RAG 관리 페이지에서 파일 업로드.
2. 백엔드 로그 확인: `Unknown column 'file_id'` 오류가 사라졌는지 확인.
3. 약 수 초 후 상태가 "완료"로 바뀌는지 확인.
