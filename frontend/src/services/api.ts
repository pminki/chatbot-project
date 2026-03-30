import { ChatRequest } from '../types/chat';

/**
 * [백엔드 서버 주소 설정]
 */
const API_BASE_URL = 'http://localhost:8000/api';

/**
 * [채팅 통신 서비스 (스트리밍 버전)]
 * AI의 답변을 기다리지 않고, 실시간으로 한 글자씩 받아오는 기능을 담당합니다.
 */
export const ChatService = {
  /**
   * 서버에 질문을 보내고, 실시간으로 쏟아지는 답변 데이터를 처리합니다.
   * 
   * @param payload 질문 내용 (세션 ID, 사용자 ID 포함)
   * @param onToken 새로운 글자(토큰)가 도착했을 때 실행할 콜백
   * @param onIntent AI가 질문의 의도를 파악했을 때 실행할 콜백 (TUTOR, CS 등)
   * @param onError 네트워크 오류 발생 시 실행할 콜백
   */
  async streamMessage(
    payload: ChatRequest,
    onToken: (text: string) => void,
    onIntent: (intent: string) => void,
    onError: () => void
  ): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      // 브라우저가 스트리밍을 지원하지 않는 경우 예외 처리
      if (!response.body) throw new Error('이 브라우저는 스트리밍을 지원하지 않습니다.');

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = ''; // 쪼개져서 오는 데이터를 합치기 위한 임시 저장소

      while (true) {
        const { done, value } = await reader.read();
        if (done) break; // 데이터 전송이 끝났으면 반복문 탈출

        // 1. 바이너리 데이터를 텍스트로 변환
        buffer += decoder.decode(value, { stream: true });

        // 2. SSE 규격(data: ...)에 맞춰 데이터를 쪼갭니다.
        // 네트워크 지연 등의 이유로 여러 메시지가 한꺼번에 올 수 있으므로 \n\n으로 나눕니다.
        const messages = buffer.split('\n\n');
        buffer = messages.pop() || ''; // 아직 완성되지 않은 마지막 조각은 버퍼에 남깁니다.

        for (const message of messages) {
          if (message.startsWith('data: ')) {
            const dataStr = message.substring(6).trim();
            if (!dataStr) continue;

            try {
              const data = JSON.parse(dataStr);
              if (data.type === 'token') {
                // 한 글자가 올 때마다 화면을 업데이트합니다.
                onToken(data.content);
              } else if (data.type === 'intent') {
                // AI가 의도를 분석했다면 해당 정보를 처리합니다.
                onIntent(data.intent);
              } else if (data.type === 'end') {
                return; // 모든 답변 전송 완료
              }
            } catch (e) {
              console.error('데이터 해석 중 오류:', e, dataStr);
            }
          }
        }
      }
    } catch (error) {
      console.error('스트리밍 통신 에러:', error);
      onError();
    }
  }
};
