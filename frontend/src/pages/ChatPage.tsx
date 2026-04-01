import React, { useState, useEffect, useRef } from 'react';
import { ChatService } from '../services/api';
import { MarkdownRenderer } from '../components/MarkdownRenderer';
import { X, Send } from 'lucide-react';


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
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  /**
   * [자동 높이 조절]
   */
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  /**
   * [자동 스크롤]
   * 새로운 메시지가 추가되거나 답변이 스트리밍될 때마다 화면을 가장 아래로 내립니다.
   */
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, streamingMsg]);


  // [수정] 세션 ID를 랜덤하게 생성하거나 외부에서 주입받을 수 있도록 변경
  const [sessionId] = useState(() => `session-${Math.random().toString(36).substr(2, 9)}`);

  /**
   * [닫기 이벤트 발생]
   * 부모(index.html)에서 인식할 수 있도록 커스텀 이벤트를 발생시킵니다.
   */
  const handleClose = () => {
    window.dispatchEvent(new CustomEvent('close-chat'));
  };

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
    <div className="flex flex-col w-full h-full bg-slate-50 rounded-2xl shadow-2xl overflow-hidden border border-slate-200 font-sans relative">
      {/* 상단 헤더: 제목과 닫기 버튼으로 균형 유지 */}
      <header className="bg-slate-800 px-5 py-4 shadow-md flex items-center justify-between">
        <div className="flex items-center">
          <h3 className="text-white font-bold text-lg tracking-tight">AI 학습 튜터</h3>
          <div className="w-2 h-2 ml-2 bg-green-400 rounded-full animate-pulse shadow-[0_0_8px_rgba(74,222,128,0.8)]"></div>
        </div>
        <button
          onClick={handleClose}
          aria-label="닫기"
          className="text-white/80 hover:text-white transition-colors p-1 hover:bg-white/10 rounded-lg active:scale-95"
        >
          <X size={20} />
        </button>
      </header>

      {/* 메시지 리스트 영역 */}
      <div className="flex-1 overflow-y-auto px-5 py-6 space-y-5 bg-white/50 backdrop-blur-sm">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}>
            <div className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm shadow-sm leading-relaxed ${msg.sender === 'user'
              ? 'bg-indigo-100 text-gray-900 rounded-tr-none'
              : 'bg-white text-slate-800 border border-slate-100 rounded-tl-none prose prose-slate max-w-none'
              }`}>
              <MarkdownRenderer content={msg.text} />
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
            <div className="max-w-[85%] bg-white border border-indigo-100 text-slate-800 px-4 py-3 rounded-2xl rounded-tl-none text-sm shadow-indigo-100/30 shadow-lg leading-relaxed relative prose prose-slate max-w-none">
              <MarkdownRenderer content={streamingMsg.text} />
              <span className="inline-block w-1.5 h-4 bg-indigo-400 ml-1 translate-y-0.5 animate-bounce"></span>
              {streamingMsg.intent === 'CS' && (
                <div className="mt-2 text-[10px] font-semibold text-rose-500 uppercase tracking-wider border-t border-rose-100 pt-1">
                  Agent Notified
                </div>
              )}
            </div>
          </div>
        )}

        {/* 자동 스크롤 전용 타겟 */}
        <div ref={scrollRef} className="h-1" />
      </div>


      {/* 하단 입력 영역: 좌우 대칭이 완벽한 푸터 디자인 */}
      <footer className="px-5 py-5 bg-white border-t border-slate-100 shadow-[0_-4px_12px_rgba(0,0,0,0.02)]">
        <div className="flex items-center space-x-3 bg-slate-50 border border-slate-200 p-2 rounded-2xl transition-all focus-within:ring-2 focus-within:ring-indigo-500/20 focus-within:border-indigo-500 focus-within:bg-white group">
          <textarea
            ref={textareaRef}
            className="flex-1 bg-transparent px-2 py-1.5 text-sm text-slate-700 placeholder-slate-400 focus:outline-none resize-none min-h-[36px] max-h-[120px] scrollbar-hide"
            rows={1}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="궁금한 내용을 물어보세요..."
            disabled={isPreparing || streamingMsg !== null}
          />
          <button
            onClick={handleSend}
            disabled={isPreparing || streamingMsg !== null || !input.trim()}
            className={`p-2.5 rounded-xl transition-all transform active:scale-95 flex items-center justify-center ${isPreparing || streamingMsg || !input.trim()
              ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
              : 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-lg shadow-indigo-100'
              }`}
          >
            <Send size={18} />
          </button>
        </div>
      </footer>

    </div>
  );
};

