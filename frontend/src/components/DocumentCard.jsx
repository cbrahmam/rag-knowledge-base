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

export default function DocumentCard({ doc, onDelete, onSummarize }) {
  const [confirming, setConfirming] = useState(false);

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

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{doc.filename}</p>
        <p className="text-xs text-text-secondary">
          {doc.total_chunks} chunks &middot; {formatBytes(doc.size_bytes)} &middot; {formatDate(doc.uploaded_at)}
        </p>
      </div>

      <div className="flex items-center gap-1">
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
