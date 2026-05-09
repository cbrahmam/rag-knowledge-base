import FileUpload from './FileUpload';
import DocumentList from './DocumentList';

export default function Sidebar({ documents, stats, onUpload, onDelete }) {
  return (
    <aside className="w-[320px] border-r border-border bg-surface flex flex-col">
      <div className="p-3 border-b border-border">
        <h2 className="text-sm font-semibold text-text-primary">Documents</h2>
      </div>

      <FileUpload onUpload={onUpload} />

      <div className="border-t border-border" />

      <DocumentList documents={documents} onDelete={onDelete} />

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
