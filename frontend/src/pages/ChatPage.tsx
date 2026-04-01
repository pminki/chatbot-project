import React, { useState, useEffect, useRef } from 'react';
import { ChatService } from '../services/api'; // 백엔드 API와 통신하는 서비스입니다.
import { MarkdownRenderer } from '../components/MarkdownRenderer'; // 마크다운 텍스트를 예쁘게 보여주는 컴포넌트입니다.
import { X, Send } from 'lucide-react'; // 아이콘 라이브러리입니다.

/**
 * [메시지 데이터 구조]
 * 개별 메시지가 유저의 것인지, AI의 것인지, 그리고 어떤 내용인지를 정의합니다.
 */
interface Message {
  sender: 'user' | 'bot'; // 보내는 사람
  text: string; // 메시지 내용
  intent?: string; // AI가 파악한 의도 (예: CS 문의 등)
}

/**
 * [ChatPage 프롭스]
 * 컴포넌트가 외부에서 전달받을 수 있는 데이터들입니다.
 */
interface ChatPageProps {
  userId?: string;
}

export const ChatPage: React.FC<ChatPageProps> = ({ userId = 'guest-user' }) => {
  // --- 상태 관리 (State) ---
  const [input, setInput] = useState(''); // 사용자가 입력창에 타이핑 중인 글자
  const [messages, setMessages] = useState<Message[]>([]); // 대화창에 쌓인 이전 메시지들
  const [isPreparing, setIsPreparing] = useState(false); // 서버가 답변을 준비 중일 때 (생각 중...)
  const [streamingMsg, setStreamingMsg] = useState<{ text: string, intent?: string } | null>(null); // 실시간으로 글자가 써지는 중인 메시지

  const scrollRef = useRef<HTMLDivElement>(null); // 메시지 리스트의 끝으로 화면을 내리기 위한 도구
  const textareaRef = useRef<HTMLTextAreaElement>(null); // 입력창의 높이를 조절하기 위한 도구

  /**
   * [입력창 자동 높이 조절]
   * 사용자가 여러 줄을 입력하면 입력창이 아래로 길어지게 만듭니다. (최대 120px)
   */
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'; // 일단 높이를 초기화하고
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`; // 내용만큼 늘립니다.
    }
  }, [input]);

  /**
   * [자동 스크롤]
   * 메시지가 추가되거나 AI가 답변을 한 글자씩 쓰는 중일 때, 항상 최하단이 보이도록 스크롤합니다.
   */
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' }); // 부드럽게 아래로 이동
    }
  }, [messages, streamingMsg]);

  // 대화의 연속성을 위해 세션 ID를 하나 생성합니다. (새로고침 전까지 유지)
  const [sessionId] = useState(() => `session-${Math.random().toString(36).substr(2, 9)}`);

  /**
   * [닫기 버튼 클릭]
   * 챗봇 창을 닫으라는 신호(이벤트)를 브라우저에 보냅니다. (부모 HTML에서 이 신호를 듣고 창을 숨깁니다)
   */
  const handleClose = () => {
    window.dispatchEvent(new CustomEvent('close-chat'));
  };

  /**
   * [메시지 전송 함수]
   * 버튼을 누르거나 엔터를 쳤을 때 실행됩니다.
   */
  const handleSend = async () => {
    if (!input.trim()) return; // 빈 메시지는 보내지 않습니다.

    const userMessage = input;
    setMessages(prev => [...prev, { sender: 'user', text: userMessage }]); // 내가 보낸 메시지를 목록에 추가
    setInput(''); // 입력창 비우기
    setIsPreparing(true); // AI가 '생각 중...'인 상태로 표시
    setStreamingMsg({ text: '', intent: undefined }); // 실시간 메시지 영역 초기화

    let currentText = '';
    let currentIntent: string | undefined = undefined;

    // 서버로부터 실시간으로 답변 조각들을 받아옵니다.
    await ChatService.streamMessage(
      { session_id: sessionId, user_id: userId, message: userMessage },
      // 1. 새로운 글자 조각이 올 때마다 실행 (onToken)
      (token) => {
        setIsPreparing(false); // 첫 글자가 오기 시작하면 '생각 중...' 문구를 지웁니다.
        currentText += token;
        setStreamingMsg({ text: currentText, intent: currentIntent }); // 화면에 실시간으로 반영
      },
      // 2. AI가 유저의 의도를 파악했을 때 실행 (onIntent)
      (intent) => {
        currentIntent = intent;
        setStreamingMsg(prev => prev ? { ...prev, intent } : { text: '', intent });
      },
      // 3. 통신 오류가 났을 때 실행 (onError)
      () => {
        setIsPreparing(false);
        setStreamingMsg(null);
        setMessages(prev => [...prev, { sender: 'bot', text: '죄송합니다. 통신 중 오류가 발생했습니다.', intent: 'ERROR' }]);
      }
    );

    // 스트리밍이 완전히 끝나면, 최종 답변을 전체 메시지 목록에 정식으로 추가합니다.
    if (currentText) {
      setMessages(prev => [...prev, { sender: 'bot', text: currentText, intent: currentIntent }]);
    }
    setStreamingMsg(null); // 실시간 메시지 영역을 다시 비웁니다.
  };

  return (
    <div className="flex flex-col w-full h-full bg-slate-50 rounded-2xl shadow-2xl overflow-hidden border border-slate-200 font-sans relative">

      {/* 상단 헤더: 제목과 닫기 버튼 */}
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

      {/* 대화 내용이 보여지는 중간 영역 */}
      <div className="flex-1 overflow-y-auto px-5 py-6 space-y-5 bg-white/50 backdrop-blur-sm">
        {/* 이전 메시지들을 순서대로 보여줍니다. */}
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}>
            <div className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm shadow-sm leading-relaxed ${msg.sender === 'user'
              ? 'bg-indigo-100 text-gray-900 rounded-tr-none' // 유저 메시지 스타일
              : 'bg-white text-slate-800 border border-slate-100 rounded-tl-none prose prose-slate' // AI 메시지 스타일
              }`}>
              <MarkdownRenderer content={msg.text} />
              {/* 만약 상담사가 필요하다는 버튼 등이 포함된 경우 표시 */}
              {msg.intent === 'CS' && (
                <div className="mt-2 text-[10px] font-semibold text-rose-500 uppercase tracking-wider border-t border-rose-100 pt-1">
                  Agent Notified
                </div>
              )}
            </div>
          </div>
        ))}

        {/* AI가 서버에서 첫 응답을 준비 중일 때 보여주는 로딩 애니메이션 */}
        {isPreparing && (
          <div className="flex justify-start animate-pulse">
            <div className="bg-indigo-50 border border-indigo-100 rounded-2xl rounded-tl-none px-4 py-2 text-indigo-400 text-sm italic">
              AI가 생각하는 중...
            </div>
          </div>
        )}

        {/* AI가 실시간으로 답변을 써내려가는 중일 때 보여주는 영역 */}
        {streamingMsg && !isPreparing && (
          <div className="flex justify-start">
            <div className="max-w-[85%] bg-white border border-indigo-100 text-slate-800 px-4 py-3 rounded-2xl rounded-tl-none text-sm shadow-indigo-100/30 shadow-lg leading-relaxed relative prose prose-slate">
              <MarkdownRenderer content={streamingMsg.text} />
              {/* 타이핑 효과를 위해 깜빡이는 커서 */}
              <span className="inline-block w-1.5 h-4 bg-indigo-400 ml-1 translate-y-0.5 animate-bounce"></span>
              {streamingMsg.intent === 'CS' && (
                <div className="mt-2 text-[10px] font-semibold text-rose-500 uppercase tracking-wider border-t border-rose-100 pt-1">
                  Agent Notified
                </div>
              )}
            </div>
          </div>
        )}

        {/* 새 메시지가 올 때 자동으로 스크롤할 위치를 잡아주는 빈 태그 */}
        <div ref={scrollRef} className="h-1" />
      </div>

      {/* 하단 입력창 영역 */}
      <footer className="px-5 py-5 bg-white border-t border-slate-100 shadow-[0_-4px_12px_rgba(0,0,0,0.02)]">
        <div className="flex items-center space-x-3 bg-slate-50 border border-slate-200 p-2 rounded-2xl transition-all focus-within:ring-2 focus-within:ring-indigo-500/20 focus-within:border-indigo-500 focus-within:bg-white group">
          <textarea
            ref={textareaRef}
            className="flex-1 bg-transparent px-2 py-1.5 text-sm text-slate-700 placeholder-slate-400 focus:outline-none resize-none min-h-[36px] max-h-[120px] scrollbar-hide"
            rows={1}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) { // 엔터키를 누르면 전송 (Shift+Enter는 다음 줄)
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="궁금한 내용을 물어보세요..."
            disabled={isPreparing || streamingMsg !== null} // 답변 중일 때는 입력을 막습니다.
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

