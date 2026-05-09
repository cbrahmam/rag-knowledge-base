import { useState, useEffect, useCallback } from 'react';
import Layout from '../components/Layout';
import Sidebar from '../components/Sidebar';
import { uploadDocument, listDocuments, deleteDocument, getStats } from '../api/client';

export default function MainPage() {
  const [documents, setDocuments] = useState([]);
  const [stats, setStats] = useState({ total_documents: 0, total_chunks: 0 });

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

  return (
    <Layout
      stats={stats}
      sidebar={
        <Sidebar
          documents={documents}
          stats={stats}
          onUpload={handleUpload}
          onDelete={handleDelete}
        />
      }
    >
      <div className="flex-1 flex items-center justify-center text-text-secondary">
        <div className="text-center">
          <svg className="w-12 h-12 mx-auto mb-4 text-border" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          <p className="text-sm">Chat interface coming in Block 5</p>
          <p className="text-xs mt-1 text-text-secondary/60">Upload documents using the sidebar to get started</p>
        </div>
      </div>
    </Layout>
  );
}
