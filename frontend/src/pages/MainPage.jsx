import { useState, useEffect, useCallback } from 'react';
import Layout from '../components/Layout';
import Sidebar from '../components/Sidebar';
import ChatInterface from '../components/ChatInterface';
import useChat from '../hooks/useChat';
import {
  uploadDocument,
  listDocuments,
  deleteDocument,
  getStats,
  loadSampleDocs,
  listCollections,
} from '../api/client';

export default function MainPage() {
  const [documents, setDocuments] = useState([]);
  const [collections, setCollections] = useState([]);
  const [activeCollection, setActiveCollection] = useState(null); // null = All
  const [stats, setStats] = useState({ total_documents: 0, total_chunks: 0 });
  const { messages, isLoading, sendMessage, clearChat } = useChat();

  const refresh = useCallback(async () => {
    const [docs, st, cols] = await Promise.all([listDocuments(), getStats(), listCollections()]);
    setDocuments(docs);
    setStats(st);
    setCollections(cols);
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  // Scope each question to the active collection (null = search everything),
  // forwarding the search mode chosen in the chat header.
  const handleSend = useCallback(
    (question, searchMode = 'hybrid') => sendMessage(question, { searchMode, collection: activeCollection }),
    [sendMessage, activeCollection],
  );

  const visibleDocuments = activeCollection
    ? documents.filter(d => d.collection === activeCollection)
    : documents;

  async function handleUpload(file, collection) {
    await uploadDocument(file, collection);
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
      sidebar={
        <Sidebar
          documents={visibleDocuments}
          collections={collections}
          activeCollection={activeCollection}
          onSelectCollection={setActiveCollection}
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
        onSend={handleSend}
        onClear={clearChat}
        hasDocuments={stats.total_chunks > 0}
        activeCollection={activeCollection}
      />
    </Layout>
  );
}
