import { useState } from 'react';
import FileUpload from './FileUpload';
import DocumentList from './DocumentList';

export default function Sidebar({ documents, stats, onUpload, onDelete, onLoadSamples, onSummarize }) {
  const [search, setSearch] = useState('');
  const [loadingSamples, setLoadingSamples] = useState(false);

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

      <FileUpload onUpload={onUpload} />

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

      <DocumentList documents={filtered} onDelete={onDelete} onSummarize={onSummarize} />

      {search && filtered.length === 0 && (
        <div className="px-3 pb-3">
          <p className="text-xs text-text-secondary text-center">No documents match "{search}"</p>
        </div>
      )}

      <div className="border-t border-border p-3">
        <div className="flex items-center justify-between text-xs text-text-secondary">
          <span>{stats.total_documents} docs &middot; {stats.total_chunks} chunks</span>
          <span className={stats.total_chunks > 0 ? 'text-success' : 'text-warning'}>
            {stats.total_chunks > 0 ? 'Ready' : 'Empty'}
          </span>
        </div>
      </div>
    </aside>
  );
}
