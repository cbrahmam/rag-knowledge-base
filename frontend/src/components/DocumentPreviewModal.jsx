import { useEffect, useState } from 'react';
import { getDocumentContent } from '../api/client';

export default function DocumentPreviewModal({ filename, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    getDocumentContent(filename)
      .then(d => { if (active) setData(d); })
      .catch(err => { if (active) setError(err.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [filename]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4" onClick={onClose}>
      <div
        className="bg-surface rounded-2xl shadow-xl w-full max-w-2xl max-h-[85vh] flex flex-col animate-fade-in"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-3 border-b border-border">
          <div className="min-w-0">
            <h2 className="text-sm font-semibold text-text-primary truncate">{filename}</h2>
            {data && (
              <p className="text-[11px] text-text-secondary">
                {data.file_type.toUpperCase()} · {data.total_characters.toLocaleString()} chars
                {data.total_pages ? ` · ${data.total_pages} pages` : ''}
              </p>
            )}
          </div>
          <button onClick={onClose} className="text-text-secondary hover:text-text-primary transition-colors shrink-0">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          {loading ? (
            <div className="py-8 text-center text-sm text-text-secondary">Loading…</div>
          ) : error ? (
            <div className="py-8 text-center text-sm text-danger">{error}</div>
          ) : (
            <pre className="text-xs text-text-primary whitespace-pre-wrap break-words font-mono leading-relaxed">
              {data.content}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
