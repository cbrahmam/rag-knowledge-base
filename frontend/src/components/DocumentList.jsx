import DocumentCard from './DocumentCard';

export default function DocumentList({ documents, onDelete, onSummarize, onPreview, onMove, onUpdateTags, collections = [] }) {
  if (documents.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <p className="text-sm text-text-secondary text-center">
          No documents yet.<br />Upload files to build your knowledge base.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-1">
      {documents.map(doc => (
        <DocumentCard key={doc.filename} doc={doc} onDelete={onDelete} onSummarize={onSummarize} onPreview={onPreview} onMove={onMove} onUpdateTags={onUpdateTags} collections={collections} />
      ))}
    </div>
  );
}
