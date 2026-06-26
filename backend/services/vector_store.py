from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

import chromadb

from models.schemas import Chunk, SearchResult, DEFAULT_COLLECTION

logger = logging.getLogger(__name__)

CHROMA_DIR = Path(__file__).parent.parent / "chroma_data"
COLLECTION_NAME = "knowledge_base"

_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None


def _get_collection() -> chromadb.Collection:
    global _client, _collection
    if _collection is None:
        CHROMA_DIR.mkdir(exist_ok=True)
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB collection '%s' initialized with %d items", COLLECTION_NAME, _collection.count())
    return _collection


def add_document(
    chunks: List[Chunk],
    embeddings: List[List[float]],
    collection_name: str = DEFAULT_COLLECTION,
) -> None:
    collection = _get_collection()
    ids = [f"{chunks[0].source_document}_{c.chunk_index}" for c in chunks]
    documents = [c.text for c in chunks]
    metadatas = [
        {
            "source_document": c.source_document,
            "chunk_index": c.chunk_index,
            "source_page": c.source_page if c.source_page is not None else -1,
            "start_char": c.start_char,
            "end_char": c.end_char,
            "collection": collection_name,
        }
        for c in chunks
    ]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    logger.info("Added %d chunks for '%s' to vector store", len(chunks), chunks[0].source_document)


def search(
    query_embedding: List[float],
    n_results: int = 5,
    collection_name: Optional[str] = None,
) -> List[SearchResult]:
    collection = _get_collection()

    if collection.count() == 0:
        return []

    where = {"collection": collection_name} if collection_name else None
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"],
        where=where,
    )

    search_results = []
    for i in range(len(results["ids"][0])):
        meta = results["metadatas"][0][i]
        distance = results["distances"][0][i]
        similarity = 1 - distance

        search_results.append(SearchResult(
            text=results["documents"][0][i],
            source_document=meta["source_document"],
            source_page=meta["source_page"] if meta["source_page"] != -1 else None,
            chunk_index=meta["chunk_index"],
            similarity_score=round(similarity, 4),
        ))

    return search_results


def delete_document(filename: str) -> int:
    collection = _get_collection()
    existing = collection.get(where={"source_document": filename})
    if existing["ids"]:
        collection.delete(ids=existing["ids"])
        logger.info("Deleted %d chunks for '%s' from vector store", len(existing["ids"]), filename)
        return len(existing["ids"])
    return 0


def list_collections() -> List[dict]:
    """Group indexed chunks by collection, with document and chunk counts.

    Chunks indexed before collections existed have no 'collection' metadata;
    they're reported under the default collection name.
    """
    collection = _get_collection()
    if collection.count() == 0:
        return []

    results = collection.get(include=["metadatas"])
    by_collection: dict[str, dict] = {}
    for meta in results["metadatas"]:
        name = meta.get("collection", DEFAULT_COLLECTION)
        entry = by_collection.setdefault(name, {"documents": set(), "chunk_count": 0})
        entry["documents"].add(meta["source_document"])
        entry["chunk_count"] += 1

    return [
        {
            "name": name,
            "document_count": len(entry["documents"]),
            "chunk_count": entry["chunk_count"],
        }
        for name, entry in sorted(by_collection.items())
    ]


def get_stats() -> dict:
    collection = _get_collection()
    total_chunks = collection.count()

    all_docs = set()
    if total_chunks > 0:
        results = collection.get(include=["metadatas"])
        for meta in results["metadatas"]:
            all_docs.add(meta["source_document"])

    return {
        "total_documents": len(all_docs),
        "total_chunks": total_chunks,
        "collection_name": COLLECTION_NAME,
    }
