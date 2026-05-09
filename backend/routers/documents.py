from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, UploadFile, File

from models.schemas import DocumentUploadResponse, DocumentListItem
from services.doc_parser import parse_document, SUPPORTED_TYPES
from services.chunker import chunk_text
from services.embeddings import generate_embeddings
from services.vector_store import add_document, delete_document as vs_delete, get_stats

router = APIRouter(prefix="/api/documents", tags=["documents"])

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
CHUNKS_STORE = Path(__file__).parent.parent / "chunks_store.json"
MAX_FILE_SIZE = 10 * 1024 * 1024

UPLOAD_DIR.mkdir(exist_ok=True)


def _load_store() -> dict:
    if CHUNKS_STORE.exists():
        with open(CHUNKS_STORE, "r") as f:
            return json.load(f)
    return {}


def _save_store(store: dict) -> None:
    with open(CHUNKS_STORE, "w") as f:
        json.dump(store, f, indent=2)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(SUPPORTED_TYPES)}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as f:
        f.write(content)

    try:
        parsed = parse_document(str(file_path), file.filename)
        chunks = chunk_text(
            parsed.text_content,
            source_document=file.filename,
            source_pages=parsed.pages,
        )

        chunk_texts = [c.text for c in chunks]
        embeddings = generate_embeddings(chunk_texts)
        add_document(chunks, embeddings)

        store = _load_store()
        store[file.filename] = {
            "file_type": parsed.file_type,
            "total_chunks": len(chunks),
            "total_characters": parsed.total_characters,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "size_bytes": len(content),
        }
        _save_store(store)

        return DocumentUploadResponse(
            filename=file.filename,
            file_type=parsed.file_type,
            total_chunks=len(chunks),
            total_characters=parsed.total_characters,
            status="processed",
            message=f"Successfully processed {file.filename} into {len(chunks)} chunks",
        )

    except ValueError as e:
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


@router.get("", response_model=List[DocumentListItem])
async def list_documents():
    store = _load_store()
    documents = []
    for filename, meta in store.items():
        documents.append(DocumentListItem(
            filename=filename,
            file_type=meta["file_type"],
            total_chunks=meta["total_chunks"],
            uploaded_at=meta["uploaded_at"],
            size_bytes=meta["size_bytes"],
        ))
    return documents


@router.delete("/{filename}")
async def delete_document(filename: str):
    store = _load_store()

    if filename not in store:
        raise HTTPException(status_code=404, detail="Document not found")

    vs_delete(filename)

    del store[filename]
    _save_store(store)

    file_path = UPLOAD_DIR / filename
    if file_path.exists():
        os.remove(file_path)

    return {"message": f"Deleted {filename}", "status": "deleted"}


@router.get("/stats")
async def document_stats():
    return get_stats()
