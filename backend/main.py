from dotenv import load_dotenv

# Load environment variables from a .env file before anything reads them
# (e.g. ANTHROPIC_API_KEY used by the RAG and summarization services).
load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from routers.documents import router as documents_router  # noqa: E402
from routers.query import router as query_router  # noqa: E402
from routers.analytics import router as analytics_router  # noqa: E402
from routers.feedback import router as feedback_router  # noqa: E402
from routers.conversations import router as conversations_router  # noqa: E402

app = FastAPI(title="DocuMind", description="AI-powered knowledge base with RAG")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(query_router)
app.include_router(analytics_router)
app.include_router(feedback_router)
app.include_router(conversations_router)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "DocuMind"}
