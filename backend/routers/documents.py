from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from models.schemas import (
    DocumentUploadResponse,
    DocumentListItem,
    CollectionInfo,
    DocumentSummary,
    DocumentContent,
    DEFAULT_COLLECTION,
)
from services.doc_parser import parse_document, SUPPORTED_TYPES
from services.chunker import chunk_document, adaptive_params
from services.embeddings import generate_embeddings
from services.vector_store import (
    add_document,
    delete_document as vs_delete,
    get_stats,
    list_collections,
    get_document_chunks,
    set_document_collection,
)
from services.summarizer import summarize_document

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


def _find_duplicate(store: dict, content_hash: str, filename: str) -> Optional[str]:
    """Return the name of an existing document with identical content, if any."""
    for name, meta in store.items():
        if name != filename and meta.get("content_hash") == content_hash:
            return name
    return None


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Form(DEFAULT_COLLECTION),
    chunk_size: Optional[int] = Form(None),
    overlap: Optional[int] = Form(None),
):
    collection = collection.strip() or DEFAULT_COLLECTION
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(SUPPORTED_TYPES)}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

    content_hash = hashlib.sha256(content).hexdigest()
    duplicate = _find_duplicate(_load_store(), content_hash, file.filename)
    if duplicate:
        raise HTTPException(
            status_code=409,
            detail=f"This document is identical to an already-uploaded file: {duplicate}",
        )

    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as f:
        f.write(content)

    try:
        parsed = parse_document(str(file_path), file.filename)
        chunks = chunk_document(
            parsed.text_content,
            source_document=file.filename,
            file_type=parsed.file_type,
            source_pages=parsed.pages,
            chunk_size=chunk_size,
            overlap=overlap,
        )

        default_size, default_overlap = adaptive_params(parsed.file_type)
        used_size = chunk_size or default_size
        used_overlap = overlap if overlap is not None else default_overlap

        chunk_texts = [c.text for c in chunks]
        embeddings = generate_embeddings(chunk_texts)
        add_document(chunks, embeddings, collection_name=collection)

        store = _load_store()
        store[file.filename] = {
            "file_type": parsed.file_type,
            "total_chunks": len(chunks),
            "total_characters": parsed.total_characters,
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "size_bytes": len(content),
            "collection": collection,
            "chunk_size": used_size,
            "overlap": used_overlap,
            "content_hash": content_hash,
        }
        _save_store(store)

        return DocumentUploadResponse(
            filename=file.filename,
            file_type=parsed.file_type,
            total_chunks=len(chunks),
            total_characters=parsed.total_characters,
            status="processed",
            message=f"Successfully processed {file.filename} into {len(chunks)} chunks",
            collection=collection,
            chunk_size=used_size,
            overlap=used_overlap,
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
            collection=meta.get("collection", DEFAULT_COLLECTION),
        ))
    return documents


@router.get("/collections", response_model=List[CollectionInfo])
async def get_collections():
    return list_collections()


@router.patch("/{filename}/collection")
async def move_document(filename: str, collection: str = Form(...)):
    collection = collection.strip() or DEFAULT_COLLECTION
    store = _load_store()
    if filename not in store:
        raise HTTPException(status_code=404, detail="Document not found")

    moved = set_document_collection(filename, collection)
    store[filename]["collection"] = collection
    _save_store(store)
    return {"filename": filename, "collection": collection, "chunks_moved": moved}


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


@router.post("/{filename}/summarize", response_model=DocumentSummary)
async def summarize(filename: str, refresh: bool = False):
    store = _load_store()
    if filename not in store:
        raise HTTPException(status_code=404, detail="Document not found")

    cached = store[filename].get("summary")
    if cached and not refresh:
        return DocumentSummary(**cached, cached=True)

    chunks = get_document_chunks(filename)
    if not chunks:
        raise HTTPException(status_code=400, detail="Document has no indexed content")

    try:
        summary = summarize_document(filename, chunks)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to summarize: {str(e)}")

    store[filename]["summary"] = summary.model_dump(exclude={"cached"})
    _save_store(store)
    return summary


@router.get("/{filename}/content", response_model=DocumentContent)
async def document_content(filename: str):
    store = _load_store()
    if filename not in store:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document file is no longer available")

    parsed = parse_document(str(file_path), filename)
    return DocumentContent(
        filename=filename,
        file_type=parsed.file_type,
        total_characters=parsed.total_characters,
        total_pages=parsed.total_pages,
        content=parsed.text_content,
    )


@router.post("/load-samples")
async def load_sample_documents():
    sample_dir = Path(__file__).parent.parent.parent / "sample-docs"
    if not sample_dir.exists():
        raise HTTPException(status_code=404, detail="Sample documents not found")

    results = []
    for file_path in sorted(sample_dir.glob("*")):
        if file_path.suffix.lower() not in SUPPORTED_TYPES:
            continue

        content = file_path.read_bytes()
        dest = UPLOAD_DIR / file_path.name
        dest.write_bytes(content)

        try:
            parsed = parse_document(str(dest), file_path.name)
            chunks = chunk_document(
                parsed.text_content,
                source_document=file_path.name,
                file_type=parsed.file_type,
                source_pages=parsed.pages,
            )
            chunk_texts = [c.text for c in chunks]
            embeddings = generate_embeddings(chunk_texts)
            add_document(chunks, embeddings, collection_name="Samples")

            store = _load_store()
            store[file_path.name] = {
                "file_type": parsed.file_type,
                "total_chunks": len(chunks),
                "total_characters": parsed.total_characters,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
                "size_bytes": len(content),
                "collection": "Samples",
                "content_hash": hashlib.sha256(content).hexdigest(),
            }
            _save_store(store)

            results.append({"filename": file_path.name, "status": "processed", "chunks": len(chunks)})
        except Exception as e:
            results.append({"filename": file_path.name, "status": "error", "error": str(e)})

    return {"loaded": len(results), "results": results}
