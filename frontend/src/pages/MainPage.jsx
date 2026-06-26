import { useState, useEffect, useCallback } from 'react';
import Layout from '../components/Layout';
import Sidebar from '../components/Sidebar';
import ChatInterface from '../components/ChatInterface';
import AnalyticsPanel from '../components/AnalyticsPanel';
import useChat from '../hooks/useChat';
import { uploadDocument, listDocuments, deleteDocument, getStats, loadSampleDocs } from '../api/client';

export default function MainPage() {
  const [documents, setDocuments] = useState([]);
  const [stats, setStats] = useState({ total_documents: 0, total_chunks: 0 });
  const [showAnalytics, setShowAnalytics] = useState(false);
  const { messages, isLoading, sendMessage, clearChat } = useChat();

  const refresh = useCallback(async () => {
    const [docs, st] = await Promise.all([listDocuments(), getStats()]);
    setDocuments(docs);
    setStats(st);
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  async function handleUpload(file) {
    await uploadDocument(file);
    await refresh();
  }

  async function handleDelete(filename) {
    await deleteDocument(filename);
    await refresh();
  }

  async function handleLoadSamples() {
    await loadSampleDocs();
    await refresh();
  }

  return (
    <Layout
      stats={stats}
      onOpenAnalytics={() => setShowAnalytics(true)}
      sidebar={
        <Sidebar
          documents={documents}
          stats={stats}
          onUpload={handleUpload}
          onDelete={handleDelete}
          onLoadSamples={handleLoadSamples}
        />
      }
    >
      <ChatInterface
        messages={messages}
        isLoading={isLoading}
        onSend={sendMessage}
        onClear={clearChat}
        hasDocuments={stats.total_chunks > 0}
      />
      {showAnalytics && <AnalyticsPanel onClose={() => setShowAnalytics(false)} />}
    </Layout>
  );
}
