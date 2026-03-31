CREATE DATABASE IF NOT EXISTS ai_chatbot_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ai_chatbot_db;

CREATE TABLE chat_sessions (
  session_id VARCHAR(100) PRIMARY KEY COMMENT 'LangGraph thread_id와 1:1 매핑',
  user_id VARCHAR(50) NOT NULL COMMENT '레거시 시스템 사용자 ID (외래키 역할)',
  session_type VARCHAR(20) DEFAULT 'NORMAL' COMMENT '모드: CS, TUTORING, CURATION, NORMAL 등',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '세션 생성 일시',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '세션 최근 업데이트 일시',
  INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='챗봇 대화 세션 관리';

CREATE TABLE learning_tutor_records (
  record_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  session_id VARCHAR(100) NOT NULL COMMENT '연결된 대화 세션',
  user_id VARCHAR(50) NOT NULL COMMENT '학습자 ID',
  learning_topic VARCHAR(200) NOT NULL COMMENT '현재 학습 중인 주제 (예: RAG 개념, Java Spring 기초 등)',
  understanding_level VARCHAR(50) COMMENT 'AI가 파악한 학습자의 이해도 (예: 입문, 개념 이해 중, 심화 질문 단계 등)',
  session_summary LONGTEXT COMMENT '해당 세션에서 학습한 핵심 개념 요약 (세션 종료 시 AI가 자동 요약하여 저장)',
  recommended_next_step TEXT COMMENT '튜터가 제안하는 다음 학습 방향, 추천 RAG 문서 또는 퀴즈',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_learning_tutor_session FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
  INDEX idx_tutor_user_topic (user_id, learning_topic)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='학습 도우미 튜터링 이력 관리';

CREATE TABLE rag_documents_meta (
  doc_id VARCHAR(100) PRIMARY KEY COMMENT 'Vector DB(Chroma, FAISS 등)의 Document ID와 동일',
  title VARCHAR(255) NOT NULL COMMENT '문서 제목',

  source_type VARCHAR(50) NOT NULL COMMENT '출처: LEGACY_DB, INTERNAL_PDF, MANUAL 등',
  legacy_ref_id VARCHAR(100) COMMENT '레거시 DB 원본 PK (iBatis/MyBatis 쿼리 연동용)',
  category VARCHAR(100) COMMENT '큐레이션 카테고리 (예: 사내규정, 기술문서 등)',
  is_active TINYINT(1) DEFAULT 1 COMMENT 'RAG 검색 노출 여부 (1: 활성, 0: 비활성)',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='RAG 학습 문서 메타 정보';

CREATE TABLE chat_messages (
  message_id BIGINT AUTO_INCREMENT PRIMARY KEY,
  session_id VARCHAR(100) NOT NULL,
  role VARCHAR(20) NOT NULL COMMENT '발화자: USER, ASSISTANT, SYSTEM',
  content LONGTEXT NOT NULL COMMENT '메시지 내용',
  tokens_used INT DEFAULT 0 COMMENT 'LLM 토큰 사용량 (과금 및 통계용)',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_chat_messages_session FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='대화 상세 내역 (Memory)';
