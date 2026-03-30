import React, { useState, useEffect } from 'react';
import { ChatService } from '../services/api';
import { ChatResponse } from '../types/chat';

interface Message {
  sender: 'user' | 'bot';
  text: string;
  intent?: string;
}

// -------------------------------------------------------------
// [타이핑 효과 커스텀 컴포넌트]
// 텍스트를 받아서 지정된 속도(ms)로 한 글자씩 렌더링합니다.
//  speed = 30 로 타이핑 속도를 설정 (단위 : ms)
// -------------------------------------------------------------
const TypewriterText: React.FC<{ text: string; speed?: number }> = ({ text, speed = 30 }) => {
  const [displayedText, setDisplayedText] = useState('');

  useEffect(() => {
    let currentIndex = 0;
    setDisplayedText(''); // 텍스트가 바뀔 때 초기화

    const timer = setInterval(() => {
      if (currentIndex < text.length) {
        setDisplayedText((prev) => prev + text.charAt(currentIndex));
        currentIndex++;
      } else {
        clearInterval(timer);
      }
    }, speed);

    return () => clearInterval(timer); // 컴포넌트 언마운트 시 타이머 정리
  }, [text, speed]);

  return <span>{displayedText}</span>;
};


export const ChatPage: React.FC = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isPreparing, setIsPreparing] = useState(false); // 답변 준비 상태 추가

  const sessionId = 'session-123';
  const userId = 'legacy-user-01';

  const handleSend = async () => {
    if (!input.trim()) return;
    
    // 1. 사용자 메시지 즉시 렌더링 및 입력창 비우기
    setMessages(prev => [...prev, { sender: 'user', text: input }]);
    setInput('');
    setIsPreparing(true); // "답변 준비 중" 상태 켜기

    try {
      // 2. 백엔드 API 호출
      const result: ChatResponse = await ChatService.sendMessage({
        session_id: sessionId, user_id: userId, message: input,
      });
      
      // 3. 응답 도착 -> "준비 중" 끄고 봇 메시지 추가 (타이핑 효과 시작됨)
      setIsPreparing(false);
      setMessages(prev => [...prev, { sender: 'bot', text: result.response, intent: result.intent }]);
    } catch (error) {
      setIsPreparing(false);
      setMessages(prev => [...prev, { sender: 'bot', text: '오류가 발생했습니다.', intent: 'ERROR' }]);
    }
  };

  return (
    <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px', width: '350px', backgroundColor: 'white' }}>
      <h3 style={{ margin: '0 0 15px 0' }}>AI 튜터링 지원</h3>
      
      {/* 채팅 대화창 */}
      <div style={{ height: '350px', overflowY: 'auto', marginBottom: '10px', fontSize: '14px', paddingRight: '5px' }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{ textAlign: msg.sender === 'user' ? 'right' : 'left', margin: '10px 0' }}>
            <span style={{ 
              background: msg.sender === 'user' ? '#e6f7ff' : '#f6ffed', 
              padding: '8px 12px', borderRadius: '8px', display: 'inline-block', whiteSpace: 'pre-wrap'
            }}>
              {/* 봇 메시지일 경우 타이핑 효과 컴포넌트 적용, 사용자 메시지는 바로 출력 */}
              {msg.sender === 'bot' ? <TypewriterText text={msg.text} speed={25} /> : msg.text}
            </span>
            {msg.intent === 'CS' && <div style={{ fontSize: '11px', color: '#ff4d4f', marginTop: '4px' }}>[시스템지원팀 안내됨]</div>}
          </div>
        ))}
        
        {/* [답변 준비 중 인디케이터] */}
        {isPreparing && (
          <div style={{ textAlign: 'left', margin: '10px 0' }}>
            <span style={{ 
              background: '#f0f0f0', padding: '8px 12px', borderRadius: '8px', 
              display: 'inline-block', color: '#666', fontStyle: 'italic', animation: 'pulse 1.5s infinite' 
            }}>
              🤔 AI가 답변을 고민하고 있습니다...
            </span>
            <style>
              {`@keyframes pulse { 0% { opacity: 0.5; } 50% { opacity: 1; } 100% { opacity: 0.5; } }`}
            </style>
          </div>
        )}
      </div>

      {/* 입력창 */}
      <div style={{ display: 'flex' }}>
        <input style={{ flex: 1, padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
          value={input} onChange={e => setInput(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && handleSend()}
          placeholder="질문을 입력하세요" 
          disabled={isPreparing} // 준비 중일 때 입력 방지
        />
        <button onClick={handleSend} disabled={isPreparing} style={{ marginLeft: '8px', padding: '8px 12px', cursor: 'pointer' }}>
          전송
        </button>
      </div>
    </div>
  );
};