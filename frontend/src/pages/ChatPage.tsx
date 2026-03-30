import React, { useState } from 'react';
import { ChatService } from '../services/api';

/**
 * [메시지 데이터 구조]
 */
interface Message {
  sender: 'user' | 'bot';
  text: string;
  intent?: string;
}

export const ChatPage: React.FC = () => {
  const [input, setInput] = useState(''); // 입력창 텍스트
  const [messages, setMessages] = useState<Message[]>([]); // 완료된 메시지 목록
  const [isPreparing, setIsPreparing] = useState(false); // AI 분석 중 상태

  /**
   * [스트리밍 상태 관리]
   * AI가 답변을 한 글자씩 내뱉을 때, 실시간으로 보여줄 임시 메시지입니다.
   */
  const [streamingMsg, setStreamingMsg] = useState<{ text: string, intent?: string } | null>(null);

  const sessionId = 'session-123';
  const userId = 'legacy-user-01';

  /**
   * [메시지 전송 로직]
   */
  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = input;
    setMessages(prev => [...prev, { sender: 'user', text: userMessage }]);
    setInput('');
    setIsPreparing(true); // AI가 분석을 시작함
    setStreamingMsg({ text: '', intent: undefined });

    let currentText = '';
    let currentIntent: string | undefined = undefined;

    // 스트리밍 서비스 호출
    await ChatService.streamMessage(
      { session_id: sessionId, user_id: userId, message: userMessage },
      // 1. 토큰(글자)이 올 때마다 호출
      (token) => {
        setIsPreparing(false); // 답변이 시작되면 분석 중 표시를 끔
        currentText += token;
        setStreamingMsg({ text: currentText, intent: currentIntent });
      },
      // 2. 의도가 파악됐을 때 호출
      (intent) => {
        currentIntent = intent;
        setStreamingMsg(prev => prev ? { ...prev, intent } : { text: '', intent });
      },
      // 3. 오류 발생 시 호출
      () => {
        setIsPreparing(false);
        setStreamingMsg(null);
        setMessages(prev => [...prev, { sender: 'bot', text: '죄송합니다. 통신 중 오류가 발생했습니다.', intent: 'ERROR' }]);
      }
    );

    // 4. 모든 답변 전송이 끝나면 임시 상태를 전체 메시지 리스트로 옮깁니다.
    if (currentText) {
      setMessages(prev => [...prev, { sender: 'bot', text: currentText, intent: currentIntent }]);
    }
    setStreamingMsg(null);
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px', width: '350px', backgroundColor: 'white' }}>
      <h3 style={{ margin: '0 0 15px 0' }}>AI 튜터링 (실시간 스트리밍)</h3>

      <div style={{ height: '350px', overflowY: 'auto', marginBottom: '10px', fontSize: '14px', paddingRight: '5px' }}>
        {/* 이전 대화 내용들 */}
        {messages.map((msg, idx) => (
          <div key={idx} style={{ textAlign: msg.sender === 'user' ? 'right' : 'left', margin: '10px 0' }}>
            <span style={{
              background: msg.sender === 'user' ? '#e6f7ff' : '#f6ffed',
              padding: '8px 12px', borderRadius: '8px', display: 'inline-block', whiteSpace: 'pre-wrap'
            }}>
              {msg.text}
            </span>
            {msg.intent === 'CS' && <div style={{ fontSize: '11px', color: '#ff4d4f', marginTop: '4px' }}>[고객지원 안내됨]</div>}
          </div>
        ))}

        {/* AI 분석 중 (박동 효과) */}
        {isPreparing && (
          <div style={{ textAlign: 'left', margin: '10px 0', color: '#999', fontStyle: 'italic', animation: 'fade 1s infinite alternate' }}>
            🤔 질문의 의도를 분석하고 있습니다...
          </div>
        )}

        {/* 🌟 실시간 스트리밍 답변 (말풍선 안에서 실시간으로 글자가 추가됨) */}
        {streamingMsg && !isPreparing && (
          <div style={{ textAlign: 'left', margin: '10px 0' }}>
            <span style={{
              background: '#f6ffed', padding: '8px 12px', borderRadius: '8px', display: 'inline-block', whiteSpace: 'pre-wrap'
            }}>
              {streamingMsg.text}
              <span style={{ animation: 'blink 0.8s infinite', fontWeight: 'bold' }}>|</span> {/* 커서 효과 */}
            </span>
            {streamingMsg.intent === 'CS' && <div style={{ fontSize: '11px', color: '#ff4d4f', marginTop: '4px' }}>[고객지원 안내됨]</div>}
          </div>
        )}
      </div>

      {/* 입력 영역 */}
      <div style={{ display: 'flex' }}>
        <input style={{ flex: 1, padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()} // [수정] deprecated된 onKeyPress 대신 onKeyDown 사용
          placeholder="메시지를 입력하세요..."
          disabled={isPreparing || streamingMsg !== null} // 응답 중일 때는 입력 방지
        />
        <button
          onClick={handleSend}
          disabled={isPreparing || streamingMsg !== null}
          style={{ marginLeft: '8px', padding: '8px 12px', cursor: (isPreparing || streamingMsg) ? 'not-allowed' : 'pointer' }}
        >
          {isPreparing ? '분석중' : '전송'}
        </button>
      </div>

      {/* 애니메이션 정의 */}
      <style>{`
        @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0; } 100% { opacity: 1; } }
        @keyframes fade { from { opacity: 0.4; } to { opacity: 1; } }
      `}</style>
    </div>
  );
};
