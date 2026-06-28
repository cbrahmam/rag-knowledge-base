import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import SourceCard from './SourceCard';
import { submitFeedback } from '../api/client';

const CONFIDENCE_STYLES = {
  high: 'bg-green-100 text-green-700',
  medium: 'bg-amber-100 text-amber-700',
  low: 'bg-red-100 text-red-700',
};

function FeedbackButtons({ question, message }) {
  const [rating, setRating] = useState(null);

  function rate(value) {
    if (rating) return; // one rating per answer
    setRating(value);
    submitFeedback({
      question: question || '',
      answer: message.content,
      rating: value,
      confidence: message.confidence,
    }).catch(() => setRating(null)); // allow retry if the call fails
  }

  return (
    <div className="flex items-center gap-1">
      <button
        onClick={() => rate('up')}
        disabled={!!rating}
        title="Helpful"
        className={`p-1 rounded transition-colors ${
          rating === 'up' ? 'text-success' : 'text-text-secondary/50 hover:text-success'
        } disabled:cursor-default`}
      >
        <svg className="w-3.5 h-3.5" fill={rating === 'up' ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6.633 10.5c.806 0 1.533-.446 2.031-1.08a9.041 9.041 0 012.861-2.4c.723-.384 1.35-.956 1.653-1.715a4.498 4.498 0 00.322-1.672V3a.75.75 0 01.75-.75A2.25 2.25 0 0116.5 4.5c0 1.152-.26 2.243-.723 3.218-.266.558.107 1.282.725 1.282h3.126c1.026 0 1.945.694 2.054 1.715.045.422.068.85.068 1.285a11.95 11.95 0 01-2.649 7.521c-.388.482-.987.729-1.605.729H13.48c-.483 0-.964-.078-1.423-.23l-3.114-1.04a4.501 4.501 0 00-1.423-.23H5.904M14 9h-3m-6.633 1.5H4.5a2.25 2.25 0 00-2.25 2.25v6.75A2.25 2.25 0 004.5 21.75h.75" />
        </svg>
      </button>
      <button
        onClick={() => rate('down')}
        disabled={!!rating}
        title="Not helpful"
        className={`p-1 rounded transition-colors ${
          rating === 'down' ? 'text-danger' : 'text-text-secondary/50 hover:text-danger'
        } disabled:cursor-default`}
      >
        <svg className="w-3.5 h-3.5" fill={rating === 'down' ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 15h2.25m8.024-9.75c.011.05.028.1.052.148.591 1.2.924 2.55.924 3.977a8.96 8.96 0 01-.999 4.125m.023-8.25c-.076-.365.183-.75.575-.75h.908c.889 0 1.713.518 1.972 1.368.339 1.11.521 2.287.521 3.507 0 1.553-.295 3.036-.831 4.398C20.613 14.547 19.833 15 19 15h-1.053c-.472 0-.745-.556-.5-.96a8.95 8.95 0 00.303-.54m-1.25-9.75H8.706c-.97 0-1.75.78-1.75 1.75v.5m9.546 8.5l-3.114 1.04a4.501 4.501 0 01-1.423.23h-.91m-3.25-3.5l-1.5-1.5" />
        </svg>
      </button>
    </div>
  );
}

export default function ChatMessage({ message, question }) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end animate-fade-in">
        <div className="max-w-[70%] bg-accent text-white rounded-2xl rounded-br-md px-4 py-2.5">
          <p className="text-sm">{message.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start animate-fade-in">
      <div className="max-w-[80%] space-y-2">
        <div className={`rounded-2xl rounded-bl-md px-4 py-3 ${
          message.isError ? 'bg-red-50 border border-red-200' : 'bg-surface border border-border'
        }`}>
          <div className="text-sm prose prose-sm max-w-none prose-p:my-1 prose-headings:my-2 prose-ul:my-1 prose-ol:my-1">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  if (!inline && match) {
                    return (
                      <SyntaxHighlighter
                        style={oneLight}
                        language={match[1]}
                        PreTag="div"
                        customStyle={{ fontSize: '12px', borderRadius: '8px', margin: '8px 0' }}
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    );
                  }
                  return (
                    <code className="bg-bg px-1 py-0.5 rounded text-xs" {...props}>
                      {children}
                    </code>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        </div>

        {message.confidence && (
          <div className="flex items-center gap-3 px-1">
            <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${CONFIDENCE_STYLES[message.confidence]}`}>
              {message.confidence} confidence
            </span>
            {message.processingTime && (
              <span className="text-[10px] text-text-secondary">
                {(message.processingTime / 1000).toFixed(1)}s
              </span>
            )}
            {!message.isError && <FeedbackButtons question={question} message={message} />}
          </div>
        )}

        {message.sources && message.sources.length > 0 && (
          <div className="space-y-1">
            <p className="text-[10px] font-medium text-text-secondary uppercase tracking-wide px-1">Sources</p>
            {message.sources.map((source, i) => (
              <SourceCard key={i} source={source} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
