# DocuMind

**Your company's knowledge, instantly searchable.**

## The Problem

Company knowledge is scattered across PDFs, docs, wikis, and Slack. Finding the right answer means digging through dozens of files, searching multiple platforms, and hoping you find the latest version.

## The Solution

DocuMind creates a searchable AI knowledge base from your documents. Upload files, ask questions in plain English, get answers with exact source citations.

## Features

- **Multi-format document upload** — PDF, DOCX, TXT, and Markdown files
- **Adaptive chunking** — Content-type-aware splitting (Markdown chunks per section); size/overlap auto-tuned per file type and overridable per upload
- **Vector embeddings** — Local embeddings with sentence-transformers (no API costs)
- **Natural language Q&A** — Ask questions and get accurate answers powered by Claude
- **Streaming answers** — Responses stream token-by-token over Server-Sent Events for instant feedback
- **Hybrid search** — Blend semantic (vector) and keyword (BM25) retrieval, switchable per query
- **Source citations** — Every answer includes the exact documents and pages it came from
- **Document summaries** — One-click AI summary, key points, and suggested questions per document
- **Document preview** — Click a document to read its full parsed text in a modal
- **Confidence scoring** — Know how reliable each answer is (high/medium/low)
- **Answer feedback** — Rate answers 👍/👎; ratings feed a satisfaction-rate metric
- **Conversation context** — Follow-up questions understand the conversation history
- **Chat export** — Download conversations as Markdown or copy to clipboard
- **Collections** — Organize documents into named collections and scope questions to one
- **Query analytics** — Usage dashboard: query volume, average latency, confidence mix, recent history
- **Saved conversations** — Save chat sessions and restore them later
- **Dark mode** — Light/dark theme toggle, remembers your choice and respects OS preference
- **Sample documents** — Included sample docs for instant testing

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | React + Vite | Fast dev experience, modern tooling |
| Styling | Tailwind CSS v4 | Utility-first, rapid UI development |
| Backend | Python + FastAPI | Async-first, auto-generated API docs |
| AI | Claude API (Anthropic) | Best-in-class reasoning for RAG |
| Embeddings | sentence-transformers | Free local embeddings, no API costs |
| Vector DB | ChromaDB | Embedded vector store, zero config |
| PDF Parsing | PyMuPDF | Fast, accurate PDF text extraction |

## Architecture

```
Document Upload → Parse (PDF/DOCX/TXT/MD)
                    → Chunk (500 chars, 50 overlap)
                      → Embed (all-MiniLM-L6-v2, 384-dim)
                        → Store (ChromaDB)

User Question → Embed Query
                  → Vector Search (top 5 chunks)
                    → Build Prompt (context + question)
                      → Claude API
                        → Answer + Source Citations
```

## How RAG Works

RAG (Retrieval-Augmented Generation) solves the problem of LLMs not knowing about your private data:

1. **Indexing**: Documents are split into chunks and converted to numerical vectors (embeddings) that capture semantic meaning
2. **Retrieval**: When you ask a question, it's also converted to a vector and compared against all stored chunks using cosine similarity
3. **Generation**: The most relevant chunks are sent as context to Claude, which generates an answer grounded in your actual documents

This approach ensures answers are factual (grounded in your docs) and traceable (with source citations).

## Analytics

Every answered query is logged locally (`backend/analytics_store.json`, gitignored). The
analytics dashboard (header → **Analytics**) surfaces total query volume, average response
time, average sources per answer, the confidence distribution, and recent questions.

- `GET /api/analytics` — summary (volume, latency, confidence distribution, recent)
- `GET /api/analytics/history?limit=N` — recent query records
- `DELETE /api/analytics/history` — clear the log

## Document summaries

Click **Summary** on any document (hover the card) to get an AI-generated overview, key points,
and suggested questions. Clicking a suggested question drops it straight into the chat. Summaries
are cached after the first generation.

- `POST /api/documents/{filename}/summarize` — returns `{ summary, key_points, suggested_questions, cached }`
- `POST /api/documents/{filename}/summarize?refresh=true` — regenerate, bypassing the cache

## Answer feedback

Each answer has 👍 / 👎 buttons. Ratings are stored locally (`backend/feedback_store.json`,
gitignored) along with the question, answer and confidence.

- `POST /api/feedback` — record a rating `{ question, answer, rating, confidence }`
- `GET /api/feedback` — `{ total, up, down, satisfaction_rate }`
- `DELETE /api/feedback` — clear feedback

## Saved conversations

Use **Save** in the chat header to store the current session, and **Saved** to browse, restore,
or delete past sessions. Conversations are stored locally (`backend/conversations_store.json`,
gitignored).

- `POST /api/conversations` — save `{ messages, title? }` (title auto-derived from the first question)
- `GET /api/conversations` — list (id, title, message count, updated_at)
- `GET /api/conversations/{id}` — full conversation
- `PUT /api/conversations/{id}` — update; `DELETE /api/conversations/{id}` — remove

## Document preview

Click a document's name in the sidebar to read its full parsed text (with file type, character
count and page count) in a modal.

- `GET /api/documents/{filename}/content` — `{ filename, file_type, total_characters, total_pages, content }`

## Adaptive chunking

Chunk size and overlap are tuned per file type (Markdown 800/100, PDF & DOCX 600/80, TXT 500/50),
and Markdown is split at heading boundaries so chunks respect sections. Override per upload via
the **Advanced** section in the uploader, or the `chunk_size` / `overlap` form fields on
`POST /api/documents/upload`.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Anthropic API key ([get one here](https://console.anthropic.com/))

### Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv ../venv
source ../venv/bin/activate  # or ..\venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp ../.env.example ../.env
# Edit .env and add your ANTHROPIC_API_KEY

# Start the server
uvicorn main:app --reload --port 8000
```

> Note: On first run, sentence-transformers will download the embedding model (~90MB). This is a one-time download.

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

The app will be available at `http://localhost:5173`.

### Quick Test

Click "Load Samples" in the sidebar to load the included sample documents, then start asking questions.

## Limitations & Future Work

- **No OCR**: Scanned PDFs (image-only) won't extract text — only text-based PDFs are supported
- **Local only**: ChromaDB and embeddings run locally — would need a hosted vector DB for production scale
- **No authentication**: No user auth — intended for local/internal use

Future improvements could include: document versioning and role-based access control.

### API: streaming endpoint

`POST /api/query/stream` returns a `text/event-stream`. Each frame is a JSON event:

```
data: {"type": "token", "text": "..."}      # one per streamed delta
data: {"type": "done", "sources": [...], "confidence": "high", ...}
```

### Search modes

`POST /api/query` accepts a `search_mode` (`hybrid` | `semantic` | `keyword`) and an `alpha`
(0.0–1.0) that weights the hybrid blend (1.0 = pure semantic, 0.0 = pure keyword):

```json
{ "question": "...", "search_mode": "hybrid", "alpha": 0.5 }
```

- **semantic** — cosine similarity over sentence-transformer embeddings (meaning-based)
- **keyword** — BM25 lexical ranking (exact terms, names, codes, acronyms)
- **hybrid** — normalized blend of both, weighted by `alpha`

`n_results` (1–20, default 5) controls how many chunks are retrieved per query, selectable from the chat header.

### Collections

Documents can be grouped into named collections. Upload accepts a `collection` form field
(default `General`); `POST /api/query` accepts an optional `collection` to scope retrieval;
`GET /api/documents/collections` lists collections with document and chunk counts.
Move a document between collections with `PATCH /api/documents/{filename}/collection` (form field
`collection`), or the hover **Move…** control on a document card.
