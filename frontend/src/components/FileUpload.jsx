import { useState, useRef } from 'react';

const ACCEPT_STRING = '.pdf,.docx,.txt,.md';

export default function FileUpload({ onUpload, collections = [] }) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState([]);
  const [collection, setCollection] = useState('General');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [chunkSize, setChunkSize] = useState('');
  const [overlap, setOverlap] = useState('');
  const inputRef = useRef(null);

  function handleDragOver(e) {
    e.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave(e) {
    e.preventDefault();
    setIsDragging(false);
  }

  async function handleFiles(files) {
    const validFiles = Array.from(files).filter(f => {
      const ext = '.' + f.name.split('.').pop().toLowerCase();
      return ['.pdf', '.docx', '.txt', '.md'].includes(ext);
    });

    if (validFiles.length === 0) return;

    setUploading(validFiles.map(f => ({ name: f.name, status: 'uploading' })));

    const target = collection.trim() || 'General';
    const options = {};
    if (chunkSize) options.chunkSize = Number(chunkSize);
    if (overlap) options.overlap = Number(overlap);

    for (let i = 0; i < validFiles.length; i++) {
      try {
        await onUpload(validFiles[i], target, options);
        setUploading(prev =>
          prev.map((item, idx) =>
            idx === i ? { ...item, status: 'done' } : item
          )
        );
      } catch (err) {
        setUploading(prev =>
          prev.map((item, idx) =>
            idx === i ? { ...item, status: 'error', error: err.message } : item
          )
        );
      }
    }

    setTimeout(() => setUploading([]), 4000);
  }

  function handleDrop(e) {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  }

  function handleClick() {
    inputRef.current?.click();
  }

  function handleChange(e) {
    if (e.target.files.length) {
      handleFiles(e.target.files);
      e.target.value = '';
    }
  }

  return (
    <div className="p-3">
      <div className="mb-2">
        <label className="text-[10px] font-medium text-text-secondary uppercase tracking-wide">Collection</label>
        <input
          type="text"
          list="collection-options"
          value={collection}
          onChange={e => setCollection(e.target.value)}
          placeholder="General"
          className="w-full mt-1 text-xs px-3 py-1.5 border border-border rounded-lg bg-bg outline-none focus:border-accent transition-colors placeholder:text-text-secondary/50"
        />
        <datalist id="collection-options">
          {collections.map(c => <option key={c} value={c} />)}
        </datalist>
      </div>

      <div
        onClick={handleClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors ${
          isDragging
            ? 'border-accent bg-accent/5'
            : 'border-border hover:border-accent/50'
        }`}
      >
        <svg className="w-6 h-6 mx-auto mb-2 text-text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
        </svg>
        <p className="text-sm text-text-secondary">Drop files or click to upload</p>
        <p className="text-xs text-text-secondary/60 mt-1">PDF, DOCX, TXT, MD</p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT_STRING}
        multiple
        onChange={handleChange}
        className="hidden"
      />

      <div className="mt-2">
        <button
          onClick={() => setShowAdvanced(s => !s)}
          className="text-[10px] text-text-secondary hover:text-accent transition-colors"
        >
          {showAdvanced ? '▾ Advanced' : '▸ Advanced'}
        </button>
        {showAdvanced && (
          <div className="mt-1.5 grid grid-cols-2 gap-2 animate-fade-in">
            <label className="text-[10px] text-text-secondary">
              Chunk size
              <input
                type="number"
                min="100"
                value={chunkSize}
                onChange={e => setChunkSize(e.target.value)}
                placeholder="auto"
                className="w-full mt-0.5 text-xs px-2 py-1 border border-border rounded bg-bg outline-none focus:border-accent transition-colors"
              />
            </label>
            <label className="text-[10px] text-text-secondary">
              Overlap
              <input
                type="number"
                min="0"
                value={overlap}
                onChange={e => setOverlap(e.target.value)}
                placeholder="auto"
                className="w-full mt-0.5 text-xs px-2 py-1 border border-border rounded bg-bg outline-none focus:border-accent transition-colors"
              />
            </label>
          </div>
        )}
      </div>

      {uploading.length > 0 && (
        <div className="mt-2 space-y-1">
          {uploading.map((item, i) => (
            <div key={i} className="flex items-center gap-2 text-xs px-1">
              {item.status === 'uploading' && (
                <div className="w-3 h-3 border-2 border-accent border-t-transparent rounded-full animate-spin" />
              )}
              {item.status === 'done' && (
                <svg className="w-3 h-3 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              )}
              {item.status === 'error' && (
                <svg className="w-3 h-3 text-danger" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              )}
              <span className="truncate text-text-secondary" title={item.error || item.name}>{item.name}</span>
              {item.status === 'error' && item.error && (
                <span className="text-[10px] text-danger truncate" title={item.error}>{item.error}</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
