import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import SourceCard from './SourceCard';

const CONFIDENCE_STYLES = {
  high: 'bg-green-100 text-green-700',
  medium: 'bg-amber-100 text-amber-700',
  low: 'bg-red-100 text-red-700',
};

export default function ChatMessage({ message }) {
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
            {message.isStreaming && (
              <span className="inline-block w-1.5 h-4 ml-0.5 align-middle bg-accent/70 rounded-sm animate-pulse" />
            )}
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
