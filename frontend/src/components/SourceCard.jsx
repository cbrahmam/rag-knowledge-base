import { useState } from 'react';

export default function SourceCard({ source }) {
  const [expanded, setExpanded] = useState(false);
  const score = Math.round(source.relevance_score * 100);

  return (
    <div className="border border-border rounded-lg overflow-hidden transition-all">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-bg/50 transition-colors"
      >
        <svg
          className={`w-3 h-3 text-text-secondary transition-transform ${expanded ? 'rotate-90' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
        <span className="text-xs font-medium text-text-primary truncate flex-1">
          {source.document}
        </span>
        {source.page && (
          <span className="text-[10px] text-text-secondary">p.{source.page}</span>
        )}
        <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full ${
          score >= 70 ? 'bg-green-100 text-green-700' :
          score >= 50 ? 'bg-amber-100 text-amber-700' :
          'bg-red-100 text-red-700'
        }`}>
          {score}%
        </span>
      </button>

      {expanded && (
        <div className="px-3 pb-3 animate-fade-in">
          <p className="text-xs text-text-secondary leading-relaxed bg-bg rounded p-2">
            {source.chunk_text}
          </p>
        </div>
      )}
    </div>
  );
}
