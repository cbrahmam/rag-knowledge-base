import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { askMultiple } from '../api/client';

const CONFIDENCE_STYLES = {
  high: 'bg-green-100 text-green-700',
  medium: 'bg-amber-100 text-amber-700',
  low: 'bg-red-100 text-red-700',
};

export default function BatchQuestionsModal({ onClose }) {
  const [text, setText] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const questions = text.split('\n').map(q => q.trim()).filter(Boolean).slice(0, 5);

  async function run() {
    if (questions.length === 0) return;
    setLoading(true);
    setError(null);
    try {
      const res = await askMultiple(questions);
      setResults(res.map((r, i) => ({ question: questions[i], ...r })));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4" onClick={onClose}>
      <div
        className="bg-surface rounded-2xl shadow-xl w-full max-w-2xl max-h-[85vh] flex flex-col animate-fade-in"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-3 border-b border-border">
          <h2 className="text-sm font-semibold text-text-primary">Batch questions</h2>
          <button onClick={onClose} className="text-text-secondary hover:text-text-primary transition-colors">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          <div>
            <p className="text-[11px] text-text-secondary mb-1.5">One question per line (up to 5).</p>
            <textarea
              value={text}
              onChange={e => setText(e.target.value)}
              rows={4}
              placeholder={"What is the vacation policy?\nWho approves expenses?"}
              className="w-full text-sm px-3 py-2 border border-border rounded-lg bg-bg outline-none focus:border-accent transition-colors resize-y"
            />
            <div className="flex items-center justify-between mt-2">
              <span className="text-[11px] text-text-secondary">{questions.length}/5 questions</span>
              <button
                onClick={run}
                disabled={loading || questions.length === 0}
                className="text-xs px-3 py-1.5 rounded-lg bg-accent text-white disabled:opacity-40 hover:bg-accent-hover transition-colors"
              >
                {loading ? 'Asking…' : 'Ask all'}
              </button>
            </div>
          </div>

          {error && <p className="text-sm text-danger">{error}</p>}

          {results && results.map((r, i) => (
            <div key={i} className="border border-border rounded-lg p-3 space-y-1.5">
              <p className="text-sm font-medium text-text-primary">{r.question}</p>
              <div className="text-sm prose prose-sm max-w-none prose-p:my-1">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{r.answer}</ReactMarkdown>
              </div>
              <div className="flex items-center gap-2">
                {r.confidence && (
                  <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${CONFIDENCE_STYLES[r.confidence]}`}>
                    {r.confidence} confidence
                  </span>
                )}
                {r.sources?.length > 0 && (
                  <span className="text-[10px] text-text-secondary">{r.sources.length} sources</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
