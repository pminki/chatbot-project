import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown'; // 텍스트 형태의 마크다운을 HTML로 변환해주는 핵심 라이브러리입니다.
import remarkGfm from 'remark-gfm'; // 표(Table), 체크리스트 등 'GitHub 스타일' 마크다운을 지원하게 해줍니다.
import remarkBreaks from 'remark-breaks'; // 엔터(줄바꿈)를 실제 화면에서도 줄바꿈으로 인식하게 해줍니다.
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'; // 코드 블록을 알록달록하게 색칠(하이라이트)해줍니다.
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'; // 코드 하이라이트의 어두운 테마 스타일입니다.
import { Copy, Check } from 'lucide-react'; // 아이콘 라이브러리입니다. (복사 버튼용)

interface Props {
  content: string; // 챗봇이 보낸 답변(마크다운 텍스트)을 전달받습니다.
}

/**
 * [마크다운 렌더러 컴포넌트]
 * 이 컴포넌트는 일반 텍스트를 받아서 예쁜 HTML 화면으로 그려줍니다.
 */
export const MarkdownRenderer: React.FC<Props> = ({ content }) => {
  return (
    <ReactMarkdown
      // 추가 기능을 위한 플러그인들을 설정합니다.
      remarkPlugins={[remarkGfm, remarkBreaks]}
      // 마크다운 요소별로 어떤 HTML 태그나 컴포넌트를 사용해서 그릴지 정의합니다.
      components={{
        // '코드' 부분에 대한 설정입니다. (```코드```)
        code({ node, inline, className, children, ...props }: any) {
          const match = /language-(\w+)/.exec(className || ''); // 어떤 언어인지(예: python, javascript) 알아냅니다.
          const [copies, setCopies] = useState(false); // 복사 완료 상태를 관리합니다.

          // 코드 복사 기능을 담당하는 함수입니다.
          const handleCopy = () => {
            navigator.clipboard.writeText(String(children).replace(/\n$/, ''));
            setCopies(true);
            setTimeout(() => setCopies(false), 2000); // 2초 뒤에 다시 복사 아이콘으로 되돌립니다.
          };

          // 한 줄 짜리 코드가 아닌, 여러 줄의 '코드 블록'인 경우
          return !inline && match ? (
            <div className="relative group my-4 rounded-lg overflow-hidden border border-slate-700">
              {/* 상단바: 언어 이름과 복사 버튼 */}
              <div className="flex items-center justify-between px-4 py-1.5 bg-slate-800 text-slate-400 text-xs border-b border-slate-700">
                <span>{match[1]}</span>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1 hover:text-white transition-colors"
                >
                  {copies ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
                  {copies ? 'Copied!' : 'Copy'}
                </button>
              </div>
              {/* 실제 알록달록한 코드 본문 */}
              <SyntaxHighlighter
                {...props}
                style={oneDark}
                language={match[1]}
                PreTag="div"
                customStyle={{
                  margin: 0,
                  padding: '1rem',
                  fontSize: '0.875rem',
                  backgroundColor: '#1e293b',
                }}
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            </div>
          ) : (
            // 문장 중간에 있는 짧은 코드(예: `ls`)는 평범하게 출력합니다.
            <code className="bg-slate-100 text-indigo-600 px-1.5 py-0.5 rounded text-sm font-medium" {...props}>
              {children}
            </code>
          );
        },
        // 문단(p), 목록(ul, ol), 인용문(blockquote), 제목(h1~h3) 등에 Tailwind CSS 디자인을 입힙니다.
        p: ({ children, ...props }: any) => <p className="mb-3 last:mb-0 leading-relaxed text-sm md:text-base" {...props}>{children}</p>,
        ul: ({ children, ...props }: any) => <ul className="list-disc ml-5 mb-3 space-y-1" {...props}>{children}</ul>,
        ol: ({ children, ...props }: any) => <ol className="list-decimal ml-5 mb-3 space-y-1" {...props}>{children}</ol>,
        li: ({ children, ...props }: any) => <li className="text-sm md:text-base" {...props}>{children}</li>,
        blockquote: ({ children, ...props }: any) => (
          <blockquote className="border-l-4 border-indigo-300 pl-4 italic my-3 text-slate-600" {...props}>
            {children}
          </blockquote>
        ),
        h1: ({ children, ...props }: any) => <h1 className="text-xl font-bold mt-4 mb-2" {...props}>{children}</h1>,
        h2: ({ children, ...props }: any) => <h2 className="text-lg font-bold mt-4 mb-2" {...props}>{children}</h2>,
        h3: ({ children, ...props }: any) => <h3 className="text-md font-bold mt-3 mb-1" {...props}>{children}</h3>,
      }}
    >
      {content}
    </ReactMarkdown>
  );
};
