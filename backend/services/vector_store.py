from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Optional

import chromadb
from rank_bm25 import BM25Okapi

from models.schemas import Chunk, SearchResult, DEFAULT_COLLECTION

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall(text.lower())

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


def keyword_search(
    query_text: str,
    n_results: int = 5,
    collection_name: Optional[str] = None,
) -> List[SearchResult]:
    """Lexical BM25 search over all chunk texts.

    Complements semantic search by catching exact term matches (names, codes,
    acronyms) that embeddings can blur together. Scores are normalized to
    [0, 1] by the top hit so they're comparable with cosine similarity.
    Optionally scoped to a single collection.
    """
    collection = _get_collection()
    if collection.count() == 0:
        return []

    where = {"collection": collection_name} if collection_name else None
    data = collection.get(include=["documents", "metadatas"], where=where)
    docs = data["documents"]
    metas = data["metadatas"]
    if not docs:
        return []

    bm25 = BM25Okapi([_tokenize(d) for d in docs])
    scores = bm25.get_scores(_tokenize(query_text))
    max_score = max(scores) if len(scores) and max(scores) > 0 else 1.0

    ranked = sorted(range(len(docs)), key=lambda i: scores[i], reverse=True)
    results = []
    for i in ranked[:n_results]:
        if scores[i] <= 0:
            break
        meta = metas[i]
        results.append(SearchResult(
            text=docs[i],
            source_document=meta["source_document"],
            source_page=meta["source_page"] if meta["source_page"] != -1 else None,
            chunk_index=meta["chunk_index"],
            similarity_score=round(scores[i] / max_score, 4),
        ))
    return results


def hybrid_search(
    query_text: str,
    query_embedding: List[float],
    n_results: int = 5,
    alpha: float = 0.5,
    collection_name: Optional[str] = None,
) -> List[SearchResult]:
    """Blend semantic (cosine) and lexical (BM25) relevance.

    ``alpha`` weights the semantic side: 1.0 == pure vector search, 0.0 ==
    pure keyword search, 0.5 == balanced. Each signal is normalized to
    [0, 1] before mixing so neither dominates by scale. Optionally scoped to
    a single collection.
    """
    collection = _get_collection()
    count = collection.count()
    if count == 0:
        return []

    where = {"collection": collection_name} if collection_name else None
    data = collection.get(include=["documents", "metadatas"], where=where)
    ids = data["ids"]
    docs = data["documents"]
    metas = data["metadatas"]
    if not docs:
        return []

    bm25 = BM25Okapi([_tokenize(d) for d in docs])
    bm25_scores = bm25.get_scores(_tokenize(query_text))
    max_bm25 = max(bm25_scores) if len(bm25_scores) and max(bm25_scores) > 0 else 1.0

    sem = collection.query(
        query_embeddings=[query_embedding],
        n_results=count,
        include=["distances"],
        where=where,
    )
    sem_by_id = {sid: 1 - dist for sid, dist in zip(sem["ids"][0], sem["distances"][0])}

    scored = []
    for i, cid in enumerate(ids):
        sem_score = sem_by_id.get(cid, 0.0)
        kw_score = bm25_scores[i] / max_bm25
        combined = alpha * sem_score + (1 - alpha) * kw_score
        scored.append((i, combined))

    scored.sort(key=lambda x: x[1], reverse=True)

    results = []
    for i, combined in scored[:n_results]:
        meta = metas[i]
        results.append(SearchResult(
            text=docs[i],
            source_document=meta["source_document"],
            source_page=meta["source_page"] if meta["source_page"] != -1 else None,
            chunk_index=meta["chunk_index"],
            similarity_score=round(combined, 4),
        ))
    return results


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


def get_document_chunks(filename: str) -> List[str]:
    """Return a document's chunk texts in chunk order."""
    collection = _get_collection()
    existing = collection.get(
        where={"source_document": filename},
        include=["documents", "metadatas"],
    )
    if not existing["ids"]:
        return []

    paired = sorted(
        zip(existing["documents"], existing["metadatas"]),
        key=lambda p: p[1].get("chunk_index", 0),
    )
    return [doc for doc, _ in paired]


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
