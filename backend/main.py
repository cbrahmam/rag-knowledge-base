from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.documents import router as documents_router

app = FastAPI(title="DocuMind", description="AI-powered knowledge base with RAG")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "DocuMind"}
