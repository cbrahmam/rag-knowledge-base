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

export default function DocumentCard({ doc, onDelete, onSummarize, onPreview, onMove, onUpdateTags, collections = [] }) {
  const [confirming, setConfirming] = useState(false);
  const [editingTags, setEditingTags] = useState(false);
  const [tagInput, setTagInput] = useState((doc.tags || []).join(', '));

  const moveTargets = collections.filter(c => c !== doc.collection);
  const tags = doc.tags || [];

  function handleDelete() {
    if (confirming) {
      onDelete(doc.filename);
      setConfirming(false);
    } else {
      setConfirming(true);
      setTimeout(() => setConfirming(false), 3000);
    }
  }

  function saveTags() {
    const parsed = tagInput.split(',').map(t => t.trim()).filter(Boolean);
    onUpdateTags?.(doc.filename, parsed);
    setEditingTags(false);
  }

  return (
    <div className="px-3 py-2 hover:bg-bg rounded-lg group transition-colors animate-fade-in">
      <div className="flex items-center gap-3">
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
          {onUpdateTags && (
            <button
              onClick={() => { setTagInput(tags.join(', ')); setEditingTags(v => !v); }}
              title="Edit tags"
              className="opacity-0 group-hover:opacity-100 text-xs px-2 py-1 rounded transition-all text-text-secondary hover:text-accent hover:bg-accent/10"
            >
              Tags
            </button>
          )}
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

      {editingTags ? (
        <div className="mt-1.5 flex items-center gap-2 pl-9">
          <input
            autoFocus
            value={tagInput}
            onChange={e => setTagInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') saveTags(); if (e.key === 'Escape') setEditingTags(false); }}
            placeholder="comma, separated, tags"
            className="flex-1 text-[11px] px-2 py-1 border border-border rounded bg-bg outline-none focus:border-accent transition-colors"
          />
          <button onClick={saveTags} className="text-[11px] text-accent hover:text-accent-hover">Save</button>
        </div>
      ) : tags.length > 0 && (
        <div className="mt-1 flex flex-wrap gap-1 pl-9">
          {tags.map(t => (
            <span key={t} className="text-[9px] px-1.5 py-0.5 rounded-full bg-border/50 text-text-secondary">#{t}</span>
          ))}
        </div>
      )}
    </div>
  );
}
