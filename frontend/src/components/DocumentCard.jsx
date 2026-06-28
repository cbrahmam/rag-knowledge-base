import { useState } from 'react';

const TYPE_COLORS = {
  pdf: 'bg-red-100 text-red-700',
  docx: 'bg-blue-100 text-blue-700',
  txt: 'bg-gray-100 text-gray-700',
  md: 'bg-purple-100 text-purple-700',
};

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export default function DocumentCard({ doc, onDelete, onSummarize, onPreview, onMove, collections = [] }) {
  const [confirming, setConfirming] = useState(false);

  const moveTargets = collections.filter(c => c !== doc.collection);

  function handleDelete() {
    if (confirming) {
      onDelete(doc.filename);
      setConfirming(false);
    } else {
      setConfirming(true);
      setTimeout(() => setConfirming(false), 3000);
    }
  }

  return (
    <div className="flex items-center gap-3 px-3 py-2 hover:bg-bg rounded-lg group transition-colors animate-fade-in">
      <span className={`text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded ${TYPE_COLORS[doc.file_type] || TYPE_COLORS.txt}`}>
        {doc.file_type}
      </span>

      <button
        onClick={() => onPreview?.(doc.filename)}
        disabled={!onPreview}
        title={onPreview ? 'Preview document' : undefined}
        className="flex-1 min-w-0 text-left disabled:cursor-default"
      >
        <div className="flex items-center gap-1.5">
          <p className={`text-sm font-medium truncate ${onPreview ? 'group-hover:text-accent transition-colors' : ''}`}>
            {doc.filename}
          </p>
          {doc.collection && (
            <span className="shrink-0 text-[9px] px-1.5 py-0.5 rounded-full bg-accent/10 text-accent">
              {doc.collection}
            </span>
          )}
        </div>
        <p className="text-xs text-text-secondary">
          {doc.total_chunks} chunks &middot; {formatBytes(doc.size_bytes)} &middot; {formatDate(doc.uploaded_at)}
        </p>
      </button>

      <div className="flex items-center gap-1">
        {onMove && moveTargets.length > 0 && (
          <select
            value=""
            onChange={e => { if (e.target.value) onMove(doc.filename, e.target.value); }}
            title="Move to collection"
            className="opacity-0 group-hover:opacity-100 text-[10px] px-1 py-1 rounded border border-border bg-bg text-text-secondary outline-none focus:border-accent transition-all"
          >
            <option value="">Move…</option>
            {moveTargets.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        )}
        {onSummarize && (
          <button
            onClick={() => onSummarize(doc.filename)}
            title="AI summary"
            className="opacity-0 group-hover:opacity-100 text-xs px-2 py-1 rounded transition-all text-text-secondary hover:text-accent hover:bg-accent/10"
          >
            Summary
          </button>
        )}
        <button
          onClick={handleDelete}
          className={`opacity-0 group-hover:opacity-100 text-xs px-2 py-1 rounded transition-all ${
            confirming
              ? 'bg-danger text-white opacity-100'
              : 'text-text-secondary hover:text-danger hover:bg-danger/10'
          }`}
        >
          {confirming ? 'Confirm' : 'Delete'}
        </button>
      </div>
    </div>
  );
}
