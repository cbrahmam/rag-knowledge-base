import { useRef, useEffect, useState } from 'react';
import ChatMessage from './ChatMessage';

const SUGGESTED_QUESTIONS = [
  "What are the main topics covered in these documents?",
  "Summarize the key points across all documents",
  "Are there any deadlines or important dates mentioned?",
];

const SEARCH_MODES = [
  { id: 'hybrid', label: 'Hybrid', hint: 'Semantic + keyword (best overall)' },
  { id: 'semantic', label: 'Semantic', hint: 'Meaning-based vector search' },
  { id: 'keyword', label: 'Keyword', hint: 'Exact term BM25 search' },
];

export default function ChatInterface({ messages, isLoading, onSend, onClear, hasDocuments, activeCollection = null }) {
  const [input, setInput] = useState('');
  const [toast, setToast] = useState(null);
  const [searchMode, setSearchMode] = useState('hybrid');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  function handleSubmit(e) {
    e.preventDefault();
    if (!input.trim() || isLoading || !hasDocuments) return;
    onSend(input.trim(), searchMode);
    setInput('');
  }

  function handleSuggestion(question) {
    onSend(question, searchMode);
  }

  function showToast(msg) {
    setToast(msg);
    setTimeout(() => setToast(null), 2500);
  }

  function exportChat() {
    const lines = messages.map(m => {
      if (m.role === 'user') return `**You:** ${m.content}`;
      let text = `**DocuMind:** ${m.content}`;
      if (m.sources?.length) {
        text += '\n\n_Sources:_\n' + m.sources.map(s =>
          `- ${s.document}${s.page ? ` (p.${s.page})` : ''} — ${Math.round(s.relevance_score * 100)}% relevance`
        ).join('\n');
      }
      return text;
    });
    const md = `# DocuMind Conversation\n\n${lines.join('\n\n---\n\n')}\n`;

    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `documind-chat-${new Date().toISOString().slice(0, 10)}.md`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Chat exported');
  }

  function copyChat() {
    const lines = messages.map(m => {
      if (m.role === 'user') return `You: ${m.content}`;
      return `DocuMind: ${m.content}`;
    });
    navigator.clipboard.writeText(lines.join('\n\n')).then(() => showToast('Copied to clipboard'));
  }

  const showSuggestions = hasDocuments && messages.length === 0;

  return (
    <div className="flex-1 flex flex-col overflow-hidden relative">
      <div className="flex items-center justify-between px-6 py-2 border-b border-border">
        <div className="flex items-center gap-3">
          <h2 className="text-sm font-semibold text-text-primary">Chat</h2>
          <div className="flex items-center rounded-lg border border-border p-0.5 bg-bg">
            {SEARCH_MODES.map(mode => (
              <button
                key={mode.id}
                onClick={() => setSearchMode(mode.id)}
                title={mode.hint}
                className={`text-[10px] px-2 py-0.5 rounded-md transition-colors ${
                  searchMode === mode.id
                    ? 'bg-accent text-white'
                    : 'text-text-secondary hover:text-accent'
                }`}
              >
                {mode.label}
              </button>
            ))}
          </div>
          {activeCollection && (
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-accent/10 text-accent">
              scoped to {activeCollection}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {messages.length > 0 && (
            <>
              <button onClick={copyChat} className="text-xs text-text-secondary hover:text-accent transition-colors">Copy</button>
              <button onClick={exportChat} className="text-xs text-text-secondary hover:text-accent transition-colors">Export</button>
              <button onClick={onClear} className="text-xs text-text-secondary hover:text-danger transition-colors">Clear</button>
            </>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {!hasDocuments && (
          <div className="flex-1 flex items-center justify-center h-full">
            <div className="text-center">
              <svg className="w-12 h-12 mx-auto mb-4 text-border" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="text-sm text-text-secondary">Upload documents to start asking questions</p>
            </div>
          </div>
        )}

        {showSuggestions && (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center space-y-4">
              <svg className="w-10 h-10 mx-auto text-accent/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              <p className="text-sm text-text-secondary">Ask anything about your documents</p>
              <div className="flex flex-wrap justify-center gap-2 max-w-md">
                {SUGGESTED_QUESTIONS.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => handleSuggestion(q)}
                    className="text-xs px-3 py-1.5 rounded-full border border-border text-text-secondary hover:border-accent hover:text-accent transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} question={i > 0 ? messages[i - 1].content : ''} />
        ))}

        {isLoading && messages[messages.length - 1]?.role !== 'assistant' && (
          <div className="flex justify-start animate-fade-in">
            <div className="bg-surface border border-border rounded-2xl rounded-bl-md px-4 py-3">
              <div className="flex items-center gap-1">
                <div className="w-2 h-2 bg-text-secondary/40 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-text-secondary/40 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-text-secondary/40 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {toast && (
        <div className="absolute top-16 right-6 bg-text-primary text-white text-xs px-3 py-2 rounded-lg shadow-lg animate-fade-in z-50">
          {toast}
        </div>
      )}

      <form onSubmit={handleSubmit} className="border-t border-border p-4">
        <div className="flex items-center gap-3 bg-surface border border-border rounded-xl px-4 py-2 focus-within:border-accent transition-colors shadow-sm">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder={hasDocuments ? "Ask anything about your documents..." : "Upload documents to start..."}
            disabled={!hasDocuments || isLoading}
            className="flex-1 bg-transparent outline-none text-sm text-text-primary placeholder:text-text-secondary/50 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading || !hasDocuments}
            className="p-1.5 rounded-lg bg-accent text-white disabled:opacity-30 hover:bg-accent-hover transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
          </button>
        </div>
      </form>
    </div>
  );
}
