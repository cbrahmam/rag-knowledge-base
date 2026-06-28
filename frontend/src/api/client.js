const BASE_URL = '/api';

async function request(url, options = {}) {
  const response = await fetch(`${BASE_URL}${url}`, options);
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function uploadDocument(file, collection = 'General', { chunkSize, overlap } = {}) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('collection', collection);
  if (chunkSize != null) formData.append('chunk_size', chunkSize);
  if (overlap != null) formData.append('overlap', overlap);
  return request('/documents/upload', { method: 'POST', body: formData });
}

export async function listDocuments() {
  return request('/documents');
}

export async function listCollections() {
  return request('/documents/collections');
}

export async function moveDocument(filename, collection) {
  const formData = new FormData();
  formData.append('collection', collection);
  return request(`/documents/${encodeURIComponent(filename)}/collection`, { method: 'PATCH', body: formData });
}

export async function deleteDocument(filename) {
  return request(`/documents/${encodeURIComponent(filename)}`, { method: 'DELETE' });
}

export async function getStats() {
  return request('/documents/stats');
}

export async function askQuestion(question, context = null, searchMode = 'hybrid', collection = null, nResults = 5) {
  return request('/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, context, search_mode: searchMode, collection, n_results: nResults }),
  });
}

export async function loadSampleDocs() {
  return request('/documents/load-samples', { method: 'POST' });
}

export async function askMultiple(questions) {
  return request('/query/multi', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ questions }),
  });
}

export async function getAnalytics() {
  return request('/analytics');
}

export async function getQueryHistory(limit = 50) {
  return request(`/analytics/history?limit=${limit}`);
}

export async function clearQueryHistory() {
  return request('/analytics/history', { method: 'DELETE' });
}

/**
 * Stream an answer via Server-Sent Events.
 *
 * EventSource only supports GET, but we need to POST the question + context,
 * so we read the fetch ReadableStream and parse SSE frames manually.
 *
 * @param {string} question
 * @param {Array|null} context
 * @param {{searchMode?: string, collection?: string|null, onToken: (text: string) => void, onDone: (meta: object) => void, onError: (err: Error) => void}} handlers
 */
export async function askQuestionStream(question, context, { searchMode = 'hybrid', collection = null, nResults = 5, onToken, onDone, onError }) {
  try {
    const response = await fetch(`${BASE_URL}/query/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, context, search_mode: searchMode, collection, n_results: nResults }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split('\n\n');
      buffer = frames.pop() || '';

      for (const frame of frames) {
        const line = frame.split('\n').find(l => l.startsWith('data: '));
        if (!line) continue;
        const event = JSON.parse(line.slice(6));

        if (event.type === 'token') onToken(event.text);
        else if (event.type === 'done') onDone(event);
        else if (event.type === 'error') throw new Error(event.detail || 'Streaming error');
      }
    }
  } catch (err) {
    onError(err);
  }
}

export async function summarizeDocument(filename, refresh = false) {
  return request(`/documents/${encodeURIComponent(filename)}/summarize?refresh=${refresh}`, {
    method: 'POST',
  });
}

export async function submitFeedback({ question, answer, rating, confidence }) {
  return request('/feedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, answer, rating, confidence }),
  });
}

export async function getFeedbackSummary() {
  return request('/feedback');
}

export async function saveConversation(messages, title = null) {
  return request('/conversations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages, title }),
  });
}

export async function listConversations() {
  return request('/conversations');
}

export async function getConversation(id) {
  return request(`/conversations/${encodeURIComponent(id)}`);
}

export async function deleteConversation(id) {
  return request(`/conversations/${encodeURIComponent(id)}`, { method: 'DELETE' });
}

export async function getDocumentContent(filename) {
  return request(`/documents/${encodeURIComponent(filename)}/content`);
}
