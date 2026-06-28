import { useEffect, useState, useCallback } from 'react';
import { summarizeDocument } from '../api/client';

export default function SummaryModal({ filename, onClose, onAskQuestion }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async (refresh = false) => {
    setLoading(true);
    setError(null);
    try {
      setData(await summarizeDocument(filename, refresh));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [filename]);

  useEffect(() => { load(); }, [load]);

  function ask(question) {
    onAskQuestion?.(question);
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4" onClick={onClose}>
      <div
        className="bg-surface rounded-2xl shadow-xl w-full max-w-lg max-h-[85vh] overflow-y-auto animate-fade-in"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-3 border-b border-border sticky top-0 bg-surface">
          <div className="min-w-0">
            <h2 className="text-sm font-semibold text-text-primary truncate">{filename}</h2>
            <p className="text-[11px] text-text-secondary">AI summary{data?.cached ? ' · cached' : ''}</p>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            {data && !loading && (
              <button onClick={() => load(true)} className="text-xs text-text-secondary hover:text-accent transition-colors">
                Regenerate
              </button>
            )}
            <button onClick={onClose} className="text-text-secondary hover:text-text-primary transition-colors">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {loading ? (
          <div className="p-8 text-center text-sm text-text-secondary">
            <div className="w-5 h-5 mx-auto mb-3 border-2 border-accent border-t-transparent rounded-full animate-spin" />
            Summarizing…
          </div>
        ) : error ? (
          <div className="p-8 text-center text-sm text-danger">{error}</div>
        ) : (
          <div className="p-5 space-y-5">
            <p className="text-sm text-text-primary leading-relaxed">{data.summary}</p>

            {data.key_points.length > 0 && (
              <div>
                <p className="text-[11px] font-medium text-text-secondary uppercase tracking-wide mb-2">Key points</p>
                <ul className="space-y-1.5">
                  {data.key_points.map((p, i) => (
                    <li key={i} className="flex gap-2 text-sm text-text-primary">
                      <span className="text-accent mt-0.5">•</span>
                      <span>{p}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {data.suggested_questions.length > 0 && (
              <div>
                <p className="text-[11px] font-medium text-text-secondary uppercase tracking-wide mb-2">Suggested questions</p>
                <div className="flex flex-wrap gap-2">
                  {data.suggested_questions.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => ask(q)}
                      className="text-xs text-left px-3 py-1.5 rounded-lg border border-border text-text-secondary hover:border-accent hover:text-accent transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
