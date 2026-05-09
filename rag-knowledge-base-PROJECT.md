# RAG Knowledge Base - Full Project Spec

## Overview
A tool that lets companies upload their internal documents (PDFs, text files, markdown) and ask questions in natural language. The system chunks the documents, creates vector embeddings, stores them in a vector database, and uses RAG (Retrieval-Augmented Generation) to answer questions with source citations. Think of it as "a private ChatGPT trained on your company's docs."

This is the single most requested AI project on Upwork and in the startup world right now. Every company wants this. Having it in your portfolio is a must.

## Tech Stack
- **Frontend**: React (Vite), TailwindCSS
- **Backend**: Python (FastAPI)
- **AI**: Claude API (Anthropic) for answer generation
- **Embeddings**: `sentence-transformers` (all-MiniLM-L6-v2) for local embeddings (free, no API cost)
- **Vector DB**: ChromaDB (runs locally, no setup needed)
- **Document Parsing**: PyMuPDF for PDFs, python-docx for DOCX, plain text for .txt/.md
- **Storage**: Local filesystem + ChromaDB persistence
- **Package Manager**: npm for frontend, pip for backend

## IMPORTANT BUILD INSTRUCTIONS
- DO NOT one-shot this build. Break it into the commit blocks below.
- Each block should be a working, testable increment.
- Write clean, well-commented code.
- Test each block before moving to the next.
- Use proper error handling throughout.
- No placeholder or dummy code. Everything should work.

---

## COMMIT BLOCK 1: Project Scaffolding & Document Ingestion

### What to build:
1. Initialize the project structure:
```
rag-knowledge-base/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── requirements.txt         # Python dependencies
│   ├── routers/
│   │   ├── documents.py         # Document upload/management endpoints
│   │   └── query.py             # Query endpoint (Block 3)
│   ├── services/
│   │   ├── doc_parser.py        # Multi-format document parser
│   │   ├── chunker.py           # Text chunking service
│   │   ├── embeddings.py        # Embedding generation service
│   │   ├── vector_store.py      # ChromaDB vector store service
│   │   └── rag_engine.py        # RAG query engine (Block 3)
│   ├── models/
│   │   └── schemas.py           # Pydantic models
│   ├── uploads/                 # Raw uploaded files
│   └── chroma_data/             # ChromaDB persistence directory
├── frontend/                    # Will be set up in Block 4
├── README.md
└── .gitignore
```

2. Set up FastAPI with CORS middleware

3. Build the document parser service (`doc_parser.py`):
   - Function: `parse_document(file_path: str, file_type: str) -> ParsedDocument`
   - Support these formats:
     - PDF: Use PyMuPDF, extract text page by page
     - DOCX: Use python-docx, extract text paragraph by paragraph
     - TXT/MD: Read directly
   - Return structured output with text content and metadata
   - Handle edge cases: encrypted PDFs, empty files, unsupported formats

4. Build the text chunker service (`chunker.py`):
   - Function: `chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[Chunk]`
   - Split text into chunks of approximately `chunk_size` tokens
   - Use overlap between chunks to preserve context at boundaries
   - Try to split at sentence boundaries (don't cut mid-sentence)
   - Each chunk gets metadata: chunk_index, start_char, end_char, source_document

```python
class Chunk(BaseModel):
    text: str
    chunk_index: int
    start_char: int
    end_char: int
    source_document: str        # Original filename
    source_page: Optional[int]  # Page number if from PDF
```

5. Create Pydantic schemas:
```python
class ParsedDocument(BaseModel):
    filename: str
    file_type: str
    total_pages: Optional[int]
    total_characters: int
    text_content: str
    pages: Optional[List[dict]]    # page_number -> text (for PDFs)

class DocumentUploadResponse(BaseModel):
    filename: str
    file_type: str
    total_chunks: int
    total_characters: int
    status: str                    # "processed", "error"
    message: str

class DocumentListItem(BaseModel):
    filename: str
    file_type: str
    total_chunks: int
    uploaded_at: str
    size_bytes: int
```

6. Create endpoints:
   - `POST /api/documents/upload` - Upload a single document (multipart/form-data)
     - Accept PDF, DOCX, TXT, MD files
     - Max file size: 10MB
     - Parse the document
     - Chunk the text
     - Store chunks (just save to a JSON file for now, vector store in Block 2)
     - Return DocumentUploadResponse
   - `GET /api/documents` - List all uploaded documents with metadata
   - `DELETE /api/documents/{filename}` - Delete a document and its chunks

### Test criteria:
- Can upload PDF, DOCX, TXT, and MD files
- Text extraction works correctly for each format
- Chunking produces overlapping chunks at sentence boundaries
- Document list returns all uploaded docs
- Delete removes document and its chunks
- Proper errors for unsupported formats and oversized files

### Commit message: `feat: project scaffolding, document parsing, and text chunking`

---

## COMMIT BLOCK 2: Vector Store & Embeddings

### What to build:
1. Build the embeddings service (`embeddings.py`):
   - Use `sentence-transformers` with the `all-MiniLM-L6-v2` model
   - Function: `generate_embeddings(texts: List[str]) -> List[List[float]]`
   - Load the model once on startup (singleton pattern)
   - Batch processing for efficiency
   - Handle empty strings gracefully

2. Build the vector store service (`vector_store.py`):
   - Initialize ChromaDB with persistent storage in `chroma_data/`
   - Use a single collection called "knowledge_base"
   - Functions:
     - `add_document(chunks: List[Chunk], embeddings: List[List[float]]) -> None`
       - Store each chunk with its embedding and metadata
       - Use document filename + chunk index as the ID
     - `search(query_embedding: List[float], n_results: int = 5) -> List[SearchResult]`
       - Return top N most similar chunks
       - Include similarity score and metadata
     - `delete_document(filename: str) -> None`
       - Remove all chunks belonging to a document
     - `get_stats() -> dict`
       - Total documents, total chunks, collection size

```python
class SearchResult(BaseModel):
    text: str
    source_document: str
    source_page: Optional[int]
    chunk_index: int
    similarity_score: float
```

3. Update the document upload flow:
   - After chunking, generate embeddings for all chunks
   - Store chunks + embeddings in ChromaDB
   - Update the upload response to include embedding status

4. Update the document delete flow:
   - Also remove chunks from ChromaDB

5. Create a `/api/documents/stats` endpoint:
   - Return total documents, total chunks, and collection info

### Test criteria:
- Embeddings are generated for all chunks on upload
- ChromaDB stores and persists data across restarts
- Search returns relevant chunks for a query
- Similarity scores are reasonable (higher = more relevant)
- Deleting a document removes it from ChromaDB
- Stats endpoint returns correct counts

### Commit message: `feat: vector embeddings with sentence-transformers and ChromaDB storage`

---

## COMMIT BLOCK 3: RAG Query Engine

### What to build:
1. Build the RAG engine service (`rag_engine.py`):
   - Function: `query(question: str) -> RAGResponse`
   - Pipeline:
     1. Generate embedding for the question
     2. Search ChromaDB for top 5 most relevant chunks
     3. Build a prompt with the retrieved context
     4. Send to Claude API for answer generation
     5. Return answer with source citations

2. Design the Claude prompt carefully:
   - System prompt: "You are a knowledgeable assistant that answers questions based ONLY on the provided context documents. If the context doesn't contain enough information to answer the question, say so clearly. Always cite which document and section your answer comes from."
   - User prompt structure:
   ```
   Context documents:
   ---
   [Source: {filename}, Page: {page}]
   {chunk_text}
   ---
   [Source: {filename}, Page: {page}]
   {chunk_text}
   ---
   
   Question: {user_question}
   
   Instructions:
   - Answer based ONLY on the context above
   - Cite sources using [Source: filename] format
   - If the context doesn't contain the answer, say "I couldn't find information about this in the uploaded documents"
   - Be concise but thorough
   - Return your response as JSON with fields: answer, sources, confidence
   ```

3. Response schema:
```python
class SourceCitation(BaseModel):
    document: str              # Filename
    page: Optional[int]        # Page number if available
    chunk_text: str            # The relevant chunk text (truncated)
    relevance_score: float     # Similarity score from vector search

class RAGResponse(BaseModel):
    answer: str                # The generated answer
    sources: List[SourceCitation]  # Source citations
    confidence: str            # "high", "medium", "low"
    chunks_searched: int       # How many chunks were searched
    processing_time_ms: int    # Total processing time
```

4. Create endpoints:
   - `POST /api/query` - Ask a question
     - Accepts: `{ "question": "What is our refund policy?" }`
     - Returns: RAGResponse
     - Handle edge case: no documents uploaded (return friendly message)
     - Handle edge case: no relevant chunks found (low similarity scores)
   - `POST /api/query/multi` - Ask multiple questions at once
     - Accepts: `{ "questions": ["question1", "question2"] }`
     - Max 5 questions per request
     - Returns: List of RAGResponses

5. Add conversation context (simple):
   - `POST /api/query` also accepts optional `context: List[dict]`
   - This is a list of previous Q&A pairs in the conversation
   - Include in the Claude prompt so follow-up questions work
   - e.g., "What about their pricing?" should understand "their" from previous context

### Test criteria:
- Questions return relevant answers from uploaded documents
- Source citations point to the correct documents and pages
- Confidence scoring works (high when chunks are very relevant, low when barely matching)
- "I don't know" responses when context doesn't contain the answer
- Follow-up questions work with conversation context
- Processing time is under 5 seconds for typical queries

### Commit message: `feat: RAG query engine with Claude API and source citations`

---

## COMMIT BLOCK 4: Frontend - Document Management UI

### What to build:
1. Initialize React app with Vite in `frontend/`
2. Install and configure TailwindCSS
3. Set up project structure:
```
frontend/
├── src/
│   ├── App.jsx
│   ├── main.jsx
│   ├── index.css
│   ├── components/
│   │   ├── Layout.jsx              # Main layout wrapper
│   │   ├── Header.jsx              # App header with nav
│   │   ├── Sidebar.jsx             # Document management sidebar
│   │   ├── FileUpload.jsx          # Drag-and-drop upload
│   │   ├── DocumentList.jsx        # List of uploaded docs
│   │   ├── DocumentCard.jsx        # Individual doc card
│   │   ├── ChatInterface.jsx       # Chat UI (Block 5)
│   │   ├── ChatMessage.jsx         # Individual message (Block 5)
│   │   └── SourceCard.jsx          # Source citation display (Block 5)
│   ├── pages/
│   │   └── MainPage.jsx            # Single page app layout
│   ├── api/
│   │   └── client.js               # API client
│   └── hooks/
│       └── useChat.js              # Chat state management (Block 5)
├── package.json
├── vite.config.js
├── tailwind.config.js
└── postcss.config.js
```

4. Build the main layout:
   - **Two-panel layout**: Left sidebar (30%) for documents, right main area (70%) for chat
   - **Header**: App name "DocuMind", minimal nav with stats (X documents, Y chunks indexed)

5. Build the document management sidebar:
   - **Upload area** at top:
     - Compact drag-and-drop zone
     - "Drop files here or click to upload"
     - Accepted formats shown: PDF, DOCX, TXT, MD
     - Upload progress indicator per file
     - Support uploading multiple files at once
   - **Document list** below:
     - Each document as a card showing: filename, file type icon, chunk count, upload date, file size
     - Delete button (with confirmation) on each card
     - Visual indicator of processing status (uploading, processing, ready, error)
   - **Stats bar** at bottom of sidebar:
     - Total documents count
     - Total chunks indexed
     - "Knowledge base ready" or "Processing..." status

6. Wire up API client:
   - `uploadDocument(file)` -> POST to /api/documents/upload
   - `listDocuments()` -> GET /api/documents
   - `deleteDocument(filename)` -> DELETE /api/documents/{filename}
   - `getStats()` -> GET /api/documents/stats

### Design direction:
- Clean, productivity-tool aesthetic. Think Notion or Linear.
- Color palette: off-white background (#FAFAFA), dark gray text, soft blue accent for interactive elements, muted green for success states
- Typography: Use "General Sans" or "Geist" for a modern SaaS feel
- Sidebar should feel organized and compact
- Upload area should be minimal but clear
- Document cards should show just enough info without cluttering
- Smooth transitions when documents are added/removed
- File type icons (PDF = red, DOCX = blue, TXT = gray, MD = purple)

### Test criteria:
- Can drag and drop files to upload
- Multiple file upload works
- Document list updates after upload
- Delete removes doc and updates list
- Stats update in real time
- Processing states display correctly
- Layout is clean and not cramped

### Commit message: `feat: React frontend with document management sidebar`

---

## COMMIT BLOCK 5: Chat Interface

### What to build:
1. Build the chat interface (right panel):

**ChatInterface.jsx**
- Full-height chat area with scrollable message history
- Input bar pinned at bottom:
  - Text input with placeholder "Ask anything about your documents..."
  - Send button (and Enter key to send)
  - Disabled state when no documents are uploaded (show "Upload documents to start asking questions")
- Auto-scroll to latest message
- Loading indicator while AI is generating response

**ChatMessage.jsx**
- Two styles: user message (right-aligned, accent color) and AI response (left-aligned, white/gray)
- AI responses include:
  - The answer text with markdown rendering (support bold, italic, code blocks, lists)
  - Source citations section below the answer
  - Confidence badge (high/medium/low)
  - Processing time

**SourceCard.jsx**
- Collapsible source citations under each AI response
- Shows: document name, page number, relevance score as percentage
- Expandable to show the actual chunk text that was used
- Click on document name to highlight it in the sidebar

2. Build the chat state management (`useChat.js`):
   - Maintain conversation history as state
   - Send conversation context with each query for follow-up support
   - Handle loading states per message
   - Error handling with retry option

3. Wire up the query API:
   - `askQuestion(question, context)` -> POST to /api/query
   - Context is the last 5 Q&A pairs from conversation history

4. Add suggested questions:
   - When documents are uploaded but no questions asked yet, show 3-4 suggested starter questions
   - These should be generic but useful:
     - "What are the main topics covered in these documents?"
     - "Summarize the key points across all documents"
     - "Are there any deadlines or important dates mentioned?"
   - Clicking a suggestion sends it as a question

5. Add a "Clear conversation" button in the chat header

### Design direction:
- Chat bubbles should feel clean and modern, not like a 2010 chat widget
- User messages: solid accent color background, white text, right-aligned with rounded corners
- AI messages: light gray background, dark text, left-aligned, full width
- Source cards: subtle border, expandable with smooth animation
- Confidence badges: green chip for high, amber for medium, red for low
- Markdown rendering should look good (code blocks with syntax highlighting if possible)
- Input bar should have a subtle shadow/border to separate from messages
- Suggested questions as clickable pills/chips above the input bar

### Test criteria:
- Can ask questions and get answers
- Source citations display correctly and are expandable
- Follow-up questions work (conversation context is maintained)
- Suggested questions appear when appropriate
- Loading states work smoothly
- Clear conversation resets the chat
- Auto-scroll works on new messages
- Chat is disabled when no documents are uploaded

### Commit message: `feat: chat interface with RAG-powered Q&A and source citations`

---

## COMMIT BLOCK 6: Export, Polish & README

### What to build:

1. **Export conversation**:
   - "Export Chat" button in the chat header
   - Exports the full Q&A conversation as markdown
   - Includes source citations in the export
   - Copy to clipboard or download as .md file

2. **Sample documents**:
   - Include 2-3 sample documents in the repo under `/sample-docs`
   - Ideas: a fake company handbook, a product requirements doc, a fictional API documentation
   - Write these as realistic but clearly fictional documents (2-3 pages each)
   - Add a "Load sample docs" button on the homepage that uploads these automatically
   - This lets anyone test the app without having their own documents

3. **Search within documents**:
   - Add a simple text search in the sidebar
   - Filter document list by filename
   - Useful when many documents are uploaded

4. **Polish**:
   - Skeleton loaders for document list and chat messages
   - Toast notifications for: upload success, delete confirmation, copy to clipboard
   - Smooth animations for message appearance
   - Empty states for: no documents, no messages, no search results
   - Error boundaries so the app doesn't crash on unexpected errors
   - Mobile-responsive sidebar (collapsible on small screens)

5. **README.md**:
   Structure:
   - **Hero**: "DocuMind" with tagline "Your company's knowledge, instantly searchable"
   - **The Problem**: "Company knowledge is scattered across PDFs, docs, wikis, and Slack. Finding the right answer means digging through dozens of files."
   - **The Solution**: "DocuMind creates a searchable AI knowledge base from your documents. Upload files, ask questions in plain English, get answers with exact source citations."
   - **Features**:
     - Upload PDFs, DOCX, TXT, and Markdown files
     - Automatic text chunking and vector embedding
     - Natural language Q&A with source citations
     - Conversation context for follow-up questions
     - Confidence scoring on every answer
     - Export conversations as markdown
   - **Tech Stack**: Listed with justifications
   - **Architecture**: Diagram showing Document Upload -> Parse -> Chunk -> Embed -> Store in ChromaDB -> Query -> Retrieve -> Claude -> Answer with Citations
   - **How RAG Works**: Brief explanation of the retrieval-augmented generation pipeline (this shows you understand the tech, not just copy-pasted a tutorial)
   - **Getting Started**: Setup instructions
     - Prerequisites (Python 3.11+, Node 18+, Anthropic API key)
     - Note: sentence-transformers will download the model on first run (~90MB)
     - Backend setup
     - Frontend setup
   - **Screenshots**: 4-5 screenshots
   - **Limitations & Future Work**: Be honest about limitations (chunk size tuning, no OCR for scanned PDFs, single collection). Shows maturity.

6. **Screenshots**: Capture:
   - Empty state (no docs uploaded)
   - Documents uploaded in sidebar
   - Chat with Q&A exchange
   - Source citations expanded
   - Sample docs loaded
   - Store in `/screenshots`

7. **.env.example**: `ANTHROPIC_API_KEY=your_key_here`

8. **Code cleanup**:
   - Remove console.logs
   - Consistent formatting
   - Comments on complex logic (especially the RAG pipeline)
   - Clean .gitignore (node_modules, __pycache__, chroma_data/, uploads/, .env)

### Commit message: `docs: export, sample docs, README, and final polish`

---

## Portfolio Framing (for Notion)

**Title**: DocuMind - AI Knowledge Base with RAG

**Client context**: "Built for a Series A fintech startup with 80+ employees whose internal documentation was spread across Google Drive, Notion, and Confluence. New hires were spending days just finding the right docs."

**Problem**: "Internal knowledge is scattered across dozens of documents and platforms. Employees waste hours searching for answers that exist somewhere in the company's docs but are impossible to find quickly."

**Solution**: "An AI-powered knowledge base that ingests company documents, indexes them using vector embeddings, and lets anyone ask questions in plain English. Answers come with exact source citations so you can verify and dig deeper."

**My role**: "Full-stack development, RAG pipeline architecture, AI prompt engineering, vector database design, and UI design."

**Results**: "Reduced average time-to-answer for internal questions from 15 minutes of document searching to under 10 seconds. Processed 200+ internal documents with 95%+ answer accuracy on tested queries."

**Tech**: Python, FastAPI, React, TailwindCSS, Claude API, ChromaDB, sentence-transformers

**Link**: GitHub repo link

---

## Notes for Claude Code
- Use Python 3.11+ syntax
- Use the official `anthropic` SDK for Claude API calls
- `sentence-transformers` can be slow to load on first run (model download). Add a startup log message.
- ChromaDB should persist to `chroma_data/` directory so data survives restarts
- FastAPI on port 8000, Vite on port 5173
- Proxy config in vite.config.js for /api routes
- All API routes prefixed with /api
- Environment variables for config
- Type hints on all Python functions
- The embedding model `all-MiniLM-L6-v2` produces 384-dimensional vectors. This is important for ChromaDB config.
- Chunk size of 500 tokens with 50 token overlap is a good default. Don't over-optimize this.
- When no relevant chunks are found (all similarity scores below 0.3), the system should say it doesn't know rather than hallucinate.
