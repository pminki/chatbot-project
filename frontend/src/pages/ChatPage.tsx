import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom'; // 전체 화면 시 부모 컨테이너의 제약을 벗어나기 위해 포털을 사용합니다.
import { ChatService } from '../services/api';
import { MarkdownRenderer } from '../components/MarkdownRenderer';
import { X, Send, Maximize2, Minimize2 } from 'lucide-react';

/**
 * [메시지 데이터 구조]
 */
interface Message {
  sender: 'user' | 'bot';
  text: string;
  intent?: string;
  isGreeting?: boolean; // 첫 인사말인지 구분하기 위한 속성
}

/**
 * [ChatPage 프롭스]
 */
interface ChatPageProps {
  userId?: string;
}

export const ChatPage: React.FC<ChatPageProps> = ({ userId = 'guest-user' }) => {
  // --- 상태 관리 (State) ---
  const [input, setInput] = useState('');
  // [수정] 처음에 빈 목록이 아니라, 안내 문구를 넣어서 시작합니다.
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'bot',
      text: '안녕하세요! 😊\n무엇을 도와드릴까요?',
      isGreeting: true
    }
  ]);
  const [isPreparing, setIsPreparing] = useState(false);
  const [streamingMsg, setStreamingMsg] = useState<{ text: string, intent?: string } | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  /**
   * [입력창 자동 높이 조절]
   */
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  /**
   * [자동 스크롤]
   */
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, streamingMsg]);

  const [sessionId] = useState(() => `session-${Math.random().toString(36).substr(2, 9)}`);

  /**
   * [닫기 버튼 클릭]
   */
  const handleClose = () => {
    if (isExpanded) setIsExpanded(false);
    window.dispatchEvent(new CustomEvent('close-chat'));
  };

  /**
   * [전체화면 토글]
   */
  const handleToggleExpand = () => {
    const next = !isExpanded;
    setIsExpanded(next);
    window.dispatchEvent(new CustomEvent(next ? 'chat-expand' : 'chat-collapse'));
  };

  /**
   * [메시지 전송 함수]
   * @param overrideText 버튼 클릭 등 직접 텍스트를 보낼 때 사용
   */
  const handleSend = async (overrideText?: string) => {
    const messageToSend = overrideText || input;
    if (!messageToSend.trim()) return;

    setMessages(prev => [...prev, { sender: 'user', text: messageToSend }]);
    if (!overrideText) setInput(''); // 직접 입력한 경우만 입력창을 비웁니다.

    setIsPreparing(true);
    setStreamingMsg({ text: '', intent: undefined });

    let currentText = '';
    let currentIntent: string | undefined = undefined;

    await ChatService.streamMessage(
      { session_id: sessionId, user_id: userId, message: messageToSend },
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

  /**
   * [채팅창 렌더링 함수]
   */
  const renderChatContent = () => (
    <div
      id="ai-chatbot-window"
      className={`flex flex-col bg-slate-50 shadow-2xl overflow-hidden border border-slate-200 font-sans relative transition-all duration-300 ease-in-out ${isExpanded
        ? 'ai-chatbot-fullscreen'
        : 'w-full h-full rounded-2xl'
        }`}
    >
      {/* 상단 헤더 */}
      <header className="bg-slate-800 px-5 py-4 shadow-md flex items-center justify-between flex-shrink-0">
        <div className="flex items-center">
          <h3 className="text-white font-bold text-lg tracking-tight">AI 학습 튜터</h3>
          <div className="w-2 h-2 ml-2 bg-green-400 rounded-full animate-pulse shadow-[0_0_8px_rgba(74,222,128,0.8)]"></div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleToggleExpand}
            aria-label={isExpanded ? '창 축소' : '전체화면 확대'}
            title={isExpanded ? '창 축소' : '전체화면 확대'}
            className="text-white/80 hover:text-white transition-colors p-1 hover:bg-white/10 rounded-lg active:scale-95"
          >
            {isExpanded ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
          </button>
          <button
            onClick={handleClose}
            aria-label="닫기"
            className="text-white/80 hover:text-white transition-colors p-1 hover:bg-white/10 rounded-lg active:scale-95"
          >
            <X size={20} />
          </button>
        </div>
      </header>

      {/* 대화 내용 */}
      <div className="flex-1 overflow-y-auto px-5 py-6 space-y-5 bg-white/50 backdrop-blur-sm">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'} animate-fade-in`}>
            <div className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm shadow-sm leading-relaxed ${msg.sender === 'user'
              ? 'bg-indigo-100 text-gray-900 rounded-tr-none'
              : 'bg-white text-slate-800 border border-slate-100 rounded-tl-none prose prose-slate'
              }`}>
              <MarkdownRenderer content={msg.text} />
              {msg.intent === 'CS' && (
                <div className="mt-2 text-[10px] font-semibold text-rose-500 uppercase tracking-wider border-t border-rose-100 pt-1">
                  Agent Notified
                </div>
              )}
            </div>

            {/* [추가] 인사말 메시지 아래에만 선택 버튼을 표시합니다. */}
            {msg.isGreeting && messages.length === 1 && (
              <div className="mt-4 flex flex-wrap gap-2 w-full">
                <button
                  onClick={() => handleSend('📚 공부 도움 (개념 설명, 문제 풀이)')}
                  className="bg-white hover:bg-indigo-50 border border-indigo-200 text-indigo-700 px-4 py-2.5 rounded-xl text-xs font-semibold text-left transition-all shadow-sm hover:shadow-md active:scale-95 w-fit"
                >
                  📚 공부 도움
                </button>
                <button
                  onClick={() => handleSend('💬 이용 문의 (결제, 오류, 계정 등)')}
                  className="bg-white hover:bg-indigo-50 border border-indigo-200 text-indigo-700 px-4 py-2.5 rounded-xl text-xs font-semibold text-left transition-all shadow-sm hover:shadow-md active:scale-95 w-fit"
                >
                  💬 이용 문의
                </button>
              </div>
            )}
          </div>
        ))}
        {isPreparing && (
          <div className="flex justify-start animate-pulse">
            <div className="bg-indigo-50 border border-indigo-100 rounded-2xl rounded-tl-none px-4 py-2 text-indigo-400 text-sm italic">
              AI가 생각하는 중...
            </div>
          </div>
        )}
        {streamingMsg && !isPreparing && (
          <div className="flex justify-start">
            <div className="max-w-[85%] bg-white border border-indigo-100 text-slate-800 px-4 py-3 rounded-2xl rounded-tl-none text-sm shadow-indigo-100/30 shadow-lg leading-relaxed relative prose prose-slate">
              <MarkdownRenderer content={streamingMsg.text} />
              <span className="inline-block w-1.5 h-4 bg-indigo-400 ml-1 translate-y-0.5 animate-bounce"></span>
            </div>
          </div>
        )}
        <div ref={scrollRef} className="h-1" />
      </div>

      {/* 하단 입력창 */}
      <footer className="px-5 py-5 bg-white border-t border-slate-100 shadow-[0_-4px_12px_rgba(0,0,0,0.02)] flex-shrink-0">
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
            onClick={() => handleSend()}
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

  if (isExpanded) {
    return createPortal(renderChatContent(), document.body);
  }

  return renderChatContent();
};
