const BASE_URL = '/api';

async function request(url, options = {}) {
  const response = await fetch(`${BASE_URL}${url}`, options);
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);
  return request('/documents/upload', { method: 'POST', body: formData });
}

export async function listDocuments() {
  return request('/documents');
}

export async function deleteDocument(filename) {
  return request(`/documents/${encodeURIComponent(filename)}`, { method: 'DELETE' });
}

export async function getStats() {
  return request('/documents/stats');
}

export async function askQuestion(question, context = null, searchMode = 'hybrid', alpha = 0.5) {
  return request('/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, context, search_mode: searchMode, alpha }),
  });
}

export async function loadSampleDocs() {
  return request('/documents/load-samples', { method: 'POST' });
}
