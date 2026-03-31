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

/**
 * [ChatPage 프롭스]
 */
interface ChatPageProps {
  userId?: string;
}

export const ChatPage: React.FC<ChatPageProps> = ({ userId = 'guest-user' }) => {
  const [input, setInput] = useState(''); // 입력창 텍스트
  const [messages, setMessages] = useState<Message[]>([]); // 완료된 메시지 목록
  const [isPreparing, setIsPreparing] = useState(false); // AI 분석 중 상태
  const [streamingMsg, setStreamingMsg] = useState<{ text: string, intent?: string } | null>(null);

  // [수정] 세션 ID를 랜덤하게 생성하거나 외부에서 주입받을 수 있도록 변경
  const [sessionId] = useState(() => `session-${Math.random().toString(36).substr(2, 9)}`);


  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage = input;
    setMessages(prev => [...prev, { sender: 'user', text: userMessage }]);
    setInput('');
    setIsPreparing(true);
    setStreamingMsg({ text: '', intent: undefined });

    let currentText = '';
    let currentIntent: string | undefined = undefined;

    await ChatService.streamMessage(
      { session_id: sessionId, user_id: userId, message: userMessage },
      (token) => {
        setIsPreparing(false);
        currentText += token;
        setStreamingMsg({ text: currentText, intent: currentIntent });
      },
      (intent) => {
        currentIntent = intent;
        setStreamingMsg(prev => prev ? { ...prev, intent } : { text: '', intent });
      },
      () => {
        setIsPreparing(false);
        setStreamingMsg(null);
        setMessages(prev => [...prev, { sender: 'bot', text: '죄송합니다. 통신 중 오류가 발생했습니다.', intent: 'ERROR' }]);
      }
    );

    if (currentText) {
      setMessages(prev => [...prev, { sender: 'bot', text: currentText, intent: currentIntent }]);
    }
    setStreamingMsg(null);
  };

  return (
    <div className="flex flex-col h-[600px] w-[400px] bg-slate-50 rounded-2xl shadow-2xl overflow-hidden border border-slate-200 font-sans">
      {/* 상단 헤더: 그라데이션과 그림자 효과 */}
      <header className="bg-indigo-600 px-6 py-4 shadow-md flex items-center justify-between">
        <h3 className="text-white font-bold text-lg tracking-tight">AI 학습 튜터</h3>
        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse shadow-[0_0_8px_rgba(74,222,128,0.8)]"></div>
      </header>

      {/* 메시지 리스트 영역 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}>
            <div className={`max-w-[85%] px-4 py-2.5 rounded-2xl text-sm shadow-sm leading-relaxed ${msg.sender === 'user'
              ? 'bg-indigo-600 text-white rounded-tr-none'
              : 'bg-white text-slate-800 border border-slate-100 rounded-tl-none'
              }`}>
              {msg.text}
              {msg.intent === 'CS' && (
                <div className="mt-2 text-[10px] font-semibold text-rose-500 uppercase tracking-wider border-t border-rose-100 pt-1">
                  Agent Notified
                </div>
              )}
            </div>
          </div>
        ))}

        {/* AI 분석 중 (스켈레톤 느낌의 애니메이션) */}
        {isPreparing && (
          <div className="flex justify-start animate-pulse">
            <div className="bg-indigo-50 border border-indigo-100 rounded-2xl rounded-tl-none px-4 py-2 text-indigo-400 text-sm italic">
              AI가 생각하는 중...
            </div>
          </div>
        )}

        {/* 실시간 스트리밍 답변 */}
        {streamingMsg && !isPreparing && (
          <div className="flex justify-start">
            <div className="max-w-[85%] bg-white border border-indigo-100 text-slate-800 px-4 py-2.5 rounded-2xl rounded-tl-none text-sm shadow-indigo-100 shadow-lg leading-relaxed relative">
              {streamingMsg.text}
              <span className="inline-block w-1.5 h-4 bg-indigo-400 ml-1 translate-y-0.5 animate-bounce"></span>
              {streamingMsg.intent === 'CS' && (
                <div className="mt-2 text-[10px] font-semibold text-rose-500 uppercase tracking-wider border-t border-rose-100 pt-1">
                  Agent Notified
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* 하단 입력 영역: 인라인 포커스 효과 */}
      <footer className="p-4 bg-white border-t border-slate-100 shadow-[0_-4px_12px_rgba(0,0,0,0.02)]">
        <div className="flex items-center space-x-2 bg-slate-50 border border-slate-200 p-1.5 rounded-xl transition-all focus-within:ring-2 focus-within:ring-indigo-500 focus-within:border-transparent focus-within:bg-white">
          <input
            className="flex-1 bg-transparent px-3 py-1.5 text-sm text-slate-700 placeholder-slate-400 focus:outline-none"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="궁금한 내용을 물어보세요..."
            disabled={isPreparing || streamingMsg !== null}
          />
          <button
            onClick={handleSend}
            disabled={isPreparing || streamingMsg !== null || !input.trim()}
            className={`p-2 rounded-lg transition-all transform active:scale-95 ${isPreparing || streamingMsg || !input.trim()
              ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
              : 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-md hover:shadow-indigo-200'
              }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
            </svg>
          </button>
        </div>
      </footer>
    </div>
  );
};

