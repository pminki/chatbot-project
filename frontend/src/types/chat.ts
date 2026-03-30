/**
 * [타입 정의: ChatRequest]
 * 프론트엔드에서 서버에 채팅을 요청할 때 사용하는 '데이터 가이드라인'입니다.
 */
export interface ChatRequest {
  session_id: string; // 대화 내용을 구분하기 위한 고유 세션 ID
  user_id: string;    // 사용자(학생)를 식별하기 위한 고유 ID
  message: string;    // 실제로 한 질문의 내용 (텍스트)
}

/**
 * [타입 정의: ChatResponse]
 * 서버에서 답변이 올 때 어떤 모양으로 오는지 정의한 '답변 가이드라인'입니다.
 */
export interface ChatResponse {
  response: string;   // AI가 생성한 최종 답변
  intent: string;     // AI가 판별한 사용자의 질문 의도 (예: TUTOR, CS)
}
