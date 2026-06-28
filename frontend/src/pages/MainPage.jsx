import { useState, useEffect, useCallback } from 'react';
import Layout from '../components/Layout';
import Sidebar from '../components/Sidebar';
import ChatInterface from '../components/ChatInterface';
import ConversationsModal from '../components/ConversationsModal';
import useChat from '../hooks/useChat';
import { uploadDocument, listDocuments, deleteDocument, getStats, loadSampleDocs, saveConversation } from '../api/client';

export default function MainPage() {
  const [documents, setDocuments] = useState([]);
  const [stats, setStats] = useState({ total_documents: 0, total_chunks: 0 });
  const [showConversations, setShowConversations] = useState(false);
  const { messages, isLoading, sendMessage, clearChat, loadMessages } = useChat();

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

  async function handleSaveConversation() {
    if (messages.length === 0) return;
    await saveConversation(messages);
  }

  return (
    <Layout
      stats={stats}
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
        onSave={handleSaveConversation}
        onOpenSaved={() => setShowConversations(true)}
      />
      {showConversations && (
        <ConversationsModal
          onClose={() => setShowConversations(false)}
          onRestore={loadMessages}
        />
      )}
    </Layout>
  );
}
