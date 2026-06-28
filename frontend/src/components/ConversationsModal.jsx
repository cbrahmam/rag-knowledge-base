import { useEffect, useState, useCallback } from 'react';
import { listConversations, getConversation, deleteConversation } from '../api/client';

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export default function ConversationsModal({ onClose, onRestore }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [confirmId, setConfirmId] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setItems(await listConversations());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function restore(id) {
    const conv = await getConversation(id);
    onRestore(conv.messages);
    onClose();
  }

  async function remove(id) {
    if (confirmId !== id) {
      setConfirmId(id);
      setTimeout(() => setConfirmId(c => (c === id ? null : c)), 3000);
      return;
    }
    await deleteConversation(id);
    setConfirmId(null);
    await load();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4" onClick={onClose}>
      <div
        className="bg-surface rounded-2xl shadow-xl w-full max-w-lg max-h-[85vh] overflow-y-auto animate-fade-in"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-3 border-b border-border sticky top-0 bg-surface">
          <h2 className="text-sm font-semibold text-text-primary">Saved conversations</h2>
          <button onClick={onClose} className="text-text-secondary hover:text-text-primary transition-colors">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-sm text-text-secondary">Loading…</div>
        ) : items.length === 0 ? (
          <div className="p-8 text-center text-sm text-text-secondary">No saved conversations yet.</div>
        ) : (
          <div className="p-2">
            {items.map(c => (
              <div key={c.id} className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-bg group transition-colors">
                <button onClick={() => restore(c.id)} className="flex-1 min-w-0 text-left">
                  <p className="text-sm font-medium text-text-primary truncate">{c.title}</p>
                  <p className="text-xs text-text-secondary">{c.message_count} messages · {formatDate(c.updated_at)}</p>
                </button>
                <button
                  onClick={() => restore(c.id)}
                  className="opacity-0 group-hover:opacity-100 text-xs px-2 py-1 rounded text-text-secondary hover:text-accent hover:bg-accent/10 transition-all"
                >
                  Open
                </button>
                <button
                  onClick={() => remove(c.id)}
                  className={`opacity-0 group-hover:opacity-100 text-xs px-2 py-1 rounded transition-all ${
                    confirmId === c.id ? 'bg-danger text-white opacity-100' : 'text-text-secondary hover:text-danger hover:bg-danger/10'
                  }`}
                >
                  {confirmId === c.id ? 'Confirm' : 'Delete'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
