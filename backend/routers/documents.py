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
    TagUpdateRequest,
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
    rename_collection,
)
from services.summarizer import summarize_document
from config import MAX_FILE_SIZE

router = APIRouter(prefix="/api/documents", tags=["documents"])

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
CHUNKS_STORE = Path(__file__).parent.parent / "chunks_store.json"

UPLOAD_DIR.mkdir(exist_ok=True)


def _safe_filename(filename: Optional[str]) -> str:
    """Reduce an uploaded filename to a safe basename.

    Strips any directory components so a crafted name like '../../etc/passwd'
    can't escape the uploads directory (path traversal).
    """
    name = Path(filename or "").name
    if not name or name in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return name


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


def _to_list_item(filename: str, meta: dict) -> DocumentListItem:
    """Build a DocumentListItem from a stored metadata entry."""
    return DocumentListItem(
        filename=filename,
        file_type=meta["file_type"],
        total_chunks=meta["total_chunks"],
        uploaded_at=meta["uploaded_at"],
        size_bytes=meta["size_bytes"],
        collection=meta.get("collection", DEFAULT_COLLECTION),
        tags=meta.get("tags", []),
    )


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Form(DEFAULT_COLLECTION),
    chunk_size: Optional[int] = Form(None),
    overlap: Optional[int] = Form(None),
):
    collection = collection.strip() or DEFAULT_COLLECTION
    filename = _safe_filename(file.filename)
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(SUPPORTED_TYPES)}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

    content_hash = hashlib.sha256(content).hexdigest()
    duplicate = _find_duplicate(_load_store(), content_hash, filename)
    if duplicate:
        raise HTTPException(
            status_code=409,
            detail=f"This document is identical to an already-uploaded file: {duplicate}",
        )

    file_path = UPLOAD_DIR / filename
    with open(file_path, "wb") as f:
        f.write(content)

    try:
        parsed = parse_document(str(file_path), filename)
        chunks = chunk_document(
            parsed.text_content,
            source_document=filename,
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
        store[filename] = {
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
            filename=filename,
            file_type=parsed.file_type,
            total_chunks=len(chunks),
            total_characters=parsed.total_characters,
            status="processed",
            message=f"Successfully processed {filename} into {len(chunks)} chunks",
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
    return [_to_list_item(filename, meta) for filename, meta in store.items()]


@router.get("/collections", response_model=List[CollectionInfo])
async def get_collections():
    return list_collections()


def _reassign_collection_in_store(store: dict, old: str, new: str) -> None:
    for meta in store.values():
        if meta.get("collection", DEFAULT_COLLECTION) == old:
            meta["collection"] = new


@router.put("/collections/{name}")
async def rename_collection_endpoint(name: str, new_name: str = Form(...)):
    new_name = new_name.strip() or DEFAULT_COLLECTION
    moved = rename_collection(name, new_name)
    store = _load_store()
    _reassign_collection_in_store(store, name, new_name)
    _save_store(store)
    return {"renamed_from": name, "renamed_to": new_name, "chunks_moved": moved}


@router.delete("/collections/{name}")
async def delete_collection_endpoint(name: str):
    """Delete a collection by reassigning its documents to the default collection."""
    if name == DEFAULT_COLLECTION:
        raise HTTPException(status_code=400, detail="Cannot delete the default collection")
    moved = rename_collection(name, DEFAULT_COLLECTION)
    store = _load_store()
    _reassign_collection_in_store(store, name, DEFAULT_COLLECTION)
    _save_store(store)
    return {"deleted": name, "reassigned_to": DEFAULT_COLLECTION, "chunks_moved": moved}


@router.put("/{filename}/tags", response_model=DocumentListItem)
async def update_tags(filename: str, request: TagUpdateRequest):
    store = _load_store()
    if filename not in store:
        raise HTTPException(status_code=404, detail="Document not found")

    # Normalize: trim, drop blanks, de-dupe (case-insensitive), preserve order.
    seen, tags = set(), []
    for t in request.tags:
        t = t.strip()
        if t and t.lower() not in seen:
            seen.add(t.lower())
            tags.append(t)

    store[filename]["tags"] = tags
    _save_store(store)
    return _to_list_item(filename, store[filename])


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


@router.post("/{filename}/reindex", response_model=DocumentUploadResponse)
async def reindex_document(
    filename: str,
    chunk_size: Optional[int] = Form(None),
    overlap: Optional[int] = Form(None),
):
    """Re-chunk and re-embed an already-uploaded document, optionally with new
    chunk settings. Preserves the document's collection and tags."""
    store = _load_store()
    if filename not in store:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document file is no longer available")

    meta = store[filename]
    collection = meta.get("collection", DEFAULT_COLLECTION)

    parsed = parse_document(str(file_path), filename)
    chunks = chunk_document(
        parsed.text_content,
        source_document=filename,
        file_type=parsed.file_type,
        source_pages=parsed.pages,
        chunk_size=chunk_size,
        overlap=overlap,
    )

    default_size, default_overlap = adaptive_params(parsed.file_type)
    used_size = chunk_size or default_size
    used_overlap = overlap if overlap is not None else default_overlap

    vs_delete(filename)  # drop the old chunks before re-adding
    embeddings = generate_embeddings([c.text for c in chunks])
    add_document(chunks, embeddings, collection_name=collection)

    meta["total_chunks"] = len(chunks)
    meta["total_characters"] = parsed.total_characters
    meta["chunk_size"] = used_size
    meta["overlap"] = used_overlap
    _save_store(store)

    return DocumentUploadResponse(
        filename=filename,
        file_type=parsed.file_type,
        total_chunks=len(chunks),
        total_characters=parsed.total_characters,
        status="reindexed",
        message=f"Re-indexed {filename} into {len(chunks)} chunks",
        collection=collection,
        chunk_size=used_size,
        overlap=used_overlap,
    )


@router.get("/stats")
async def document_stats():
    return get_stats()


@router.get("/export")
async def export_knowledge_base():
    """Export a JSON manifest of the knowledge base (document metadata + stats).

    Excludes raw chunk text / embeddings — it's a portable inventory of what's
    indexed, useful for backup or auditing.
    """
    store = _load_store()
    documents = [
        {
            "filename": name,
            "file_type": meta.get("file_type"),
            "collection": meta.get("collection", DEFAULT_COLLECTION),
            "total_chunks": meta.get("total_chunks"),
            "total_characters": meta.get("total_characters"),
            "size_bytes": meta.get("size_bytes"),
            "uploaded_at": meta.get("uploaded_at"),
            "chunk_size": meta.get("chunk_size"),
            "overlap": meta.get("overlap"),
            "content_hash": meta.get("content_hash"),
        }
        for name, meta in store.items()
    ]
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "stats": get_stats(),
        "collections": list_collections(),
        "documents": documents,
    }


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
