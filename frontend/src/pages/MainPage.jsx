import { useState, useEffect, useCallback } from 'react';
import Layout from '../components/Layout';
import Sidebar from '../components/Sidebar';
import ChatInterface from '../components/ChatInterface';
import AnalyticsPanel from '../components/AnalyticsPanel';
import SummaryModal from '../components/SummaryModal';
import ConversationsModal from '../components/ConversationsModal';
import DocumentPreviewModal from '../components/DocumentPreviewModal';
import BatchQuestionsModal from '../components/BatchQuestionsModal';
import useChat from '../hooks/useChat';
import {
  uploadDocument,
  listDocuments,
  deleteDocument,
  getStats,
  loadSampleDocs,
  listCollections,
  saveConversation,
  moveDocument,
  updateTags,
} from '../api/client';

export default function MainPage() {
  const [documents, setDocuments] = useState([]);
  const [collections, setCollections] = useState([]);
  const [activeCollection, setActiveCollection] = useState(null); // null = All
  const [stats, setStats] = useState({ total_documents: 0, total_chunks: 0 });
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [summaryFor, setSummaryFor] = useState(null);
  const [showConversations, setShowConversations] = useState(false);
  const [previewFor, setPreviewFor] = useState(null);
  const [showBatch, setShowBatch] = useState(false);
  const { messages, isLoading, sendMessage, clearChat, loadMessages } = useChat();

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
    (question, searchMode = 'hybrid', nResults = 5) =>
      sendMessage(question, { searchMode, collection: activeCollection, nResults }),
    [sendMessage, activeCollection],
  );

  const visibleDocuments = activeCollection
    ? documents.filter(d => d.collection === activeCollection)
    : documents;

  async function handleUpload(file, collection, options) {
    await uploadDocument(file, collection, options);
    await refresh();
  }

  async function handleDelete(filename) {
    await deleteDocument(filename);
    await refresh();
  }

  async function handleMove(filename, collection) {
    await moveDocument(filename, collection);
    await refresh();
  }

  async function handleUpdateTags(filename, tags) {
    await updateTags(filename, tags);
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
      onOpenAnalytics={() => setShowAnalytics(true)}
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
          onSummarize={setSummaryFor}
          onPreview={setPreviewFor}
          onMove={handleMove}
          onUpdateTags={handleUpdateTags}
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
        onSave={handleSaveConversation}
        onOpenSaved={() => setShowConversations(true)}
        onOpenBatch={() => setShowBatch(true)}
      />
      {showAnalytics && <AnalyticsPanel onClose={() => setShowAnalytics(false)} />}
      {summaryFor && (
        <SummaryModal
          filename={summaryFor}
          onClose={() => setSummaryFor(null)}
          onAskQuestion={handleSend}
        />
      )}
      {showConversations && (
        <ConversationsModal
          onClose={() => setShowConversations(false)}
          onRestore={loadMessages}
        />
      )}
      {previewFor && (
        <DocumentPreviewModal filename={previewFor} onClose={() => setPreviewFor(null)} />
      )}
      {showBatch && <BatchQuestionsModal onClose={() => setShowBatch(false)} />}
    </Layout>
  );
}
