import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkBreaks from 'remark-breaks';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check } from 'lucide-react';

interface Props {
  content: string;
}

export const MarkdownRenderer: React.FC<Props> = ({ content }) => {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, remarkBreaks]}
      components={{
        code({ node, inline, className, children, ...props }: any) {
          const match = /language-(\w+)/.exec(className || '');
          const [copies, setCopies] = useState(false);

          const handleCopy = () => {
            navigator.clipboard.writeText(String(children).replace(/\n$/, ''));
            setCopies(true);
            setTimeout(() => setCopies(false), 2000);
          };

          return !inline && match ? (
            <div className="relative group my-4 rounded-lg overflow-hidden border border-slate-700">
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
            <code className="bg-slate-100 text-indigo-600 px-1.5 py-0.5 rounded text-sm font-medium" {...props}>
              {children}
            </code>
          );
        },
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
