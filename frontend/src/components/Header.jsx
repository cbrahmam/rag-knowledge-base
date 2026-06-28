import ThemeToggle from './ThemeToggle';

export default function Header({ stats }) {
  return (
    <header className="h-14 border-b border-border bg-surface flex items-center justify-between px-6">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-accent rounded-lg flex items-center justify-center">
          <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h1 className="text-lg font-semibold text-text-primary">DocuMind</h1>
      </div>
      <div className="flex items-center gap-4 text-sm text-text-secondary">
        <span>{stats.total_documents} documents</span>
        <span className="text-border">|</span>
        <span>{stats.total_chunks} chunks indexed</span>
        <ThemeToggle />
      </div>
    </header>
  );
}
