import Header from './Header';

export default function Layout({ stats, sidebar, children }) {
  return (
    <div className="h-screen flex flex-col">
      <Header stats={stats} />
      <div className="flex-1 flex overflow-hidden">
        {sidebar}
        <main className="flex-1 flex flex-col overflow-hidden bg-bg">
          {children}
        </main>
      </div>
    </div>
  );
}
