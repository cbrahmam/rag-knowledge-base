import { useState } from 'react';
import FileUpload from './FileUpload';
import DocumentList from './DocumentList';
import { exportKnowledgeBase } from '../api/client';

export default function Sidebar({
  documents,
  collections = [],
  activeCollection = null,
  onSelectCollection,
  stats,
  onUpload,
  onDelete,
  onLoadSamples,
  onSummarize,
  onPreview,
  onMove,
  onUpdateTags,
  onReindex,
  onRenameCollection,
  onDeleteCollection,
}) {
  const [search, setSearch] = useState('');
  const [loadingSamples, setLoadingSamples] = useState(false);
  const [renaming, setRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState('');
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [exporting, setExporting] = useState(false);
  const collectionNames = collections.map(c => c.name);

  async function handleExport() {
    setExporting(true);
    try {
      const data = await exportKnowledgeBase();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `documind-kb-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  }

  const filtered = search
    ? documents.filter(d => d.filename.toLowerCase().includes(search.toLowerCase()))
    : documents;

  async function handleLoadSamples() {
    setLoadingSamples(true);
    try {
      await onLoadSamples();
    } finally {
      setLoadingSamples(false);
    }
  }

  return (
    <aside className="w-[320px] border-r border-border bg-surface flex flex-col shrink-0">
      <div className="p-3 border-b border-border flex items-center justify-between">
        <h2 className="text-sm font-semibold text-text-primary">Documents</h2>
        {documents.length === 0 && (
          <button
            onClick={handleLoadSamples}
            disabled={loadingSamples}
            className="text-[10px] px-2 py-1 rounded bg-accent/10 text-accent hover:bg-accent/20 transition-colors disabled:opacity-50"
          >
            {loadingSamples ? 'Loading...' : 'Load Samples'}
          </button>
        )}
      </div>

      <FileUpload onUpload={onUpload} collections={collectionNames} />

      {collections.length > 0 && (
        <div className="px-3 pb-2">
          <select
            value={activeCollection || ''}
            onChange={e => onSelectCollection?.(e.target.value || null)}
            className="w-full text-xs px-3 py-1.5 border border-border rounded-lg bg-bg outline-none focus:border-accent transition-colors text-text-primary"
          >
            <option value="">All collections</option>
            {collections.map(c => (
              <option key={c.name} value={c.name}>
                {c.name} ({c.document_count})
              </option>
            ))}
          </select>

          {activeCollection && activeCollection !== 'General' && (
            renaming ? (
              <div className="mt-1.5 flex items-center gap-1.5">
                <input
                  autoFocus
                  value={renameValue}
                  onChange={e => setRenameValue(e.target.value)}
                  onKeyDown={e => {
                    if (e.key === 'Enter' && renameValue.trim()) { onRenameCollection?.(activeCollection, renameValue.trim()); setRenaming(false); }
                    if (e.key === 'Escape') setRenaming(false);
                  }}
                  placeholder="New name"
                  className="flex-1 text-[11px] px-2 py-1 border border-border rounded bg-bg outline-none focus:border-accent transition-colors"
                />
                <button onClick={() => { if (renameValue.trim()) { onRenameCollection?.(activeCollection, renameValue.trim()); setRenaming(false); } }} className="text-[11px] text-accent">Save</button>
              </div>
            ) : (
              <div className="mt-1.5 flex items-center gap-3 px-0.5">
                <button
                  onClick={() => { setRenameValue(activeCollection); setRenaming(true); }}
                  className="text-[10px] text-text-secondary hover:text-accent transition-colors"
                >
                  Rename
                </button>
                <button
                  onClick={() => {
                    if (confirmDelete) { onDeleteCollection?.(activeCollection); setConfirmDelete(false); }
                    else { setConfirmDelete(true); setTimeout(() => setConfirmDelete(false), 3000); }
                  }}
                  className={`text-[10px] transition-colors ${confirmDelete ? 'text-danger font-medium' : 'text-text-secondary hover:text-danger'}`}
                >
                  {confirmDelete ? 'Confirm delete' : 'Delete'}
                </button>
              </div>
            )
          )}
        </div>
      )}

      {documents.length > 3 && (
        <div className="px-3 pb-2">
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search documents..."
            className="w-full text-xs px-3 py-1.5 border border-border rounded-lg bg-bg outline-none focus:border-accent transition-colors placeholder:text-text-secondary/50"
          />
        </div>
      )}

      <div className="border-t border-border" />

      <DocumentList documents={filtered} onDelete={onDelete} onSummarize={onSummarize} onPreview={onPreview} onMove={onMove} onUpdateTags={onUpdateTags} onReindex={onReindex} collections={collectionNames} />

      {search && filtered.length === 0 && (
        <div className="px-3 pb-3">
          <p className="text-xs text-text-secondary text-center">No documents match "{search}"</p>
        </div>
      )}

      <div className="border-t border-border p-3 space-y-2">
        <div className="flex items-center justify-between text-xs text-text-secondary">
          <span>{stats.total_documents} docs &middot; {stats.total_chunks} chunks</span>
          <span className={stats.total_chunks > 0 ? 'text-success' : 'text-warning'}>
            {stats.total_chunks > 0 ? 'Ready' : 'Empty'}
          </span>
        </div>
        {stats.total_documents > 0 && (
          <button
            onClick={handleExport}
            disabled={exporting}
            className="w-full text-[11px] py-1 rounded-lg border border-border text-text-secondary hover:border-accent hover:text-accent transition-colors disabled:opacity-50"
          >
            {exporting ? 'Exporting…' : 'Export knowledge base'}
          </button>
        )}
      </div>
    </aside>
  );
}
