import { useEffect, useState, useCallback } from 'react';
import { getAnalytics, clearQueryHistory } from '../api/client';

const CONFIDENCE_COLORS = {
  high: 'bg-green-500',
  medium: 'bg-amber-500',
  low: 'bg-red-500',
};

function StatCard({ label, value, sub }) {
  return (
    <div className="border border-border rounded-lg p-3 bg-bg">
      <p className="text-2xl font-semibold text-text-primary">{value}</p>
      <p className="text-[11px] text-text-secondary mt-0.5">{label}</p>
      {sub && <p className="text-[10px] text-text-secondary/70">{sub}</p>}
    </div>
  );
}

export default function AnalyticsPanel({ onClose, onAskQuestion }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [clearing, setClearing] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await getAnalytics());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleClear() {
    setClearing(true);
    try {
      await clearQueryHistory();
      await load();
    } finally {
      setClearing(false);
    }
  }

  const dist = data?.confidence_distribution || { high: 0, medium: 0, low: 0 };
  const distTotal = (dist.high || 0) + (dist.medium || 0) + (dist.low || 0);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4" onClick={onClose}>
      <div
        className="bg-surface rounded-2xl shadow-xl w-full max-w-lg max-h-[85vh] overflow-y-auto animate-fade-in"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-3 border-b border-border sticky top-0 bg-surface">
          <h2 className="text-sm font-semibold text-text-primary">Query Analytics</h2>
          <button onClick={onClose} className="text-text-secondary hover:text-text-primary transition-colors">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {loading ? (
          <div className="p-8 text-center text-sm text-text-secondary">Loading…</div>
        ) : !data || data.total_queries === 0 ? (
          <div className="p-8 text-center text-sm text-text-secondary">No queries yet. Ask a question to see analytics.</div>
        ) : (
          <div className="p-5 space-y-5">
            <div className="grid grid-cols-3 gap-3">
              <StatCard label="Total queries" value={data.total_queries} />
              <StatCard label="Avg response" value={`${(data.avg_processing_time_ms / 1000).toFixed(1)}s`} />
              <StatCard label="Avg sources" value={data.avg_source_count} />
            </div>

            <div>
              <p className="text-[11px] font-medium text-text-secondary uppercase tracking-wide mb-2">Confidence distribution</p>
              <div className="space-y-1.5">
                {['high', 'medium', 'low'].map(level => {
                  const count = dist[level] || 0;
                  const pct = distTotal ? Math.round((count / distTotal) * 100) : 0;
                  return (
                    <div key={level} className="flex items-center gap-2">
                      <span className="w-14 text-xs text-text-secondary capitalize">{level}</span>
                      <div className="flex-1 h-2 bg-bg rounded-full overflow-hidden">
                        <div className={`h-full ${CONFIDENCE_COLORS[level]} transition-all`} style={{ width: `${pct}%` }} />
                      </div>
                      <span className="w-10 text-right text-xs text-text-secondary">{count}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div>
              <p className="text-[11px] font-medium text-text-secondary uppercase tracking-wide mb-2">
                Recent questions{onAskQuestion ? ' · click to re-ask' : ''}
              </p>
              <div className="space-y-1">
                {data.recent.map((r, i) => {
                  const Row = onAskQuestion ? 'button' : 'div';
                  return (
                    <Row
                      key={i}
                      onClick={onAskQuestion ? () => { onAskQuestion(r.question); onClose(); } : undefined}
                      title={onAskQuestion ? 'Re-ask this question' : undefined}
                      className={`w-full flex items-center gap-2 text-xs px-2 py-1.5 rounded-lg transition-colors text-left ${
                        onAskQuestion ? 'hover:bg-accent/10 hover:text-accent cursor-pointer' : 'hover:bg-bg'
                      }`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${CONFIDENCE_COLORS[r.confidence]}`} />
                      <span className="flex-1 truncate text-text-primary">{r.question}</span>
                      <span className="text-text-secondary/70 shrink-0">{(r.processing_time_ms / 1000).toFixed(1)}s</span>
                    </Row>
                  );
                })}
              </div>
            </div>

            <div className="flex justify-end pt-2 border-t border-border">
              <button
                onClick={handleClear}
                disabled={clearing}
                className="text-xs text-text-secondary hover:text-danger transition-colors disabled:opacity-50"
              >
                {clearing ? 'Clearing…' : 'Clear history'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
