# DocuMind

**Your company's knowledge, instantly searchable.**

## The Problem

Company knowledge is scattered across PDFs, docs, wikis, and Slack. Finding the right answer means digging through dozens of files, searching multiple platforms, and hoping you find the latest version.

## The Solution

DocuMind creates a searchable AI knowledge base from your documents. Upload files, ask questions in plain English, get answers with exact source citations.

## Features

- **Multi-format document upload** — PDF, DOCX, TXT, and Markdown files
- **Automatic text chunking** — Smart splitting at sentence boundaries with configurable overlap
- **Vector embeddings** — Local embeddings with sentence-transformers (no API costs)
- **Natural language Q&A** — Ask questions and get accurate answers powered by Claude
- **Streaming answers** — Responses stream token-by-token over Server-Sent Events for instant feedback
- **Hybrid search** — Blend semantic (vector) and keyword (BM25) retrieval, switchable per query
- **Source citations** — Every answer includes the exact documents and pages it came from
- **Confidence scoring** — Know how reliable each answer is (high/medium/low)
- **Conversation context** — Follow-up questions understand the conversation history
- **Chat export** — Download conversations as Markdown or copy to clipboard
- **Collections** — Organize documents into named collections and scope questions to one
- **Query analytics** — Usage dashboard: query volume, average latency, confidence mix, recent history
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
- **Chunk size**: Fixed at 500 characters — could benefit from adaptive chunking based on content type
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

### Collections

Documents can be grouped into named collections. Upload accepts a `collection` form field
(default `General`); `POST /api/query` accepts an optional `collection` to scope retrieval;
`GET /api/documents/collections` lists collections with document and chunk counts.
